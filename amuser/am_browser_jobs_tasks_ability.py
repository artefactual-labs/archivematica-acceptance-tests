"""Archivematica Browser Jobs & Tasks Ability"""

import logging
import time

from selenium.common.exceptions import NoSuchElementException

from . import constants as c
from . import utils
from . import selenium_ability


logger = logging.getLogger("amuser.jobstasks")


class ArchivematicaBrowserJobsTasksAbility(
    selenium_ability.ArchivematicaSeleniumAbility
):
    """Archivematica Browser Jobs & Tasks Ability."""

    @selenium_ability.recurse_on_stale
    def get_job_output(self, ms_name, transfer_uuid):
        """Get the output---"Completed successfully", "Failed"---of the Job
        model representing the execution of micro-service ``ms_name`` in
        transfer ``transfer_uuid``.
        """
        ms_name, group_name = utils.micro_service2group(ms_name)
        ms_group_elem = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        for job_elem in ms_group_elem.find_elements_by_css_selector("div.job"):
            for span_elem in job_elem.find_elements_by_css_selector(
                "div.job-detail-microservice span"
            ):
                if span_elem.text.strip() == ms_name:
                    return job_elem.find_element_by_css_selector(
                        "div.job-detail-currentstep span"
                    ).text.strip()
        return None

    def expose_job(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Expose (i.e., click MS group and wait for appearance of) the job
        representing the execution of the micro-service named ``ms_name`` on
        the transfer/SIP with UUID ``transfer_uuid``.
        """
        logger.info("exposing job %s", ms_name)
        # Navigate to the Transfers or Ingest tab, depending on ``unit_type``
        # (if we're not there already)
        unit_url = self.get_transfer_url()
        if unit_type != "transfer":
            unit_url = self.get_ingest_url()
        self.navigate(unit_url)
        ms_name, group_name = utils.micro_service2group(ms_name)
        logger.info("expecting job %s to be in group %s", ms_name, group_name)
        # If not visible, click the micro-service group to expand it.
        self.wait_for_transfer_micro_service_group(group_name, transfer_uuid)
        is_visible = (
            self.get_transfer_micro_service_group_elem(group_name, transfer_uuid)
            .find_element_by_css_selector("div.microservice-group + div")
            .is_displayed()
        )
        if not is_visible:
            self.get_transfer_micro_service_group_elem(
                group_name, transfer_uuid
            ).click()
        self.wait_for_microservice_visibility(ms_name, group_name, transfer_uuid)
        logger.info("exposed job %s (%s)", ms_name, group_name)
        return ms_name, group_name

    def parse_job(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Parse the job representing the execution of the micro-service named
        ``ms_name`` on the transfer with UUID ``transfer_uuid``. Return a dict
        containing the ``job_output`` (e.g., "Failed") and the parsed tasks
        <table> as a dict with the following format::
            >>> {
                    '<task_uuid>': {
                        'task_uuid': '...',
                        'file_uuid': '...',
                        'file_name': '...',
                        'client': '...',
                        'exit_code': '...',
                        'command': '...',
                        'arguments': [...],
                        'stdout': '...',
                        'stderr': '...'
                    },
                    '<task_uuid>': { ... }
                }
        """
        ms_name, group_name = self.expose_job(ms_name, transfer_uuid, unit_type)
        # If we don't wait for a second here, then sometimes the tasks page
        # returns incorrect data because (assumedly) the tasks haven't been
        # written to disk correctly (?) What happens is that tasks will have an
        # exit code of 'None' in the interface but when you look at them in the
        # db, they have a sensible exit code.
        # TODO: this doesn't solve the problem. Figure out why these strange
        # exit codes sometimes show up.
        time.sleep(self.optimistic_wait)
        # Getting the Job UUID also means waiting for the job to terminate.
        job_uuid, job_output = self.get_job_uuid(ms_name, group_name, transfer_uuid)
        # Open the tasks in a new browser window with a new
        # Selenium driver; then parse the table there.
        table_dict = {"job_output": job_output, "tasks": {}}
        tasks_url = self.get_tasks_url(job_uuid)
        table_dict = self.parse_tasks_table(tasks_url, table_dict)
        return table_dict

    def parse_tasks_table(self, tasks_url, table_dict):
        old_driver = self.driver
        table_dict = self._parse_tasks_table(tasks_url, table_dict, self.vn)
        self.driver = old_driver
        return table_dict

    def _parse_tasks_table(self, tasks_url, table_dict, vn):
        return {
            "1.6": self._parse_tasks_table_am_1_6,
            "1.7": self._parse_tasks_table_am_gte_1_7,
            "1.8": self._parse_tasks_table_am_gte_1_7,
        }.get(vn, self._parse_tasks_table_am_1_6)(tasks_url, table_dict)

    def _parse_tasks_table_am_1_6(self, tasks_url, table_dict):
        self.driver = self.get_driver()
        if self.driver.current_url != tasks_url:
            self.login()
        self.driver.get(tasks_url)
        self.wait_for_presence("table")
        # Parse the <table> to a dict and return it.
        table_elem = self.driver.find_element_by_tag_name("table")
        row_dict = {}
        for row_elem in table_elem.find_elements_by_tag_name("tr"):
            row_type = get_tasks_row_type(row_elem)
            if row_type == "header":
                if row_dict:
                    table_dict["tasks"][row_dict["task_uuid"]] = row_dict
                row_dict = process_task_header_row(row_elem, {})
            elif row_type == "command":
                row_dict = process_task_command_row(row_elem, row_dict)
            elif row_type == "stdout":
                row_dict = process_task_stdout_row(row_elem, row_dict)
            else:
                row_dict = process_task_stderr_row(row_elem, row_dict)
        table_dict["tasks"][row_dict["task_uuid"]] = row_dict
        next_tasks_url = None
        for link_button in self.driver.find_elements_by_css_selector("a.btn"):
            if link_button.text.strip() == "Next Page":
                next_tasks_url = "{}{}".format(
                    self.am_url, link_button.get_attribute("href")
                )
        self.driver.quit()
        if next_tasks_url:
            table_dict = self._parse_tasks_table_am_1_6(next_tasks_url, table_dict)
        return table_dict

    def _parse_tasks_table_am_gte_1_7(self, tasks_url, table_dict):
        """Parse all the Task <article> elements at ``task_url`` and return
        them as a dict in ``table_dict``. Note: <table> elements are no longer
        used in AM 1.7+ for this but we call the returned dict a ``table_dict``
        anyway.
        """
        self.driver = self.get_driver()
        if self.driver.current_url != tasks_url:
            self.login()
        self.driver.get(tasks_url)
        self.wait_for_presence("article.task")
        for task_art_elem in self.driver.find_elements_by_css_selector("article.task"):
            row_dict = {}
            try:
                row_dict["stdout"] = task_art_elem.find_element_by_css_selector(
                    ".panel-info pre"
                ).text.strip()
            except NoSuchElementException:
                row_dict["stdout"] = ""
            try:
                row_dict["stderr"] = task_art_elem.find_element_by_css_selector(
                    ".panel-danger pre"
                ).text.strip()
            except NoSuchElementException:
                row_dict["stderr"] = ""
            row_dict["command"] = task_art_elem.find_element_by_css_selector(
                "h3.panel-title.panel-title-simple"
            ).text.strip()
            arguments = task_art_elem.find_element_by_css_selector(
                "div.panel-primary div.shell-output pre"
            ).text.strip()
            row_dict["arguments"] = utils.parse_task_arguments_to_list(arguments)
            for dl_el in task_art_elem.find_elements_by_css_selector("div.row dl"):
                for el in dl_el.find_elements_by_css_selector("*"):
                    if el.tag_name == "dt":
                        attr = el.text.strip().lower().replace(" ", "_")
                    else:
                        val = el.text.strip()
                        row_dict[attr] = val
            row_dict["task_uuid"] = (
                task_art_elem.find_element_by_css_selector("div.task-heading h4")
                .text.strip()
                .split()[1]
            )
            table_dict["tasks"][row_dict["task_uuid"]] = row_dict
        next_tasks_url = None
        for link_button in self.driver.find_elements_by_css_selector("a.btn"):
            if link_button.text.strip() == "Next page":
                next_tasks_url = "{}{}".format(
                    self.am_url, link_button.get_attribute("href")
                )
        self.driver.quit()
        if next_tasks_url:
            table_dict = self._parse_tasks_table_am_gte_1_7(next_tasks_url, table_dict)
        return table_dict

    @selenium_ability.recurse_on_stale
    def get_job_uuid(
        self, ms_name, group_name, transfer_uuid, job_outputs=c.JOB_OUTPUTS_COMPLETE
    ):
        """Get the UUID of the Job model representing the execution of
        micro-service ``ms_name`` in transfer ``transfer_uuid``.
        """
        ms_group_elem = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        for job_elem in ms_group_elem.find_elements_by_css_selector("div.job"):
            for span_elem in job_elem.find_elements_by_css_selector(
                "div.job-detail-microservice span"
            ):
                if utils.squash(span_elem.text) == utils.squash(ms_name):
                    job_output = job_elem.find_element_by_css_selector(
                        "div.job-detail-currentstep span"
                    ).text.strip()
                    if job_output in job_outputs:
                        return (span_elem.get_attribute("title").strip(), job_output)
                    time.sleep(self.quick_wait)
                    return self.get_job_uuid(ms_name, group_name, transfer_uuid)
        return None, None


def process_task_header_row(row_elem, row_dict):
    """Parse the text in the first tasks <tr>, the one "File UUID:"."""
    for line in row_elem.find_element_by_tag_name("td").text.strip().split("\n"):
        line = line.strip()
        if line.startswith("("):
            line = line[1:]
        if line.endswith(")"):
            line = line[:-1]
        attr, val = [x.strip() for x in line.split(":")]
        row_dict[attr.lower().replace(" ", "_")] = val
    return row_dict


def process_task_command_row(row_elem, row_dict):
    """Parse the text in the second tasks <tr>, the one specifying command
    and arguments.
    """
    command_text = row_elem.find_element_by_tag_name("td").text.strip().split(":")[1]
    command, *arguments = command_text.split()
    row_dict["command"] = command
    arguments = " ".join(arguments)
    row_dict["arguments"] = utils.parse_task_arguments_to_list(arguments)
    return row_dict


def process_task_stdout_row(row_elem, row_dict):
    """Parse out the tasks's stdout from the <table>."""
    row_dict["stdout"] = row_elem.find_element_by_tag_name("pre").text.strip()
    return row_dict


def process_task_stderr_row(row_elem, row_dict):
    """Parse out the tasks's stderr from the <table>."""
    row_dict["stderr"] = row_elem.find_element_by_tag_name("pre").text.strip()
    return row_dict


def get_tasks_row_type(row_elem):
    """Induce the type of the row ``row_elem`` in the tasks table.
    Note: tasks are represented as a table where blocks of adjacent rows
    represent the outcome of a single task. All tasks appear to have
    "header" and "command" rows, but not all have "sdtout" and "stderr(or)"
    rows.
    """
    if row_elem.get_attribute("class").strip():
        return "header"
    try:
        row_elem.find_element_by_css_selector("td.stdout")
        return "stdout"
    except NoSuchElementException:
        pass
    try:
        row_elem.find_element_by_css_selector("td.stderror")
        return "stderr"
    except NoSuchElementException:
        pass
    return "command"
