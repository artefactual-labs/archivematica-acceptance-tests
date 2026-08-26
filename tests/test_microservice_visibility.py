import unittest
from unittest import mock

from amuser import am_browser_transfer_ingest_ability


class TestMicroserviceVisibilityPolling(unittest.TestCase):
    def test_returns_when_microservice_becomes_visible(self):
        ability = mock.Mock(
            max_check_for_ms_visibility_attempts=2,
            micro_wait=1,
            quick_wait=2,
        )
        missing_group = mock.Mock()
        missing_group.find_elements.return_value = []
        span = mock.Mock(text="Expected microservice")
        job = mock.Mock()
        job.find_elements.return_value = [span]
        visible_group = mock.Mock()
        visible_group.find_elements.return_value = [job]
        ability.get_transfer_micro_service_group_elem.side_effect = (
            missing_group,
            visible_group,
        )

        with mock.patch.object(
            am_browser_transfer_ingest_ability.time, "sleep"
        ) as sleep:
            am_browser_transfer_ingest_ability.ArchivematicaBrowserTransferIngestAbility.wait_for_microservice_visibility(
                ability,
                "Expected microservice",
                "Group",
                "transfer-uuid",
            )

        sleep.assert_called_once_with(1)

    def test_raises_after_configured_attempts(self):
        ability = mock.Mock(
            max_check_for_ms_visibility_attempts=2,
            micro_wait=1,
            quick_wait=2,
        )
        missing_group = mock.Mock()
        missing_group.find_elements.return_value = []
        ability.get_transfer_micro_service_group_elem.return_value = missing_group

        with (
            mock.patch.object(
                am_browser_transfer_ingest_ability.time, "sleep"
            ) as sleep,
            self.assertRaisesRegex(
                am_browser_transfer_ingest_ability.ArchivematicaBrowserTransferIngestAbilityError,
                "after 2 attempts",
            ),
        ):
            am_browser_transfer_ingest_ability.ArchivematicaBrowserTransferIngestAbility.wait_for_microservice_visibility(
                ability,
                "Missing microservice",
                "Group",
                "transfer-uuid",
            )

        sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
