"""Check navigation and METS reading in the Vue AIP browser."""

import unittest
from html import escape
from unittest import mock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from amuser.am_browser_ability import ArchivematicaBrowserAbility
from amuser.am_browser_ingest_ability import ArchivematicaBrowserMETSAbilityError

SIP_UUID = "00000000-0000-0000-0000-000000000001"
TRANSFER_NAME = "sample [1]'s files"
METS_NAME = f"METS.{SIP_UUID}.xml"
AIP_NAME = f"{TRANSFER_NAME}-{SIP_UUID}"
METS_PATH = f"storeAIP/{AIP_NAME}/{METS_NAME}"
METS_XML = '<mets xmlns="http://www.loc.gov/METS/"><metsHdr/></mets>'


def vue_node(name, children=None):
    attributes = 'aria-expanded="false"' if children is not None else ""
    group = f'<ul role="group" hidden>{children}</ul>' if children is not None else ""
    return f"""
        <li role="treeitem" {attributes}>
          <div class="tree-node-content">
            <span class="tree-node-label">{escape(name)}</span>
          </div>
          {group}
        </li>
    """


def vue_fixture():
    # A duplicate filename in a sibling AIP must not satisfy the requested path.
    directories = vue_node("another-aip", vue_node(METS_NAME))
    directories += vue_node(AIP_NAME, vue_node(METS_NAME))
    return f"""
        <div id="aip-browser">
          <ul role="tree">{vue_node("storeAIP", directories)}</ul>
        </div>
        <script>
          window.fileClicks = [];
          document.querySelectorAll('.tree-node-label').forEach(label => {{
            label.onclick = event => {{
              const item = label.parentElement.parentElement;
              const group = item.querySelector(':scope > [role="group"]');
              if (group) {{
                group.hidden = !group.hidden;
                item.setAttribute('aria-expanded', String(!group.hidden));
              }} else {{
                window.fileClicks.push({{name: label.textContent, trusted: event.isTrusted}});
                window.open('/filesystem/download_fs/?filepath=mets', '_blank', 'noopener');
              }}
            }};
          }});
        </script>
    """


class AIPBrowserChecks:
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
            medium_wait=0.5,
            nihilistic_wait=0.5,
            apathetic_wait=2,
        )
        self.addCleanup(self.ability.tear_down)
        self.ability.set_up()
        self.page = self.ability.page
        self.markup = vue_fixture()
        self.mets_status = 200
        self.ability.browser_context.route("**/*", self.serve)

    def serve(self, route):
        if "/filesystem/download_fs/" in route.request.url:
            route.fulfill(
                status=self.mets_status, content_type="application/xml", body=METS_XML
            )
        else:
            route.fulfill(content_type="text/html", body=self.markup)

    def test_reads_mets(self):
        with mock.patch.object(self.ability, "expose_job"):
            mets = self.ability.get_mets(TRANSFER_NAME, SIP_UUID)

        self.assertEqual(mets.tag, "{http://www.loc.gov/METS/}mets")
        self.assertEqual(len(mets), 1)
        self.assertEqual(len(self.ability.browser_context.pages), 1)

    def test_returns_raw_xml_without_the_browser_viewer(self):
        with mock.patch.object(self.ability, "expose_job"):
            mets = self.ability.get_mets(TRANSFER_NAME, SIP_UUID, parse_xml=False)

        self.assertEqual(mets, METS_XML)

    def test_rejects_failed_mets_response_and_closes_popup(self):
        self.mets_status = 404
        with mock.patch.object(self.ability, "expose_job"):
            with self.assertRaisesRegex(
                ArchivematicaBrowserMETSAbilityError, "HTTP 404"
            ):
                self.ability.get_mets(TRANSFER_NAME, SIP_UUID)

        self.assertEqual(len(self.ability.browser_context.pages), 1)

    def test_reuses_expanded_vue_directories(self):
        self.page.goto(self.ability.am_url)
        for _ in range(2):
            with self.page.expect_popup() as popup:
                self.ability.navigate_to_aip_directory_and_click(METS_PATH)
            popup.value.close()
        self.assertEqual(
            self.page.evaluate("window.fileClicks"),
            [{"name": METS_NAME, "trusted": True}] * 2,
        )

    def test_missing_vue_file_does_not_match_another_aip(self):
        self.page.goto(self.ability.am_url)
        self.page.get_by_text(METS_NAME, exact=True).last.evaluate("el => el.remove()")
        self.page.get_by_text("storeAIP", exact=True).click()
        self.page.get_by_text("another-aip", exact=True).click()
        self.assertTrue(self.page.get_by_text(METS_NAME, exact=True).is_visible())

        with self.assertRaises(PlaywrightTimeoutError):
            self.ability.navigate_to_aip_directory_and_click(METS_PATH)

        self.assertEqual(self.page.evaluate("window.fileClicks"), [])

    def test_rejects_broken_directory_control(self):
        self.page.goto(self.ability.am_url)
        self.page.get_by_text("storeAIP", exact=True).evaluate(
            "el => el.onclick = null"
        )

        with self.assertRaises(AssertionError):
            self.ability.navigate_to_aip_directory_and_click(METS_PATH)
        self.assertEqual(self.page.evaluate("window.fileClicks"), [])


class ChromeAIPBrowserTests(AIPBrowserChecks, unittest.TestCase):
    browser_name = "Chrome"


class FirefoxAIPBrowserTests(AIPBrowserChecks, unittest.TestCase):
    browser_name = "Firefox"


if __name__ == "__main__":
    unittest.main()
