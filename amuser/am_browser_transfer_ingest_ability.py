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
        ms_name = utils.normalize_ms_name(ms_name)
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

    def _decision_choices(self, decision_point, uuid_val, unit_type):
        decision_point = utils.normalize_ms_name(decision_point)
        decision_point, group_name = self.expose_job(
            decision_point, uuid_val, unit_type=unit_type
        )
        self.get_job_uuid(
            decision_point, group_name, uuid_val, job_outputs=("Awaiting decision",)
        )
        group = self.get_transfer_micro_service_group_elem(group_name, uuid_val)
        job, _ = self._job_for_microservice(group, decision_point)
        choices = job.locator("div.job-detail-actions select")
        choices.wait_for(
            state="visible", timeout=self._milliseconds(self.nihilistic_wait)
        )
        return choices

    @staticmethod
    def _matching_choices(choices, choice_text):
        expected = " ".join(choice_text.split()).casefold()
        matches = []
        for option in choices.locator("option").all():
            # Vue prefixes actual choices with "- "; the empty Actions option
            # is a placeholder and must never count as a workflow decision.
            label = " ".join(option.inner_text().split()).removeprefix("- ")
            if option.get_attribute("value") and label.casefold() == expected:
                matches.append(option)
        return matches

    def make_choice(self, choice_text, decision_point, uuid_val, unit_type="transfer"):
        """Choose one exact option at an awaiting microservice decision point."""
        choices = self._decision_choices(decision_point, uuid_val, unit_type)
        matches = self._matching_choices(choices, choice_text)
        if len(matches) != 1:
            raise ArchivematicaBrowserTransferIngestAbilityError(
                f'Expected one choice "{choice_text}" at "{decision_point}"; '
                f"found {len(matches)}"
            )
        choices.select_option(value=matches[0].get_attribute("value"))

    def assert_no_option(
        self, choice_text, decision_point, uuid_val, unit_type="transfer"
    ):
        """Assert that a choice is absent without executing any decision."""
        choices = self._decision_choices(decision_point, uuid_val, unit_type)
        if self._matching_choices(choices, choice_text):
            raise AssertionError(
                f'Choice "{choice_text}" is present at decision point '
                f'"{decision_point}" even though we expected it to be absent.'
            )

    def wait_for_microservice_visibility(self, ms_name, group_name, transfer_uuid):
        """Wait until a transfer's named microservice is visible."""
        microservice_group = self._transfer_microservice_group_locator(
            group_name, transfer_uuid
        )
        max_attempts = int(self.max_check_for_ms_visibility_attempts)
        timeout = sum(
            float(self.micro_wait if attempt < max_attempts / 2 else self.quick_wait)
            for attempt in range(max(0, max_attempts - 1))
        )
        name_pattern = utils.microservice_name_pattern(ms_name)
        name = microservice_group.locator(
            "div.job-detail-microservice > span[title]"
        ).filter(has_text=name_pattern)
        try:
            name.first.wait_for(
                state="visible",
                timeout=max(1, self._milliseconds(timeout)),
            )
        except PlaywrightTimeoutError as exc:
            raise ArchivematicaBrowserTransferIngestAbilityError(
                f'Unable to find microservice "{ms_name}" in group '
                f'"{group_name}" for {transfer_uuid} after {max_attempts} attempts'
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
