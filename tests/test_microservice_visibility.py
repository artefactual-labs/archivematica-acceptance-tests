"""Check the visibility timeout budget and reported errors."""

import unittest
from unittest import mock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from amuser import am_browser_transfer_ingest_ability


class TestMicroserviceVisibilityTimeout(unittest.TestCase):
    def make_ability(self, max_attempts=2):
        ability = am_browser_transfer_ingest_ability.ArchivematicaBrowserTransferIngestAbility(
            max_check_for_ms_visibility_attempts=max_attempts,
            micro_wait=1,
            quick_wait=2,
        )
        ability._transfer_microservice_group_locator = mock.Mock()
        group = ability._transfer_microservice_group_locator.return_value
        return ability, group.locator.return_value.filter.return_value.first

    def test_passes_a_bounded_timeout_to_playwright(self):
        for attempts, timeout in ((1, 1), (2, 1000), (4, 4000)):
            with self.subTest(attempts=attempts):
                ability, name = self.make_ability(max_attempts=attempts)

                ability.wait_for_microservice_visibility(
                    "Expected microservice", "Group", "transfer-uuid"
                )

                name.wait_for.assert_called_once_with(state="visible", timeout=timeout)

    def test_raises_after_configured_attempts(self):
        ability, name = self.make_ability()
        error = PlaywrightTimeoutError("Timed out")
        name.wait_for.side_effect = error

        with self.assertRaisesRegex(
            am_browser_transfer_ingest_ability.ArchivematicaBrowserTransferIngestAbilityError,
            '"Missing microservice" in group "Group" for transfer-uuid after 2 attempts',
        ) as raised:
            ability.wait_for_microservice_visibility(
                "Missing microservice", "Group", "transfer-uuid"
            )

        self.assertIs(raised.exception.__cause__, error)


if __name__ == "__main__":
    unittest.main()
