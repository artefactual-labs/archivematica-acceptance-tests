"""Preserve browser selection for existing AMAUAT callers."""

import unittest

from amuser import ArchivematicaUser
from features.environment import get_am_user


class TestBrowserConfiguration(unittest.TestCase):
    def test_selects_the_requested_browser(self):
        cases = (
            ({}, "Chrome"),
            ({"driver_name": "Firefox"}, "Firefox"),
            ({"browser_name": "Firefox"}, "Firefox"),
            ({"driver_name": "Firefox", "browser_name": "Chrome"}, "Chrome"),
        )
        for factory in (ArchivematicaUser, lambda **kwargs: get_am_user(kwargs)):
            for options, expected in cases:
                with self.subTest(factory=factory, options=options):
                    user = factory(**options)

                    runtime = user.browser.create_playwright_runtime()

                    self.assertEqual(runtime.browser_name, expected)


if __name__ == "__main__":
    unittest.main()
