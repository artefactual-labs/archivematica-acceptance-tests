import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

FEATURES_PATH = Path(__file__).parents[1] / "features"
sys.path.insert(0, str(FEATURES_PATH))

from amuser.playwright_ability import ArchivematicaPlaywrightAbility  # noqa: E402
from amuser.playwright_ability import ArchivematicaPlaywrightRuntime  # noqa: E402
from features.environment import after_scenario  # noqa: E402

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

    def test_reuses_a_connected_browser(self):
        runtime = ArchivematicaPlaywrightRuntime("Firefox", None, "/tmp/project")
        runtime.playwright = mock.Mock()
        runtime.browser = mock.Mock()
        runtime.browser.is_connected.return_value = True

        runtime.start()

        runtime.browser.close.assert_not_called()


class CompatibleLayoutTests(unittest.TestCase):
    def test_waits_for_a_supported_layout_before_selecting_one(self):
        ability = ArchivematicaPlaywrightAbility()
        ability.page = mock.Mock()
        combined = mock.Mock()
        vue = mock.Mock()
        legacy = mock.Mock()
        vue.count.return_value = 0
        legacy.count.return_value = 1
        ability.page.locator.side_effect = {
            ".vue, .legacy": combined,
            ".vue": vue,
            ".legacy": legacy,
        }.get

        result = ability.first_present_locator((".vue", ".legacy"))

        combined.first.wait_for.assert_called_once_with(
            state="attached",
            timeout=ability._milliseconds(ability.pessimistic_wait),
        )
        self.assertIs(result, legacy.first)


class TableFilterTests(unittest.TestCase):
    def test_checks_an_empty_result_before_requiring_the_table(self):
        ability = ArchivematicaPlaywrightAbility()
        ability.page = mock.Mock()

        ability.wait_for_table_filter(
            ".results", '"first token" second', ".empty-results"
        )

        predicate = ability.page.wait_for_function.call_args.args[0]
        self.assertLess(
            predicate.index("const empty"),
            predicate.index("const table"),
        )
        self.assertEqual(
            ability.page.wait_for_function.call_args.kwargs["arg"],
            {
                "tableSelector": ".results",
                "emptySelector": ".empty-results",
                "tokens": ["first token", "second"],
            },
        )


if __name__ == "__main__":
    unittest.main()
