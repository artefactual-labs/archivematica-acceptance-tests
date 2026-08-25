"""Check transfer setup through the Vue file browser."""

import unittest
from html import escape
from unittest import mock

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from amuser.am_browser_ability import ArchivematicaBrowserAbility

FOLDER = "sample [1]'s files"
TRANSFER_PATH = f"parent/{FOLDER}"


def node(name, path, children=None):
    attrs = 'aria-expanded="false"' if children is not None else ""
    group = f'<ul role="group" hidden>{children}</ul>' if children is not None else ""
    return f"""
      <li role="treeitem" aria-selected="false" {attrs} data-path="{escape(path)}">
        <div class="tree-node-content">
          <span class="tree-node-label">
            <span class="transfer-node-name">{escape(name)}</span>
            <span class="tree-node-display">(display details)</span>
          </span>
        </div>
        {group}
      </li>
    """


def fixture():
    children = node(FOLDER, TRANSFER_PATH, "")
    children += node(FOLDER + " extra", TRANSFER_PATH + " extra", "")
    children += node("bag.zip", "parent/bag.zip")
    return f"""
      <div id="transfer-browser">
        <div id="transfer-browser-form">
          <input id="transfer-name"><input id="transfer-accession">
          <select id="transfer-type">
            <option>Standard</option><option>Zipped bag</option>
          </select>
          <button class="btn-browse" onclick="document.querySelector('#file-browser').hidden = false">Browse</button>
          <button class="btn-success" onclick="window.started = event.isTrusted">Start transfer</button>
          <button class="btn-success dropdown-toggle" onclick="throw new Error('Wrong button')">Options</button>
        </div>
        <div class="path-container"></div>
        <section id="file-browser" hidden>
          <ul role="tree">{node("parent", "parent", children)}</ul>
          <button class="transfer-tree-add-btn" disabled>Add</button>
        </section>
      </div>
      <script>
        window.selectedPath = null;
        document.querySelectorAll('.transfer-node-name').forEach(label => {{
          label.onclick = event => {{
            const item = label.closest('[role="treeitem"]');
            document.querySelectorAll('[role="treeitem"]').forEach(node => node.setAttribute('aria-selected', 'false'));
            item.setAttribute('aria-selected', 'true');
            window.selectedPath = item.dataset.path;
            document.querySelector('.transfer-tree-add-btn').disabled = false;
            const group = item.querySelector(':scope > [role="group"]');
            if (group) {{
              const expanded = item.getAttribute('aria-expanded') !== 'true';
              item.setAttribute('aria-expanded', String(expanded));
              setTimeout(() => group.hidden = !expanded, 50);
            }}
          }};
        }});
        document.querySelector('.transfer-tree-add-btn').onclick = event => {{
          if (!event.isTrusted) throw new Error('Untrusted click');
          const entry = document.createElement('span');
          entry.className = 'path';
          entry.textContent = '/source/' + window.selectedPath;
          document.querySelector('.path-container').append(entry);
        }};
      </script>
    """


class TransferBrowserChecks:
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
            am_version="1.18",
            pessimistic_wait=0.5,
            medium_wait=0.5,
        )
        self.addCleanup(self.ability.tear_down)
        self.ability.set_up()
        self.page = self.ability.page
        self.page.set_content(fixture())

    def test_configures_transfer_and_adds_exact_folder(self):
        self.ability.set_transfer_type("Standard")
        self.ability.enter_transfer_name("Browser test")
        self.ability.enter_accession_no("ACC-1")
        self.ability.add_transfer_directory(TRANSFER_PATH)
        self.ability.click_start_transfer_button()

        self.assertEqual(
            self.page.locator("#transfer-name").input_value(), "Browser test"
        )
        self.assertEqual(
            self.page.locator("#transfer-accession").input_value(), "ACC-1"
        )
        self.assertEqual(
            self.page.locator(".path").inner_text(), "/source/" + TRANSFER_PATH
        )
        self.assertTrue(self.page.evaluate("window.started"))

    def test_adds_compressed_file(self):
        self.ability.set_transfer_type("Zipped bag")
        self.ability.add_transfer_directory("parent/bag.zip")

        self.assertEqual(
            self.page.locator(".path").inner_text(), "/source/parent/bag.zip"
        )

    def test_reuses_expanded_parent(self):
        self.ability.add_transfer_directory(TRANSFER_PATH)
        self.ability.add_transfer_directory(TRANSFER_PATH + " extra")

        self.assertEqual(self.page.locator(".path").count(), 2)

    def test_rejects_missing_folder_with_similar_name(self):
        self.page.get_by_text(FOLDER, exact=True).evaluate("el => el.remove()")
        with self.assertRaises(PlaywrightTimeoutError):
            self.ability.add_transfer_directory(TRANSFER_PATH)
        self.assertEqual(self.page.locator(".path").count(), 0)

    def test_rejects_broken_add_button(self):
        self.page.locator(".transfer-tree-add-btn").evaluate("el => el.onclick = null")
        with self.assertRaises(AssertionError):
            self.ability.add_transfer_directory(TRANSFER_PATH)
        self.assertEqual(self.page.locator(".path").count(), 0)


class ChromeTransferBrowserTests(TransferBrowserChecks, unittest.TestCase):
    browser_name = "Chrome"


class FirefoxTransferBrowserTests(TransferBrowserChecks, unittest.TestCase):
    browser_name = "Firefox"


if __name__ == "__main__":
    unittest.main()
