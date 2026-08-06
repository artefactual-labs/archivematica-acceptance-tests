"""Archivematica API Ability.

This module contains the ``ArchivematicaAPIAbility`` class, which represents a
user's ability to use Archivematica's APIs to interact with Archivematica.
"""

import logging
import os
import time
import xml.etree.ElementTree as ET

import requests

from . import base

logger = logging.getLogger("amuser.api")

CREATE_SIP_DECISION_ID = "bb194013-597c-4e4a-8493-b36d190f8717"


class ArchivematicaAPIAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaAPIAbility(base.Base):
    """Represents an Archivematica (AM) user's ability to use AM's APIs to
    interact with AM.
    """

    def _authenticated_dashboard_session(self):
        try:
            return self._dashboard_session
        except AttributeError:
            pass

        session = requests.Session()
        login_url = self.get_login_url()
        response = session.get(login_url, timeout=self.pessimistic_wait)
        response.raise_for_status()
        csrf_token = session.cookies.get("csrftoken")
        if not csrf_token:
            raise ArchivematicaAPIAbilityError(
                "Unable to obtain a CSRF token from Archivematica"
            )
        response = session.post(
            login_url,
            data={
                "csrfmiddlewaretoken": csrf_token,
                "username": self.am_username,
                "password": self.am_password,
            },
            headers={"Referer": login_url},
            allow_redirects=False,
            timeout=self.pessimistic_wait,
        )
        if response.status_code not in (301, 302) or not session.cookies.get(
            "sessionid"
        ):
            raise ArchivematicaAPIAbilityError("Unable to log in to Archivematica")
        self._dashboard_session = session
        return session

    def install_transfer_only_processing_config(self, name):
        """Clone the automated config without its Create SIP(s) choice."""
        session = self._authenticated_dashboard_session()
        source_url = f"{self.am_url}api/processing-configuration/automated"
        response = session.get(
            source_url,
            headers={"Accept": "application/xml"},
            timeout=self.pessimistic_wait,
        )
        response.raise_for_status()
        source_root = ET.fromstring(response.content)
        choices = {
            choice.findtext("appliesTo"): choice.findtext("goToChain")
            for choice in source_root.findall(".//preconfiguredChoice")
            if choice.findtext("appliesTo") != CREATE_SIP_DECISION_ID
        }

        add_url = f"{self.am_url}administration/processing/add/"
        csrf_token = session.cookies.get("csrftoken")
        response = session.post(
            add_url,
            data={
                "csrfmiddlewaretoken": csrf_token,
                "name": name,
                **choices,
            },
            headers={"Referer": add_url},
            allow_redirects=False,
            timeout=self.pessimistic_wait,
        )
        if response.status_code not in (301, 302):
            raise ArchivematicaAPIAbilityError(
                f'Unable to install processing configuration "{name}"'
            )

        target_url = f"{self.am_url}api/processing-configuration/{name}"
        response = session.get(
            target_url,
            headers={"Accept": "application/xml"},
            timeout=self.pessimistic_wait,
        )
        response.raise_for_status()
        target_root = ET.fromstring(response.content)
        installed_choices = {
            choice.findtext("appliesTo"): choice.findtext("goToChain")
            for choice in target_root.findall(".//preconfiguredChoice")
        }
        if installed_choices != choices:
            raise ArchivematicaAPIAbilityError(
                f'Processing configuration "{name}" was not installed correctly'
            )

    def reject_transfer(self, transfer_uuid):
        """Reject a transfer paused at a Dashboard decision point."""
        session = self._authenticated_dashboard_session()
        list_url = f"{self.am_url}mcp/list/"
        response = session.get(list_url, timeout=self.pessimistic_wait)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        for job in root:
            if job.findtext("./unit/unitXML/UUID") != transfer_uuid:
                continue
            for choice in job.findall("./choices/choice"):
                if choice.findtext("description") != "Reject transfer":
                    continue
                execute_url = f"{self.am_url}mcp/execute/"
                response = session.post(
                    execute_url,
                    data={
                        "csrfmiddlewaretoken": session.cookies.get("csrftoken"),
                        "uuid": job.findtext("UUID"),
                        "choice": choice.findtext("chainAvailable"),
                    },
                    headers={"Referer": list_url},
                    timeout=self.pessimistic_wait,
                )
                response.raise_for_status()
                return
        raise ArchivematicaAPIAbilityError(
            f"Unable to find the reject decision for transfer {transfer_uuid}"
        )

    def download_aip(self, transfer_name, sip_uuid, ss_api_key):
        """Use the AM SS API to download the completed AIP.
        Calls http://localhost:8000/api/v2/file/<SIP-UUID>/download/\
                  ?username=<SS-USERNAME>&api_key=<SS-API-KEY>
        """
        payload = {"username": self.ss_username, "api_key": ss_api_key}
        url = f"{self.ss_url}api/v2/file/{sip_uuid}/download/"
        aip_name = f"{transfer_name}-{sip_uuid}.7z"
        aip_path = os.path.join(self.tmp_path, aip_name)
        max_attempts = self.max_download_aip_attempts
        attempt = 0
        while True:
            r = requests.get(url, params=payload, stream=True)
            if r.ok:
                _save_download(r, aip_path)
                return aip_path
            elif r.status_code in (404, 500) and attempt < max_attempts:
                logger.warning(
                    "Trying again to download AIP %s via GET request to URL %s;"
                    " SS returned status code %s and message %s",
                    sip_uuid,
                    url,
                    r.status_code,
                    r.text,
                )
                attempt += 1
                time.sleep(self.optimistic_wait)
            else:
                logger.warning(
                    "Unable to download AIP %s via GET request to"
                    " URL %s; SS returned status code %s and message"
                    " %s",
                    sip_uuid,
                    url,
                    r.status_code,
                    r.text,
                )
                raise ArchivematicaAPIAbilityError(f"Unable to download AIP {sip_uuid}")

    def download_aip_pointer_file(self, sip_uuid, ss_api_key):
        """Use the AM SS API to download the completed AIP's pointer file.
        Calls http://localhost:8000/api/v2/file/<SIP-UUID>/pointer_file/\
                  ?username=<SS-USERNAME>&api_key=<SS-API-KEY>
        """
        payload = {"username": self.ss_username, "api_key": ss_api_key}
        url = f"{self.ss_url}api/v2/file/{sip_uuid}/pointer_file/"
        pointer_file_name = f"pointer.{sip_uuid}.xml"
        pointer_file_path = os.path.join(self.tmp_path, pointer_file_name)
        max_attempts = self.max_download_aip_attempts
        attempt = 0
        while True:
            r = requests.get(url, params=payload, stream=True)
            if r.ok:
                _save_download(r, pointer_file_path)
                return pointer_file_path
            elif r.status_code in (404, 500) and attempt < max_attempts:
                logger.warning(
                    "Trying again to download AIP %s pointer file via GET"
                    " request to URL %s; SS returned status code %s and message"
                    " %s",
                    sip_uuid,
                    url,
                    r.status_code,
                    r.text,
                )
                attempt += 1
                time.sleep(self.optimistic_wait)
            else:
                logger.warning(
                    "Unable to download AIP %s pointer file via GET"
                    " request to URL %s; SS returned status code %s"
                    " and message %s",
                    sip_uuid,
                    url,
                    r.status_code,
                    r.text,
                )
                raise ArchivematicaAPIAbilityError(
                    f"Unable to download AIP {sip_uuid} pointer file"
                )

    def poll_until_aip_stored(
        self, sip_uuid, ss_api_key, poll_interval=1, max_polls=None
    ):
        max_polls = max_polls or self.max_check_aip_stored_attempts
        payload = {"username": self.ss_username, "api_key": ss_api_key}
        url = f"{self.ss_url}api/v2/file/{sip_uuid}/"
        counter = 0
        while True:
            counter += 1
            if counter > max_polls:
                raise ArchivematicaAPIAbilityError(
                    "Polled too many times waiting for AIP %s to be stored" % sip_uuid
                )
            r = requests.get(url, params=payload)
            if r.ok:
                break
            time.sleep(poll_interval)


def _save_download(request, file_path):
    with open(file_path, "wb") as f:
        for block in request.iter_content(1024):
            f.write(block)
