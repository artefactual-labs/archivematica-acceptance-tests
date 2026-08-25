"""Archivematica Browser Jobs & Tasks Ability."""

import logging
import re
from urllib.parse import urljoin

from playwright.sync_api import expect

from . import base
from . import constants as c
from . import playwright_ability
from . import utils

logger = logging.getLogger("amuser.jobstasks")


class ArchivematicaBrowserJobsTasksAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaBrowserJobsTasksAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Inspect Archivematica jobs and their task output."""

    @staticmethod
    def _job_result_key(microservice_name, transfer_uuid):
        return transfer_uuid, utils.canonical_microservice_name(microservice_name)

    def remember_job_result(self, microservice_name, transfer_uuid, result):
        """Retain a completed job that may leave the processing monitor."""
        if not hasattr(self, "_completed_job_results"):
            self._completed_job_results = {}
        key = self._job_result_key(microservice_name, transfer_uuid)
        self._completed_job_results[key] = result

    def recalled_job_result(self, microservice_name, transfer_uuid):
        """Return a previously observed completed job, when available."""
        key = self._job_result_key(microservice_name, transfer_uuid)
        return getattr(self, "_completed_job_results", {}).get(key)

    @staticmethod
    def _job_for_microservice(microservice_group, microservice_name):
        name_pattern = utils.microservice_name_pattern(microservice_name)
        name = microservice_group.locator(
            "div.job-detail-microservice > span[title]"
        ).filter(has_text=name_pattern)
        if not name.count():
            return None, None
        name = name.first
        job = name.locator(
            "xpath=ancestor::div["
            "contains(concat(' ', normalize-space(@class), ' '), ' job ')][1]"
        )
        return job, name

    def _expand_microservice_group(self, microservice_group):
        job_container = microservice_group.locator("div.job-container")
        if job_container.count() == 0:
            job_container = microservice_group.locator("div.microservice-group + div")
        if job_container.locator("div.job").first.is_visible():
            return
        heading = microservice_group.locator("div.microservice-group")
        if heading.count():
            # Click the label, since the center of a wide heading can overlap
            # floated job rows. Keep normal visibility and pointer checks.
            label = heading.locator("span.microservice-group-name")
            (label.first if label.count() else heading.first).click()
        else:
            microservice_group.click()
        job_container.locator("div.job").first.wait_for(
            state="visible", timeout=self._milliseconds(self.pessimistic_wait)
        )

    def get_job_output(self, ms_name, transfer_uuid):
        """Return the current output for a transfer microservice job."""
        ms_name, group_name = utils.micro_service2group(ms_name)
        microservice_group = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        if not microservice_group:
            return None
        job, _ = self._job_for_microservice(microservice_group, ms_name)
        if not job:
            return None
        output = job.locator("div.job-detail-currentstep span")
        return output.inner_text().strip() if output.is_visible() else ""

    def expose_job(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Expand and wait for a microservice job."""
        logger.info("Exposing job %s", ms_name)
        unit_url = self.get_transfer_url()
        if unit_type != "transfer":
            unit_url = self.get_ingest_url()
        # Lazy job groups are snapshots loaded when their unit is expanded.
        # Refresh before expanding so a prior job lookup cannot leave us
        # polling a stale snapshot for the next workflow step.
        self.navigate(unit_url, reload=True)
        ms_name, group_name = utils.micro_service2group(ms_name)
        self.wait_for_presence(f"#sip-row-{transfer_uuid}")
        unit_row = self.page.locator(f"#sip-row-{transfer_uuid}")
        unit = unit_row.locator("xpath=..")
        unit_classes = (unit.get_attribute("class") or "").split()
        if (
            "sip-expanded" not in unit_classes
            and unit.locator("div.microservicegroup").count() == 0
        ):
            unit_row.locator(".sip-detail-directory").click()
        self.wait_for_transfer_micro_service_group(group_name, transfer_uuid)
        microservice_group = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        self._expand_microservice_group(microservice_group)
        self.wait_for_microservice_visibility(ms_name, group_name, transfer_uuid)
        logger.info("Exposed job %s (%s)", ms_name, group_name)
        return ms_name, group_name

    def parse_job(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Return a job's completion output and parsed task records."""
        ms_name, group_name = utils.micro_service2group(ms_name)
        job_result = self.recalled_job_result(ms_name, transfer_uuid)
        if job_result is None:
            ms_name, group_name = self.expose_job(ms_name, transfer_uuid, unit_type)
            job_result = self.get_job_uuid(ms_name, group_name, transfer_uuid)
        job_uuid, job_output = job_result
        table_dict = {"job_output": job_output, "tasks": {}}
        if not job_uuid:
            raise ArchivematicaBrowserJobsTasksAbilityError(
                f'Missing job UUID for microservice "{ms_name}" in group '
                f'"{group_name}" for {transfer_uuid}; unable to verify task output'
            )
        return self.parse_tasks_table(self.get_tasks_url(job_uuid), table_dict)

    def parse_tasks_table(self, tasks_url, table_dict):
        """Parse every page of task output without replacing the main page."""
        with self.temporary_page():
            next_tasks_url = tasks_url
            while next_tasks_url:
                self.navigate(next_tasks_url)
                self.wait_for_presence("article.task")
                for task in self.page.locator("article.task").all():
                    row = {
                        "stdout": self._optional_text(task, ".panel-info pre"),
                        "stderr": self._optional_text(task, ".panel-danger pre"),
                        "command": task.locator("h3.panel-title.panel-title-simple")
                        .inner_text()
                        .strip(),
                    }
                    arguments = (
                        task.locator("div.panel-primary div.shell-output pre")
                        .inner_text()
                        .strip()
                    )
                    row["arguments"] = utils.parse_task_arguments_to_list(arguments)
                    for definition_list in task.locator("div.row dl").all():
                        for term in definition_list.locator("dt").all():
                            attr = term.inner_text().strip().lower().replace(" ", "_")
                            value = term.locator("xpath=following-sibling::dd[1]")
                            row[attr] = value.inner_text().strip()
                    row["task_uuid"] = (
                        task.locator("div.task-heading h4")
                        .inner_text()
                        .strip()
                        .split()[1]
                    )
                    table_dict["tasks"][row["task_uuid"]] = row
                next_button = self.page.get_by_role("link", name="Next page")
                if not next_button.count():
                    next_tasks_url = None
                else:
                    href = next_button.first.get_attribute("href")
                    next_tasks_url = urljoin(self.am_url, href) if href else None
        return table_dict

    @staticmethod
    def _optional_text(container, selector):
        element = container.locator(selector)
        return element.first.inner_text().strip() if element.count() else ""

    def get_job_uuid(
        self,
        ms_name,
        group_name,
        transfer_uuid,
        job_outputs=c.JOB_OUTPUTS_COMPLETE,
    ):
        """Wait for a job to finish, then return its UUID and output."""
        max_attempts = int(self.max_check_job_status_attempts)
        microservice_group = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        job, name = self._job_for_microservice(microservice_group, ms_name)
        output = job.locator("div.job-detail-currentstep span:visible")
        output_pattern = re.compile(
            r"^\s*(?:"
            + "|".join(re.escape(job_output) for job_output in job_outputs)
            + r")\s*$"
        )
        try:
            expect(output).to_be_visible(
                timeout=self._milliseconds(self.pessimistic_wait)
            )
            expect(output).to_have_text(
                output_pattern,
                timeout=self._milliseconds(max_attempts * float(self.quick_wait)),
            )
        except AssertionError as exc:
            last_output = output.inner_text().strip() if output.count() else None
            expected_outputs = ", ".join(repr(value) for value in job_outputs)
            raise ArchivematicaBrowserJobsTasksAbilityError(
                f'Timed out waiting for job "{ms_name}" in group '
                f'"{group_name}" for {transfer_uuid} after {max_attempts} '
                f"attempts; last output was {last_output!r}; expected one of "
                f"{expected_outputs}"
            ) from exc
        job_uuid = name.get_attribute("title")
        return job_uuid.strip() if job_uuid else None, output.inner_text().strip()
