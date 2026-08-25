"""Archivematica Transfer & Ingest Tabs Ability."""

import logging
import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from . import am_browser_file_explorer_ability as file_explorer_abl
from . import am_browser_ingest_ability as ingest_abl
from . import am_browser_jobs_tasks_ability as jobs_tasks_abl
from . import am_browser_transfer_ability as transfer_abl
from . import base
from . import utils

logger = logging.getLogger("amuser.transferingest")


class ArchivematicaBrowserTransferIngestAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaBrowserTransferIngestAbility(
    jobs_tasks_abl.ArchivematicaBrowserJobsTasksAbility,
    file_explorer_abl.ArchivematicaBrowserFileExplorerAbility,
    transfer_abl.ArchivematicaBrowserTransferAbility,
    ingest_abl.ArchivematicaBrowserIngestAbility,
):
    """Interact with the Transfer and Ingest tabs."""

    def await_job_completion(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Wait for a unit's microservice job to complete."""
        ms_name, group_name = self.expose_job(ms_name, transfer_uuid, unit_type)
        result = self.get_job_uuid(ms_name, group_name, transfer_uuid)
        self.remember_job_result(ms_name, transfer_uuid, result)
        return result

    def await_decision_point(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Wait for a decision-point job to appear."""
        ms_name = utils.normalize_ms_name(ms_name, self.vn)
        logger.info(
            'Await decision point "%s" with unit %s of type %s',
            ms_name,
            transfer_uuid,
            unit_type,
        )
        ms_name, group_name = self.expose_job(ms_name, transfer_uuid, unit_type)
        return self.get_job_uuid(
            ms_name,
            group_name,
            transfer_uuid,
            job_outputs=("Awaiting decision",),
        )

    def make_choice(self, choice_text, decision_point, uuid_val, unit_type="transfer"):
        """Choose an option at a microservice decision point."""
        decision_point = utils.normalize_ms_name(decision_point, self.vn)
        decision_point, group_name = self.expose_job(
            decision_point, uuid_val, unit_type=unit_type
        )
        microservice_group = self.get_transfer_micro_service_group_elem(
            group_name, uuid_val
        )
        job, _ = self._job_for_microservice(microservice_group, decision_point)
        if not job:
            raise ArchivematicaBrowserTransferIngestAbilityError(
                f"Unable to find decision point {decision_point}"
            )
        choices = job.locator("div.job-detail-actions select")
        choices.wait_for(
            state="attached", timeout=self._milliseconds(self.nihilistic_wait)
        )
        for index, option in enumerate(choices.locator("option").all()):
            if utils.squash(choice_text) in utils.squash(option.inner_text()):
                choices.select_option(index=index)
                return
        raise ArchivematicaBrowserTransferIngestAbilityError(
            f'Unable to select choice "{choice_text}"'
        )

    def assert_no_option(
        self, choice_text, decision_point, uuid_val, unit_type="transfer"
    ):
        """Assert that a choice is unavailable at a decision point."""
        try:
            self.make_choice(choice_text, decision_point, uuid_val, unit_type=unit_type)
        except ArchivematicaBrowserTransferIngestAbilityError as exc:
            assert f'Unable to select choice "{choice_text}"' == str(exc)
        else:
            raise AssertionError(
                f'We were able to select choice "{choice_text}" at decision point '
                f'"{decision_point}" even though we expected this not to be possible.'
            )

    def wait_for_microservice_visibility(self, ms_name, group_name, transfer_uuid):
        """Wait until a transfer's named microservice is present."""
        microservice_group = self._transfer_microservice_group_locator(
            group_name, transfer_uuid
        )
        variants = utils.microservice_name_variants(ms_name)
        name_pattern = re.compile(
            r"^\s*(?:" + "|".join(re.escape(name) for name in variants) + r")\s*$",
            re.IGNORECASE,
        )
        name = microservice_group.locator("div.job-detail-microservice span").filter(
            has_text=name_pattern
        )
        try:
            name.first.wait_for(
                state="attached",
                timeout=self._milliseconds(
                    int(self.max_check_for_ms_group_attempts) * float(self.micro_wait)
                ),
            )
        except PlaywrightTimeoutError as exc:
            raise ArchivematicaBrowserTransferIngestAbilityError(
                f'Unable to find microservice "{ms_name}" in group '
                f'"{group_name}" for {transfer_uuid}'
            ) from exc

    def click_show_tasks_button(self, ms_name, group_name, transfer_uuid):
        """Open the task list for a microservice job."""
        microservice_group = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        job, _ = self._job_for_microservice(microservice_group, ms_name)
        if job:
            job.locator("div.job-detail-actions a.btn_show_tasks").click()

    def wait_for_transfer_micro_service_group(self, group_name, transfer_uuid):
        """Wait for a microservice group to appear."""
        max_attempts = int(self.max_check_for_ms_group_attempts)
        group = self._transfer_microservice_group_locator(group_name, transfer_uuid)
        try:
            group.wait_for(
                state="attached",
                timeout=self._milliseconds(max_attempts * float(self.quick_wait)),
            )
        except PlaywrightTimeoutError as exc:
            msg = (
                f"Exceeded maximum allowable attempts ({max_attempts}) for "
                f"checking whether microservice group {group_name} of "
                f"transfer {transfer_uuid} is visible."
            )
            logger.warning(msg)
            raise ArchivematicaBrowserTransferIngestAbilityError(msg) from exc

    def _transfer_microservice_group_locator(self, group_name, transfer_uuid):
        transfer = self.page.locator(f'div.sip:has([id="sip-row-{transfer_uuid}"])')
        prefix = "Micro-service" if self.vn == "1.6" else "Microservice"
        expected_name = f"{prefix}: {group_name}"
        name = transfer.locator("span.microservice-group-name").filter(
            has_text=re.compile(rf"^\s*{re.escape(expected_name)}\s*$")
        )
        return name.first.locator(
            "xpath=ancestor::div["
            "contains(concat(' ', normalize-space(@class), ' '), "
            "' microservicegroup ')][1]"
        )

    def get_transfer_micro_service_group_elem(self, group_name, transfer_uuid):
        """Return the locator for a transfer's named microservice group."""
        transfer = self.page.locator(f'div.sip:has([id="sip-row-{transfer_uuid}"])')
        if transfer.count() == 0:
            logger.warning("Unable to find Transfer %s.", transfer_uuid)
            return None
        group = self._transfer_microservice_group_locator(group_name, transfer_uuid)
        return group if group.count() else None
