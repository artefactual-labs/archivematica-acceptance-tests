"""Archivematica Transfer & Ingest Tabs Ability"""

import logging
import sys
import time

from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

from . import utils
from . import base
from . import selenium_ability
from . import am_browser_jobs_tasks_ability as jobs_tasks_abl
from . import am_browser_file_explorer_ability as file_explorer_abl
from . import am_browser_transfer_ability as transfer_abl
from . import am_browser_ingest_ability as ingest_abl


logger = logging.getLogger("amuser.transferingest")


class ArchivematicaBrowserTransferIngestAbilityError(base.ArchivematicaUserError):
    pass


class ArchivematicaBrowserTransferIngestAbility(
    jobs_tasks_abl.ArchivematicaBrowserJobsTasksAbility,
    file_explorer_abl.ArchivematicaBrowserFileExplorerAbility,
    transfer_abl.ArchivematicaBrowserTransferAbility,
    ingest_abl.ArchivematicaBrowserIngestAbility,
):
    """Archivematica Browser Transfer & Ingest Tabs Ability."""

    def await_job_completion(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Wait for the job representing the execution of micro-service
        ``ms_name`` on the unit with UUID ``transfer_uuid`` to complete.
        """
        ms_name, group_name = self.expose_job(ms_name, transfer_uuid, unit_type)
        job_uuid, job_output = self.get_job_uuid(ms_name, group_name, transfer_uuid)
        return job_uuid, job_output

    def await_decision_point(self, ms_name, transfer_uuid, unit_type="transfer"):
        """Wait for the decision point job for micro-service ``ms_name`` to
        appear.
        """
        ms_name = utils.normalize_ms_name(ms_name, self.vn)
        logger.info(
            'Await decision point "%s" with unit %s of type %s',
            ms_name,
            transfer_uuid,
            unit_type,
        )
        ms_name, group_name = self.expose_job(ms_name, transfer_uuid, unit_type)
        job_uuid, job_output = self.get_job_uuid(
            ms_name, group_name, transfer_uuid, job_outputs=("Awaiting decision",)
        )
        return job_uuid, job_output

    @selenium_ability.recurse_on_stale
    def make_choice(self, choice_text, decision_point, uuid_val, unit_type="transfer"):
        """Make the choice matching the text ``choice_text`` at decision point
        (i.e., microservice) job matching ``decision_point``.
        """
        decision_point = utils.normalize_ms_name(decision_point, self.vn)
        decision_point, group_name = self.expose_job(
            decision_point, uuid_val, unit_type=unit_type
        )
        ms_group_elem = self.get_transfer_micro_service_group_elem(group_name, uuid_val)
        action_div_el = None
        for job_elem in ms_group_elem.find_elements_by_css_selector("div.job"):
            for span_elem in job_elem.find_elements_by_css_selector(
                "div.job-detail-microservice span"
            ):
                if utils.squash(span_elem.text) == utils.squash(decision_point):
                    action_div_el = job_elem.find_element_by_css_selector(
                        "div.job-detail-actions"
                    )
                    break
            if action_div_el:
                break
        if action_div_el:
            try:
                select_el = action_div_el.find_element_by_css_selector("select")
            except NoSuchElementException:
                time.sleep(self.quick_wait)
                return self.make_choice(
                    choice_text, decision_point, uuid_val, unit_type=unit_type
                )
            index = None
            for i, option_el in enumerate(
                select_el.find_elements_by_tag_name("option")
            ):
                if utils.squash(choice_text) in utils.squash(option_el.text):
                    index = i
            if index is not None:
                Select(select_el).select_by_index(index)
            else:
                raise ArchivematicaBrowserTransferIngestAbilityError(
                    'Unable to select choice "{}"'.format(choice_text)
                )
        else:
            raise ArchivematicaBrowserTransferIngestAbilityError(
                "Unable to find decision point {}".format(decision_point)
            )

    def assert_no_option(
        self, choice_text, decision_point, uuid_val, unit_type="transfer"
    ):
        """Assert that the option ``choice_text`` is not available for
        ``decision_point`` by attempting to make it and expecting an error with
        the "Unable to select choice" error message.
        """
        try:
            self.make_choice(choice_text, decision_point, uuid_val, unit_type=unit_type)
        except ArchivematicaBrowserTransferIngestAbilityError as exc:
            assert 'Unable to select choice "{}"'.format(choice_text) == str(exc)
        else:
            raise AssertionError(
                'We were able to select choice "{}" at decision point "{}" even'
                " though we expected this not to be possible.".format(
                    choice_text, decision_point
                )
            )

    @selenium_ability.recurse_on_stale
    def wait_for_microservice_visibility(
        self, ms_name, group_name, transfer_uuid, level=0
    ):
        """Wait until micro-service ``ms_name`` of transfer ``transfer_uuid``
        is visible.
        """
        ms_group_elem = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        for job_elem in ms_group_elem.find_elements_by_css_selector("div.job"):
            for span_elem in job_elem.find_elements_by_css_selector(
                "div.job-detail-microservice span"
            ):
                if utils.squash(span_elem.text) == utils.squash(ms_name):
                    return
        if level < (sys.getrecursionlimit() / 2):
            # The job is taking a long time to complete. Half the
            # amount of checking to avoid stack-overflow.
            logger.warning(
                "Recursion limit close to being reached: level: {} <= {}".format(
                    level, sys.getrecursionlimit()
                )
            )
            time.sleep(self.micro_wait)
        else:
            time.sleep(self.quick_wait)
        level += 1
        try:
            self.wait_for_microservice_visibility(ms_name, group_name, transfer_uuid)
        except RecursionError:
            logger.error(
                "Recursion depth exceeded waiting for microservice visibility, consider re-running the test"
            )

    @selenium_ability.recurse_on_stale
    def click_show_tasks_button(self, ms_name, group_name, transfer_uuid):
        """Click the gear icon that triggers the displaying of tasks in a new
        tab.
        Note: this is not currently being used because the strategy of just
        generating the tasks URL and then opening it with a new Selenium web
        driver seems to be easier than juggling multiple tabs.
        """
        ms_group_elem = self.get_transfer_micro_service_group_elem(
            group_name, transfer_uuid
        )
        for job_elem in ms_group_elem.find_elements_by_css_selector("div.job"):
            for span_elem in job_elem.find_elements_by_css_selector(
                "div.job-detail-microservice span"
            ):
                if span_elem.text.strip() == ms_name:
                    job_elem.find_element_by_css_selector(
                        "div.job-detail-actions a.btn_show_tasks"
                    ).click()

    def wait_for_transfer_micro_service_group(self, group_name, transfer_uuid):
        """Wait for the micro-service group with name ``group_name`` to appear
        in the Transfer tab.
        """
        max_attempts = self.max_check_for_ms_group_attempts
        attempts = 0
        while True:
            if attempts > max_attempts:
                msg = (
                    "Exceeded maxumim allowable attempts ({}) for checking"
                    " whether micro-service group {} of transfer {} is"
                    " visible.".format(max_attempts, group_name, transfer_uuid)
                )
                logger.warning(msg)
                raise ArchivematicaBrowserTransferIngestAbilityError(msg)
            ms_group_elem = self.get_transfer_micro_service_group_elem(
                group_name, transfer_uuid
            )
            if ms_group_elem:
                return
            time.sleep(self.quick_wait)
            attempts += 1

    @selenium_ability.recurse_on_stale
    def get_transfer_micro_service_group_elem(self, group_name, transfer_uuid):
        """Get the DOM element (<div>) representing the micro-service group
        with name ``group_name`` of the transfer with UUID ``transfer_uuid``.
        """
        transfer_div_elem = None
        transfer_dom_id = "sip-row-{}".format(transfer_uuid)
        for elem in self.driver.find_elements_by_css_selector("div.sip"):
            try:
                elem.find_element_by_id(transfer_dom_id)
                transfer_div_elem = elem
            except NoSuchElementException:
                pass
        if not transfer_div_elem:
            logger.warning("Unable to find Transfer %s.", transfer_uuid)
            return None
        if self.vn == "1.6":
            expected_name = "Micro-service: {}".format(group_name)
        else:
            expected_name = "Microservice: {}".format(group_name)
        result = None
        for ms_group_elem in transfer_div_elem.find_elements_by_css_selector(
            "div.microservicegroup"
        ):
            name_elem_text = ms_group_elem.find_element_by_css_selector(
                "span.microservice-group-name"
            ).text.strip()
            if name_elem_text == expected_name:
                logger.info(
                    'DOM name "%s" MATCHES expected name "%s"',
                    name_elem_text,
                    expected_name,
                )
                result = ms_group_elem
                break
        return result
