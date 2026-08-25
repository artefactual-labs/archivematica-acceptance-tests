"""Exercise supported UI layouts without an Archivematica deployment."""

import unittest
from unittest import mock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from amuser.am_browser_ability import ArchivematicaBrowserAbility
from amuser.am_browser_transfer_ability import ArchivematicaBrowserTransferAbilityError

SEARCH_LAYOUTS = ("fpr-vue", "ss-vue", "fpr-legacy", "ss-legacy")


class BrowserLayoutChecks:
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
            apathetic_wait=0.5,
        )
        self.addCleanup(self.ability.tear_down)
        self.ability.set_up()
        self.page = self.ability.page

    def test_waits_for_a_supported_layout_to_appear(self):
        selectors = (".fpr-table-app", "#DataTables_Table_0")
        for markup in (
            '<div class="fpr-table-app">Loaded Vue layout</div>',
            '<table id="DataTables_Table_0"><tr><td>Loaded legacy layout</td></tr></table>',
        ):
            with self.subTest(markup=markup):
                self.page.set_content('<main id="container"></main>')
                self.page.evaluate(
                    """markup => setTimeout(() => {
                      document.querySelector('#container').innerHTML = markup;
                    }, 100)""",
                    markup,
                )

                result = self.ability.first_present_locator(selectors)

                self.assertIsNotNone(result)
                self.assertIn("Loaded", result.inner_text())

    def test_returns_none_when_no_supported_layout_appears(self):
        self.page.set_content('<div class="unrelated">Other page content</div>')

        result = self.ability.first_present_locator(
            (".fpr-table-app", "#DataTables_Table_0")
        )

        self.assertIsNone(result)

    def test_accepts_settled_empty_vue_search_results(self):
        self.page.set_content(
            """
            <div class="fpr-table-app">
              <div class="fpr-toolbar-search"><input type="search"></div>
              <div class="alert alert-info">No results found.</div>
            </div>
            """
        )

        self.ability.search_rules("missing rule")

        self.assertTrue(self.ability._fpr_search_has_no_matches())

    def test_accepts_vue_search_removing_the_results_table(self):
        self.page.set_content(
            """
            <div class="fpr-table-app">
              <div class="fpr-toolbar-search"><input type="search"></div>
              <table><tbody><tr><td>Existing rule</td></tr></tbody></table>
            </div>
            <script>
              document.querySelector('input').oninput = () => setTimeout(() => {
                document.querySelector('table').remove();
                const empty = document.createElement('div');
                empty.className = 'alert alert-info';
                empty.textContent = 'No results found.';
                document.querySelector('.fpr-table-app').append(empty);
              }, 50);
            </script>
            """
        )

        self.ability.search_rules("missing rule")

        self.assertEqual(self.page.locator("table").count(), 0)
        self.assertTrue(self.ability._fpr_search_has_no_matches())

    def test_does_not_accept_missing_vue_results_and_empty_state(self):
        self.page.set_content(
            """
            <div class="fpr-table-app">
              <div class="fpr-toolbar-search"><input type="search"></div>
            </div>
            """
        )

        with self.assertRaises((PlaywrightTimeoutError, AssertionError)):
            self.ability.search_rules("missing rule")

    def test_accepts_legacy_search_results(self):
        self.page.set_content(
            """
            <div id="DataTables_Table_0_filter"><input></div>
            <table id="DataTables_Table_0">
              <tbody><tr><td>Existing rule</td></tr></tbody>
            </table>
            """
        )

        self.ability.search_rules("Existing rule")

        self.assertEqual(self.page.locator("td").inner_text(), "Existing rule")

    def set_search_fixture(self, layout, initial_query):
        if layout == "fpr-vue":
            markup = """
            <div class="fpr-table-app">
              <div class="fpr-toolbar-search"><input type="search"></div>
              <div id="results"></div>
            </div>
            """
        elif layout == "ss-vue":
            markup = '<input class="ss-table-search-input"><div id="results"></div>'
        else:
            markup = """
            <div id="DataTables_Table_0_filter"><input></div>
            <div id="results"></div>
            """
        self.page.set_content(markup)
        self.page.evaluate(
            """({ layout, initialQuery }) => {
              const input = document.querySelector('input');
              const results = document.querySelector('#results');
              const records = ['Existing rule', 'Existing extra rule'];
              const render = (query) => {
                window.appliedQuery = query;
                const matches = records.filter(record => record.includes(query));
                if (!matches.length && layout === 'fpr-vue') {
                  results.innerHTML = '<div class="alert alert-info">No results found.</div>';
                  return;
                }
                const tableAttrs = layout === 'ss-vue'
                  ? 'class="ss-table-grid"' : 'id="DataTables_Table_0"';
                const rows = matches.length
                  ? matches.map(record => `<tr><td class="result">${record}</td></tr>`).join('')
                  : '<tr><td class="ss-table-cell--empty">No matching records found</td></tr>';
                results.innerHTML = `<table ${tableAttrs}><tbody>${rows}</tbody></table>`;
              };
              input.value = initialQuery;
              render(initialQuery);
              let timer;
              input.oninput = () => {
                clearTimeout(timer);
                timer = setTimeout(() => render(input.value), 100);
              };
            }""",
            {"layout": layout, "initialQuery": initial_query},
        )
        if layout.startswith("ss-"):
            return self.ability._search_ss_table
        return self.ability.search_rules

    def test_waits_for_matches_after_an_empty_search(self):
        for layout in SEARCH_LAYOUTS:
            with self.subTest(layout=layout):
                search = self.set_search_fixture(layout, "missing")

                search("Existing rule")

                self.assertEqual(
                    self.page.locator("td.result").all_text_contents(),
                    ["Existing rule"],
                )

    def test_waits_for_a_second_empty_search(self):
        for layout in SEARCH_LAYOUTS:
            with self.subTest(layout=layout):
                search = self.set_search_fixture(layout, "first missing")

                search("second missing")

                self.assertEqual(
                    self.page.evaluate("window.appliedQuery"), "second missing"
                )
                self.assertEqual(self.page.locator("td.result").count(), 0)

    def test_waits_for_all_matches_when_broadening_a_search(self):
        for layout in SEARCH_LAYOUTS:
            with self.subTest(layout=layout):
                search = self.set_search_fixture(layout, "Existing extra rule")

                search("Existing")

                self.assertEqual(
                    self.page.locator("td.result").all_text_contents(),
                    ["Existing rule", "Existing extra rule"],
                )

    def set_cleanup_fixture(self, remove_control=True):
        control = (
            """
        <a class="btn_remove_sip" href="#" onclick="
          event.preventDefault();
          window.pendingRemoval = this.closest('.sip');
          document.querySelector('.monitor-modal').style.display = 'block';
        ">Remove</a>
        """
            if remove_control
            else ""
        )
        markup = f"""
        <title>Archivematica Dashboard - Transfer</title>
        <form id="transfer-browser-form"></form>
        <div class="sip"><div class="sip-row">First transfer {control}</div></div>
        <div class="sip"><div class="sip-row">Second transfer {control}</div></div>
        <div class="monitor-modal monitor-modal-visible" style="display:none">
          <button class="btn btn-primary" onclick="
            window.pendingRemoval.remove();
            this.parentElement.style.display = 'none';
          ">Confirm</button>
        </div>
        """
        self.page.route(
            "**/*", lambda route: route.fulfill(content_type="text/html", body=markup)
        )

    def test_cleanup_rejects_missing_remove_control(self):
        self.set_cleanup_fixture(remove_control=False)
        original_remove = self.ability.remove_top_transfer
        for method in ("remove_all_transfers", "remove_all_ingests"):
            with self.subTest(method=method):
                calls = []

                def bounded_remove(transfer, calls=calls):
                    calls.append(transfer)
                    if len(calls) > 1:
                        self.fail("Cleanup retried the unchanged row without an error")
                    original_remove(transfer)

                with mock.patch.object(
                    self.ability, "remove_top_transfer", bounded_remove
                ):
                    with self.assertRaisesRegex(
                        ArchivematicaBrowserTransferAbilityError, "Remove"
                    ):
                        getattr(self.ability, method)()

                self.assertEqual(len(calls), 1)
                self.assertEqual(self.page.locator("div.sip").count(), 2)

    def test_cleanup_removes_each_unit(self):
        self.set_cleanup_fixture()
        for method in ("remove_all_transfers", "remove_all_ingests"):
            with self.subTest(method=method):
                getattr(self.ability, method)()

                self.assertEqual(self.page.locator("div.sip").count(), 0)


class ChromeLayoutTests(BrowserLayoutChecks, unittest.TestCase):
    browser_name = "Chrome"


class FirefoxLayoutTests(BrowserLayoutChecks, unittest.TestCase):
    browser_name = "Firefox"


if __name__ == "__main__":
    unittest.main()
