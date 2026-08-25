"""Check that broken monitor UI cannot satisfy job and task assertions."""

import unittest
from html import escape
from unittest import mock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from amuser import utils
from amuser.am_browser_ability import ArchivematicaBrowserAbility
from amuser.am_browser_jobs_tasks_ability import (
    ArchivematicaBrowserJobsTasksAbilityError,
)
from amuser.am_browser_transfer_ingest_ability import (
    ArchivematicaBrowserTransferIngestAbilityError,
)

TRANSFER_UUID = "00000000-0000-0000-0000-000000000001"
JOB_UUID = "00000000-0000-0000-0000-000000000002"
TASK_UUID = "00000000-0000-0000-0000-000000000003"
MICROSERVICE = "Policy checks for originals"
GROUP = "Validation"


class BrowserJobChecks:
    @classmethod
    def setUpClass(cls):
        headless = mock.patch.dict("os.environ", {"HEADLESS": "1"})
        headless.start()
        cls.addClassCleanup(headless.stop)
        owner = ArchivematicaBrowserAbility(browser_name=cls.browser_name)
        cls.runtime = owner.create_playwright_runtime()
        cls.addClassCleanup(cls.runtime.stop)
        cls.runtime.start()

    def setUp(self):
        self.ability = ArchivematicaBrowserAbility(
            playwright_runtime=self.runtime,
            am_url="http://fixture.invalid/",
            am_version="1.18",
            pessimistic_wait=0.5,
            nihilistic_wait=0.5,
            micro_wait=0.5,
            quick_wait=0.5,
            max_check_for_ms_visibility_attempts=2,
            max_check_job_status_attempts=2,
        )
        self.addCleanup(self.ability.tear_down)
        self.ability.set_up()
        self.page = self.ability.page
        self.task_requests = []
        self.monitor_html = ""
        self.ability.browser_context.route("**/*", self.serve)

    def serve(self, route):
        if route.request.url in (
            self.ability.get_transfer_url(),
            self.ability.get_ingest_url(),
        ):
            route.fulfill(content_type="text/html", body=self.monitor_html)
        elif route.request.url == self.ability.get_tasks_url(JOB_UUID):
            self.task_requests.append(route.request.url)
            route.fulfill(
                content_type="text/html",
                body=f"""
                <article class="task">
                  <div class="task-heading"><h4>Task {TASK_UUID}</h4></div>
                  <h3 class="panel-title panel-title-simple">policy_check.py</h3>
                  <div class="panel-primary"><div class="shell-output">
                    <pre>"input.mkv"</pre>
                  </div></div>
                  <div class="panel-info"><pre>All policy checks passed:</pre></div>
                  <div class="row"><dl><dt>Exit Code</dt><dd>0</dd></dl></div>
                </article>
                """,
            )
        else:
            route.fulfill(status=404, body="Not found")

    def set_monitor(
        self,
        *,
        job_uuid=JOB_UUID,
        layout="expanded",
        broken=False,
        hidden_name=False,
        hidden_status=False,
    ):
        name_style = 'style="display:none"' if hidden_name else ""
        status_style = 'style="display:none"' if hidden_status else ""
        job = f"""
        <div class="job">
          <div class="job-detail-microservice">
            <span title="{escape(job_uuid, quote=True)}" {name_style}>
              {MICROSERVICE}
            </span>
          </div>
          <div class="job-detail-currentstep">
            <span {status_style}>Completed successfully</span>
          </div>
        </div>
        """
        container_class = "" if layout == "legacy" else 'class="job-container"'
        container_style = "" if layout == "expanded" else 'style="display:none"'
        container = f"<div {container_class} {container_style}>{job}</div>"
        expand = "this.nextElementSibling.style.display = 'block'"
        if layout == "lazy":
            container = f'<template><div class="job-container">{job}</div></template>'
            expand = """
            const template = this.nextElementSibling;
            setTimeout(() => template.replaceWith(template.content.cloneNode(true)), 50)
            """
        elif layout == "expanded":
            expand = "this.nextElementSibling.style.display = 'none'"
        if broken:
            expand = ""
        self.monitor_html = f"""
        <div class="sip sip-expanded">
          <div id="sip-row-{TRANSFER_UUID}"></div>
          <div class="microservicegroup">
            <div class="microservice-group"
              onclick="window.expansionAttempts += 1;
                window.lastClickTrusted = event.isTrusted; {expand}">
              <span class="microservice-group-name">Microservice: {GROUP}</span>
            </div>
            {container}
          </div>
        </div>
        <script>window.expansionAttempts = 0</script>
        """

    def set_decision_monitor(
        self,
        name,
        *,
        review=False,
        status="Awaiting decision",
        options=None,
        select_attrs="",
        hidden_name=False,
    ):
        _, group = utils.micro_service2group(name)
        self.set_monitor(hidden_name=hidden_name)
        label = escape(name)
        if review:
            # Actual Vue output has three spaces before the inline Review link.
            label += '   <a href="/review/" target="_blank">Review</a>'
        self.monitor_html = self.monitor_html.replace(MICROSERVICE, label)
        self.monitor_html = self.monitor_html.replace(
            f"Microservice: {GROUP}", f"Microservice: {escape(group)}"
        ).replace("Completed successfully", status)
        if options is None:
            options = '<option value="yes"> - Yes</option>'
        self.monitor_html = self.monitor_html.replace(
            '<div class="job-detail-currentstep">',
            f"""<div class="job-detail-actions">
              <select {select_attrs} onchange="window.selectedChoice = this.value">
                <option value="">Actions</option>{options}
              </select>
            </div><div class="job-detail-currentstep">""",
        )

    def test_approval_steps_with_vue_review_links(self):
        for name in ("Approve normalization", "Store AIP"):
            for requested in (name, name + " (review)"):
                with self.subTest(name=name, requested=requested):
                    self.set_decision_monitor(name, review=True)

                    result = self.ability.await_decision_point(
                        requested, TRANSFER_UUID, unit_type="sip"
                    )
                    self.assertEqual(result, (JOB_UUID, "Awaiting decision"))
                    self.ability.make_choice(
                        "Yes", requested, TRANSFER_UUID, unit_type="sip"
                    )
                    self.assertEqual(self.page.evaluate("window.selectedChoice"), "yes")

    def test_each_review_decision_option(self):
        for name, labels in (
            ("Approve normalization", ("Yes", "Redo", "Reject")),
            ("Store AIP", ("Yes", "Reject AIP")),
        ):
            options = "".join(
                f'<option value="{index}"> - {label}</option>'
                for index, label in enumerate(labels)
            )
            for index, label in enumerate(labels):
                with self.subTest(name=name, choice=label):
                    self.set_decision_monitor(name, review=True, options=options)
                    self.ability.make_choice(
                        label, name, TRANSFER_UUID, unit_type="sip"
                    )
                    self.assertEqual(
                        self.page.evaluate("window.selectedChoice"), str(index)
                    )

    def test_review_link_does_not_make_a_hidden_job_acceptable(self):
        for name in ("Approve normalization", "Store AIP"):
            with self.subTest(name=name):
                self.set_decision_monitor(name, review=True, hidden_name=True)
                with self.assertRaises(ArchivematicaBrowserTransferIngestAbilityError):
                    self.ability.await_decision_point(
                        name, TRANSFER_UUID, unit_type="sip"
                    )

    def test_other_suite_decisions(self):
        decisions = (
            ("Approve standard transfer", "Approve transfer", "transfer"),
            ("Approve AIP reingest", "Approve AIP reingest", "sip"),
            ("Create SIP(s)", "Create single SIP and continue processing", "transfer"),
            ("Normalize", "Normalize for preservation", "sip"),
            ("Assign UUIDs to directories?", "No", "transfer"),
            ("Do you want to perform file format identification?", "Yes", "transfer"),
            ("Perform policy checks on originals?", "No", "transfer"),
            ("Perform policy checks on preservation derivatives?", "No", "sip"),
            ("Perform policy checks on access derivatives?", "No", "sip"),
            ("Bind PIDs?", "No", "sip"),
            ("Document empty directories?", "No", "sip"),
            ("Reminder: add metadata if desired", "Continue", "sip"),
            ("Store AIP location", "Local storage", "sip"),
            ("Upload DIP", "Do not upload DIP", "sip"),
        )
        for name, choice, unit_type in decisions:
            with self.subTest(name=name):
                self.set_decision_monitor(
                    name, options=f'<option value="choice"> - {escape(choice)}</option>'
                )
                result = self.ability.await_decision_point(
                    name, TRANSFER_UUID, unit_type=unit_type
                )
                self.assertEqual(result, (JOB_UUID, "Awaiting decision"))
                self.ability.make_choice(
                    choice, name, TRANSFER_UUID, unit_type=unit_type
                )
                self.assertEqual(self.page.evaluate("window.selectedChoice"), "choice")

    def test_matches_whitespace_without_accepting_different_job_names(self):
        for label in (
            "Approve normalization   Review",
            "Approve\n normalization\t Review",
            "Approve normalization location",
            "Do not Approve normalization Review",
        ):
            with self.subTest(label=label):
                self.set_decision_monitor("Approve normalization")
                self.monitor_html = self.monitor_html.replace(
                    "Approve normalization", label
                )
                self.page.goto(self.ability.get_transfer_url())
                if label in (
                    "Approve normalization location",
                    "Do not Approve normalization Review",
                ):
                    with self.assertRaises(
                        ArchivematicaBrowserTransferIngestAbilityError
                    ):
                        self.ability.wait_for_microservice_visibility(
                            "Approve normalization", "Normalize", TRANSFER_UUID
                        )
                else:
                    self.ability.wait_for_microservice_visibility(
                        "Approve normalization", "Normalize", TRANSFER_UUID
                    )
                group = self.ability.get_transfer_micro_service_group_elem(
                    "Normalize", TRANSFER_UUID
                )
                job, _ = self.ability._job_for_microservice(
                    group, "Approve normalization"
                )
                self.assertEqual(
                    job is not None,
                    label.startswith("Approve") and "location" not in label,
                )

    def test_choice_requires_exact_unambiguous_label(self):
        for options, succeeds in (
            ('<option value="wrong"> - Yes, and do something else</option>', False),
            (
                '<option value="wrong"> - Yes, and do something else</option>'
                '<option value="yes"> - Yes</option>',
                True,
            ),
            (
                '<option value="one"> - Yes</option><option value="two"> - Yes</option>',
                False,
            ),
        ):
            with self.subTest(options=options):
                self.set_decision_monitor(
                    "Approve normalization", review=True, options=options
                )
                if succeeds:
                    self.ability.make_choice(
                        "Yes", "Approve normalization", TRANSFER_UUID
                    )
                    self.assertEqual(self.page.evaluate("window.selectedChoice"), "yes")
                else:
                    with self.assertRaises(
                        ArchivematicaBrowserTransferIngestAbilityError
                    ):
                        self.ability.make_choice(
                            "Yes", "Approve normalization", TRANSFER_UUID
                        )
                    self.assertIsNone(self.page.evaluate("window.selectedChoice"))

    def test_rejects_placeholder_as_choice(self):
        self.set_decision_monitor("Approve normalization")
        with self.assertRaises(ArchivematicaBrowserTransferIngestAbilityError):
            self.ability.make_choice("Actions", "Approve normalization", TRANSFER_UUID)
        self.assertIsNone(self.page.evaluate("window.selectedChoice"))

    def test_cannot_approve_hidden_or_disabled_controls(self):
        for attrs in ('style="display:none"', "disabled"):
            with self.subTest(attrs=attrs):
                self.set_decision_monitor("Approve normalization", select_attrs=attrs)
                with self.assertRaises(PlaywrightTimeoutError):
                    self.ability.make_choice(
                        "Yes", "Approve normalization", TRANSFER_UUID
                    )
                self.assertIsNone(self.page.evaluate("window.selectedChoice"))

    def test_cannot_approve_job_that_is_not_awaiting_decision(self):
        for status in ("Executing commands", "Failed", "Completed successfully"):
            with self.subTest(status=status):
                self.set_decision_monitor("Approve normalization", status=status)
                with self.assertRaises(ArchivematicaBrowserJobsTasksAbilityError):
                    self.ability.make_choice(
                        "Yes", "Approve normalization", TRANSFER_UUID
                    )
                self.assertIsNone(self.page.evaluate("window.selectedChoice"))

    def test_absent_choice_check_never_executes_a_decision(self):
        self.set_decision_monitor("Approve normalization", review=True)
        self.ability.assert_no_option("No", "Approve normalization", TRANSFER_UUID)
        self.assertIsNone(self.page.evaluate("window.selectedChoice"))
        with self.assertRaises(AssertionError):
            self.ability.assert_no_option("Yes", "Approve normalization", TRANSFER_UUID)
        self.assertIsNone(self.page.evaluate("window.selectedChoice"))

    def test_rejects_missing_job_uuid(self):
        for title in ("", " \t "):
            with self.subTest(title=title):
                self.set_monitor(job_uuid=title)

                with self.assertRaisesRegex(
                    ArchivematicaBrowserJobsTasksAbilityError, "Missing job UUID"
                ):
                    self.ability.parse_job(MICROSERVICE, TRANSFER_UUID)

    def test_rejects_cached_job_without_uuid(self):
        for title in ("", " \t "):
            with self.subTest(title=title):
                self.set_monitor(job_uuid=title)
                self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

                with self.assertRaisesRegex(
                    ArchivematicaBrowserJobsTasksAbilityError, "Missing job UUID"
                ):
                    self.ability.parse_job(MICROSERVICE, TRANSFER_UUID)

    def test_rejects_broken_microservice_group_expansion(self):
        for layout in ("legacy", "hidden"):
            with self.subTest(layout=layout):
                self.set_monitor(layout=layout, broken=True)

                with self.assertRaises(PlaywrightTimeoutError):
                    self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

                self.assertFalse(self.page.locator("div.job").is_visible())
                self.assertEqual(self.page.evaluate("window.expansionAttempts"), 1)
                self.assertIsNone(
                    self.ability.recalled_job_result(MICROSERVICE, TRANSFER_UUID)
                )

    def test_rejects_obstructed_microservice_group(self):
        self.set_monitor(layout="hidden")
        self.monitor_html += """
        <div style="position:fixed;inset:0;z-index:10"></div>
        """

        with self.assertRaises(PlaywrightTimeoutError):
            self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

        self.assertEqual(self.page.evaluate("window.expansionAttempts"), 0)
        self.assertFalse(self.page.locator("div.job").is_visible())
        self.assertIsNone(self.ability.recalled_job_result(MICROSERVICE, TRANSFER_UUID))

    def test_clicks_visible_label_when_heading_center_is_covered(self):
        self.set_monitor(layout="hidden")
        self.monitor_html += """
        <style>.microservice-group { width: 900px; height: 30px; }</style>
        <div style="position:fixed;left:400px;right:0;top:0;height:50px;z-index:10">
        </div>
        """

        result = self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

        self.assertEqual(result, (JOB_UUID, "Completed successfully"))
        self.assertTrue(self.page.evaluate("window.lastClickTrusted"))
        self.assertEqual(self.page.evaluate("window.expansionAttempts"), 1)

    def test_expands_hidden_microservice_group(self):
        for layout in ("legacy", "hidden"):
            with self.subTest(layout=layout):
                self.set_monitor(layout=layout)

                result = self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

                self.assertEqual(result, (JOB_UUID, "Completed successfully"))
                self.assertTrue(self.page.locator("div.job").is_visible())
                self.assertEqual(self.page.evaluate("window.expansionAttempts"), 1)
                self.assertTrue(self.page.evaluate("window.lastClickTrusted"))

    def test_expands_lazily_loaded_microservice_group(self):
        self.set_monitor(layout="lazy")

        result = self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

        self.assertEqual(result, (JOB_UUID, "Completed successfully"))
        self.assertTrue(self.page.locator("div.job").is_visible())
        self.assertEqual(self.page.evaluate("window.expansionAttempts"), 1)

    def test_reads_tasks_without_collapsing_visible_group(self):
        self.set_monitor()
        self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

        job = self.ability.parse_job(MICROSERVICE, TRANSFER_UUID)

        self.assertEqual(job["job_output"], "Completed successfully")
        self.assertEqual(set(job["tasks"]), {TASK_UUID})
        self.assertEqual(job["tasks"][TASK_UUID]["stdout"], "All policy checks passed:")
        self.assertEqual(job["tasks"][TASK_UUID]["exit_code"], "0")
        self.assertEqual(self.task_requests, [self.ability.get_tasks_url(JOB_UUID)])
        self.assertEqual(self.page.url, self.ability.get_transfer_url())
        self.assertTrue(self.page.locator("div.job").is_visible())
        self.assertEqual(self.page.evaluate("window.expansionAttempts"), 0)

    def test_rejects_hidden_microservice_name(self):
        self.set_monitor(hidden_name=True)
        self.page.goto(self.ability.get_transfer_url())

        with self.assertRaises(ArchivematicaBrowserTransferIngestAbilityError):
            self.ability.wait_for_microservice_visibility(
                MICROSERVICE, GROUP, TRANSFER_UUID
            )

    def test_rejects_hidden_job_status(self):
        self.set_monitor(hidden_status=True)

        with self.assertRaises(ArchivematicaBrowserJobsTasksAbilityError):
            self.ability.parse_job(MICROSERVICE, TRANSFER_UUID)

        self.assertEqual(self.task_requests, [])
        self.assertEqual(self.ability.get_job_output(MICROSERVICE, TRANSFER_UUID), "")

    def test_rejects_status_hidden_when_job_finishes(self):
        self.set_monitor()
        self.monitor_html = self.monitor_html.replace(
            "Completed successfully", "Executing commands"
        )
        self.monitor_html += """
        <script>
          setTimeout(() => {
            const status = document.querySelector('.job-detail-currentstep span');
            status.hidden = true;
            status.textContent = 'Completed successfully';
          }, 100);
        </script>
        """

        with self.assertRaises(ArchivematicaBrowserJobsTasksAbilityError):
            self.ability.await_job_completion(MICROSERVICE, TRANSFER_UUID)

        self.assertIsNone(self.ability.recalled_job_result(MICROSERVICE, TRANSFER_UUID))


class ChromeJobTests(BrowserJobChecks, unittest.TestCase):
    browser_name = "Chrome"


class FirefoxJobTests(BrowserJobChecks, unittest.TestCase):
    browser_name = "Firefox"


if __name__ == "__main__":
    unittest.main()
