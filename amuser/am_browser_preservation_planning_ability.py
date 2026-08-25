"""Archivematica Browser Preservation Planning Ability."""

import logging

from . import playwright_ability

logger = logging.getLogger("amuser.preservationplanning")


class ArchivematicaBrowserPreservationPlanningAbility(
    playwright_ability.ArchivematicaPlaywrightAbility
):
    """Manage Archivematica format policy rules through the browser."""

    FPR_LAYOUT_SELECTORS = {
        "search_input": {
            "vue": '.fpr-table-app .fpr-toolbar-search input[type="search"]',
            "legacy": "#DataTables_Table_0_filter input",
        },
        "table": {
            "vue": ".fpr-table-app table",
            "legacy": "#DataTables_Table_0",
        },
        "info": {
            "vue": ".fpr-pagination-info",
            "legacy": "#DataTables_Table_0_info",
        },
        "no_matches_alert": {"vue": ".fpr-table-app .alert-info"},
    }

    def navigate_to_preservation_planning(self):
        self.navigate(self.get_preservation_planning_url())

    def navigate_to_normalization_rules(self):
        self.navigate(self.get_normalization_rules_url())

    @classmethod
    def _ordered_selectors(cls, key):
        selector_group = cls.FPR_LAYOUT_SELECTORS[key]
        return [
            selector_group[layout]
            for layout in ("vue", "legacy")
            if layout in selector_group
        ]

    def _first_present_locator(self, key):
        for selector in self._ordered_selectors(key):
            locator = self.page.locator(selector)
            if locator.count():
                return locator.first
        return None

    def _find_fpr_search_input(self):
        return self._first_present_locator("search_input")

    def _find_fpr_table(self):
        return self._first_present_locator("table")

    def _find_fpr_info(self):
        return self._first_present_locator("info")

    def _fpr_search_has_no_matches(self):
        selector = self.FPR_LAYOUT_SELECTORS["no_matches_alert"]["vue"]
        if self.page.locator(selector).count():
            return True
        info = self._find_fpr_info()
        return bool(
            info and info.inner_text().strip().startswith("Showing 0 to 0 of 0 entries")
        )

    def _wait_for_fpr_search_results(self, search_term):
        if self.page.locator(self.FPR_LAYOUT_SELECTORS["table"]["vue"]).count():
            self.wait_for_table_filter(
                self.FPR_LAYOUT_SELECTORS["table"]["vue"],
                search_term,
                self.FPR_LAYOUT_SELECTORS["no_matches_alert"]["vue"],
            )
            return
        self.wait_for_table_filter(
            self.FPR_LAYOUT_SELECTORS["table"]["legacy"], search_term
        )

    def search_rules(self, search_term):
        search_input = self._find_fpr_search_input()
        if not search_input:
            raise AssertionError("Unable to find FPR search input")
        search_input.fill(search_term)
        self._wait_for_fpr_search_results(search_term)

    def click_first_rule_replace_link(self):
        """Click the first visible Replace link in the FPR rules table."""
        table = self._find_fpr_table()
        if table:
            replace_link = table.get_by_role("link", name="Replace", exact=True)
            if replace_link.count():
                replace_link.first.click()
                return
        raise AssertionError('Unable to find a "Replace" link in the FPR rules table')

    def wait_for_rule_edit_interface(self):
        self.wait_for_presence("input[type=submit]")

    def set_fpr_command(self, command_name):
        self.page.locator("#id_f-command").select_option(label=command_name)

    def save_fpr_command(self):
        self.page.locator("input[type=submit]").click()
        self.wait_for_presence(".fpr-table-app, #DataTables_Table_0")

    def change_normalization_rule_command(self, search_term, command_name):
        """Change the command used by the uniquely matching FPR rule."""
        self.navigate_to_normalization_rules()
        self.search_rules(search_term)
        self.click_first_rule_replace_link()
        self.wait_for_rule_edit_interface()
        self.set_fpr_command(command_name)
        self.save_fpr_command()

    def navigate_to_first_policy_check_validation_command(self):
        """Open a policy-check command and return all matching descriptions."""
        policy_command_url = None
        descriptions = []
        commands_table = self._find_fpr_table()
        if not commands_table:
            return descriptions
        for row in commands_table.locator("tbody tr").all():
            anchor = row.locator("a")
            if not anchor.count():
                continue
            description = anchor.first.inner_text().strip()
            if description.startswith("Check against policy "):
                policy_command_url = anchor.first.evaluate("link => link.href")
                descriptions.append(description)
        if policy_command_url:
            self.navigate(policy_command_url)
        return descriptions

    def ensure_fpr_policy_check_command(self, policy_file, policy_path):
        """Ensure a MediaConch validation command exists for a policy file."""
        logger.info("Ensuring an FPR validation command checks policy %s", policy_file)
        self.navigate(self.get_validation_commands_url())
        descriptions = self.navigate_to_first_policy_check_validation_command()
        description = self.get_policy_command_description(policy_file)
        if description in descriptions:
            return
        command = self.get_policy_command(policy_file, policy_path)
        self.save_policy_check_command(command, description)

    def get_policy_command(self, policy_file, policy_path):
        """Adapt the open MediaConch command to use a new policy file."""
        policy_command = None
        for term in self.page.locator("dl dt").all():
            if term.inner_text().strip() == "Command":
                policy_command = (
                    term.locator("xpath=following-sibling::dd[1]//pre")
                    .inner_text()
                    .strip()
                )
                break
        if policy_command is None:
            raise AssertionError("Unable to find the policy command body")
        with open(policy_path) as policy_input:
            policy_lines = policy_input.read().splitlines()
        lines = []
        for line in policy_command.splitlines():
            if line.strip().startswith('POLICY = """'):
                lines.append(line)
                lines.extend(policy_lines)
            elif line.strip() == "POLICY_NAME = ''":
                lines.append(f"POLICY_NAME = '{policy_file}'")
            else:
                lines.append(line)
        return "\n".join(lines)

    def save_policy_check_command(self, policy_command, description):
        """Create and save an FPR policy-check command."""
        self.navigate(self.get_create_command_url())
        tools = self.page.locator("#id_tool")
        for option in tools.locator("option").all():
            label = option.inner_text()
            if "MediaConch" in label:
                tools.select_option(label=label)
                break
        self.page.locator("#id_description").fill(description)
        self.page.locator("#id_command").fill(policy_command)
        self.page.locator("#id_script_type").select_option(value="pythonScript")
        self.page.locator("#id_command_usage").select_option(label="Validation")
        self.page.locator("input[type=submit]").click()

    def ensure_fpr_rule(self, purpose, format_, command_description):
        """Create an FPR rule unless an equivalent rule already exists."""
        if self.fpr_rule_already_exists(purpose, format_, command_description):
            return
        self.navigate(self.get_create_rule_url())
        self.page.locator("#id_f-purpose").select_option(label=purpose)
        self.page.locator("#id_f-format").select_option(label=format_)
        self.page.locator("#id_f-command").select_option(label=command_description)
        self.page.locator("input[type=submit]").click()

    def fpr_rule_already_exists(self, purpose, format_, command_description):
        """Return whether an equivalent FPR rule exists."""
        self.navigate(self.get_rules_url())
        self.search_for_fpr_rule(purpose, format_, command_description)
        return not self._fpr_search_has_no_matches()

    def search_for_fpr_rule(self, purpose, format_, command_description):
        """Search for an FPR rule using the asynchronous table filter."""
        terse_format = format_.split(":")[2].strip()
        self.search_rules(f'"{purpose}" "{terse_format}" "{command_description}"')

    def ensure_fpr_rule_enabled(self, purpose, format_, command_description):
        self.navigate(self.get_rules_url())
        self.search_for_fpr_rule(purpose, format_, command_description)
        if self._fpr_search_has_no_matches():
            return
        table = self._find_fpr_table()
        disabled_rules = [
            row
            for row in table.locator("tbody tr").all()
            if row.locator("td:nth-child(5)").inner_text() == "No"
        ]
        if not disabled_rules:
            logger.info("The matching FPR rule is already enabled")
            return
        assert len(disabled_rules) == 1, (
            f'Expected one disabled FPR rule for "{purpose}" / "{format_}" / '
            f'"{command_description}", found {len(disabled_rules)}'
        )
        disabled_rules[0].locator("td:nth-child(6) a").nth(2).click()
        enable = self.page.locator('input[value="Enable"]')
        enable.wait_for(state="visible")
        enable.click()

    @staticmethod
    def get_policy_command_description(policy_file):
        return f"Check against policy {policy_file} using MediaConch"
