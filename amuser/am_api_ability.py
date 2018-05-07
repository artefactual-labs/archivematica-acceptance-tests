"""Archivematica API Ability.

This module contains the ``ArchivematicaAPIAbility`` class, which represents a
user's ability to use Archivematica's APIs to interact with Archivematica.
"""

import logging
import os
import time

import requests

from . import base
from . import utils


logger = logging.getLogger('ArchivematicaUser API')


class ArchivematicaAPIAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaAPIAbility(base.Base):
    """Represents an Archivematica (AM) user's ability to use AM's APIs to
    interact with AM.
    """

    def download_aip(self, transfer_name, sip_uuid, ss_api_key):
        """Use the AM SS API to download the completed AIP.
        Calls http://localhost:8000/api/v2/file/<SIP-UUID>/download/\
                  ?username=<SS-USERNAME>&api_key=<SS-API-KEY>
        """
        payload = {'username': self.ss_username, 'api_key': ss_api_key}
        url = '{}api/v2/file/{}/download/'.format(self.ss_url, sip_uuid)
        aip_name = '{}-{}.7z'.format(transfer_name, sip_uuid)
        aip_path = os.path.join(self.tmp_path, aip_name)
        max_attempts = 20
        attempt = 0
        while True:
            r = requests.get(url, params=payload, stream=True)
            if r.ok:
                _save_download(r, aip_path)
                return aip_path
            elif r.status_code in (404, 500) and attempt < max_attempts:
                logger.warning(
                    'Trying again to download AIP %s via GET request to URL %s;'
                    ' SS returned status code %s and message %s',
                    sip_uuid, url, r.status_code, r.text)
                attempt += 1
                time.sleep(1)
            else:
                logger.warning('Unable to download AIP %s via GET request to'
                               ' URL %s; SS returned status code %s and message'
                               ' %s', sip_uuid, url, r.status_code, r.text)
                raise ArchivematicaAPIAbilityError(
                    'Unable to download AIP {}'.format(sip_uuid))

    def download_aip_pointer_file(self, sip_uuid, ss_api_key):
        """Use the AM SS API to download the completed AIP's pointer file.
        Calls http://localhost:8000/api/v2/file/<SIP-UUID>/pointer_file/\
                  ?username=<SS-USERNAME>&api_key=<SS-API-KEY>
        """
        payload = {'username': self.ss_username, 'api_key': ss_api_key}
        url = '{}api/v2/file/{}/pointer_file/'.format(self.ss_url, sip_uuid)
        pointer_file_name = 'pointer.{}.xml'.format(sip_uuid)
        pointer_file_path = os.path.join(self.tmp_path, pointer_file_name)
        max_attempts = 20
        attempt = 0
        while True:
            r = requests.get(url, params=payload, stream=True)
            if r.ok:
                _save_download(r, pointer_file_path)
                return pointer_file_path
            elif r.status_code in (404, 500) and attempt < max_attempts:
                logger.warning(
                    'Trying again to download AIP %s pointer file via GET'
                    ' request to URL %s; SS returned status code %s and message'
                    ' %s', sip_uuid, url, r.status_code, r.text)
                attempt += 1
                time.sleep(1)
            else:
                logger.warning('Unable to download AIP %s pointer file via GET'
                               ' request to URL %s; SS returned status code %s'
                               ' and message %s', sip_uuid, url, r.status_code,
                               r.text)
                raise ArchivematicaAPIAbilityError(
                    'Unable to download AIP {} pointer file'.format(sip_uuid))

    def poll_until_aip_stored(self, sip_uuid, ss_api_key, poll_interval=1,
                              max_polls=60):
        payload = {'username': self.ss_username, 'api_key': ss_api_key}
        url = '{}api/v2/file/{}/'.format(self.ss_url, sip_uuid)
        counter = 0
        while True:
            counter += 1
            if counter > max_polls:
                raise ArchivematicaAPIAbilityError(
                    'Polled too many times waiting for AIP %s to be stored',
                    sip_uuid)
            r = requests.get(url, params=payload)
            if r.ok:
                break
            time.sleep(poll_interval)


def _save_download(request, file_path):
    with open(file_path, 'wb') as f:
        for block in request.iter_content(1024):
            f.write(block)
