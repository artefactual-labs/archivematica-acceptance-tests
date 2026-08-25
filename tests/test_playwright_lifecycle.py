"""Check browser resource ownership and scenario cleanup."""

import unittest
from types import SimpleNamespace
from unittest import mock

from amuser.playwright_ability import ArchivematicaPlaywrightRuntime
from features.environment import after_scenario

NORMALIZATION_SCENARIO = (
    "Isla wants to confirm that normalization to .mkv for access is successful"
)


class FakeBrowser:
    def __init__(self):
        self.page = "failure-page"
        self.browser_context = object()
        self.events = []

    def capture_failure_artifacts(self, artifact_name):
        self.events.append(("artifacts", artifact_name, self.page))

    def change_normalization_rule_command(self, *args):
        self.events.append(("restore", *args))
        self.page = "cleanup-page"

    def set_default_aip_storage_replicators(self, values):
        self.events.append(("replicators", values))

    def tear_down(self):
        self.events.append(("tear_down",))
        self.page = None
        self.browser_context = None


def make_context(browser):
    return SimpleNamespace(
        am_user=SimpleNamespace(
            browser=browser,
            api=mock.Mock(),
            docker=mock.Mock(),
        ),
        current_transfer={},
    )


def make_scenario(name="Example scenario", status="passed"):
    return SimpleNamespace(
        name=name,
        status=SimpleNamespace(name=status),
        previous_default_aip_storage_replicators=None,
    )


class AfterScenarioTests(unittest.TestCase):
    def test_captures_errors_before_browser_restoration(self):
        browser = FakeBrowser()

        after_scenario(
            make_context(browser),
            make_scenario(name=NORMALIZATION_SCENARIO, status="error"),
        )

        self.assertEqual(
            browser.events,
            [
                ("artifacts", NORMALIZATION_SCENARIO, "failure-page"),
                (
                    "restore",
                    "Access Generic MOV",
                    "Transcoding to mp4 with ffmpeg",
                ),
                ("tear_down",),
            ],
        )

    def test_tears_down_when_restoration_fails(self):
        browser = FakeBrowser()
        browser.change_normalization_rule_command = mock.Mock(
            side_effect=RuntimeError("cleanup failed")
        )

        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            after_scenario(
                make_context(browser),
                make_scenario(name=NORMALIZATION_SCENARIO),
            )

        self.assertEqual(
            browser.events,
            [
                (
                    "artifacts",
                    f"{NORMALIZATION_SCENARIO}-cleanup",
                    "failure-page",
                ),
                ("tear_down",),
            ],
        )

    def test_does_not_retain_artifacts_for_successful_statuses(self):
        for status in ("passed", "skipped", "xfailed"):
            with self.subTest(status=status):
                browser = FakeBrowser()

                after_scenario(make_context(browser), make_scenario(status=status))

                self.assertEqual(browser.events, [("tear_down",)])


class PlaywrightRuntimeTests(unittest.TestCase):
    @mock.patch("amuser.playwright_ability.sync_playwright")
    def test_stops_partially_started_runtime_after_launch_error(self, playwright):
        manager = playwright.return_value
        playwright_instance = manager.start.return_value
        playwright_instance.firefox.launch.side_effect = RuntimeError("launch failed")
        runtime = ArchivematicaPlaywrightRuntime("Firefox", None, "/tmp/project")

        with self.assertRaisesRegex(RuntimeError, "launch failed"):
            runtime.start()

        playwright_instance.stop.assert_called_once_with()
        self.assertIsNone(runtime.playwright)
        self.assertIsNone(runtime.browser)

    @mock.patch("amuser.playwright_ability.sync_playwright")
    def test_reuses_a_connected_browser(self, playwright):
        runtime = ArchivematicaPlaywrightRuntime("Firefox", None, "/tmp/project")
        instance = mock.Mock()
        browser = mock.Mock()
        browser.is_connected.return_value = True
        runtime.playwright = instance
        runtime.browser = browser

        runtime.start()

        self.assertIs(runtime.playwright, instance)
        self.assertIs(runtime.browser, browser)
        playwright.assert_not_called()
        instance.stop.assert_not_called()
        browser.close.assert_not_called()


if __name__ == "__main__":
    unittest.main()
