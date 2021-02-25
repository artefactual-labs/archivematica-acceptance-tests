"""Archivematica Browser Preservation Planning Ability"""

import logging

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

from . import selenium_ability


logger = logging.getLogger("amuser.preservationplanning")


class ArchivematicaBrowserPreservationPlanningAbility(
    selenium_ability.ArchivematicaSeleniumAbility
):
    """Archivematica Browser Ability: the ability of an Archivematica user to
    use a browser to interact with Archivematica. A class for using Selenium to
    interact with a live Archivematica instance.
    """

    def navigate_to_preservation_planning(self):
        self.navigate(self.get_preservation_planning_url())

    def navigate_to_normalization_rules(self):
        self.navigate(self.get_normalization_rules_url())

    def search_rules(self, search_term):
        search_input_el = self.driver.find_element_by_css_selector(
            "#DataTables_Table_0_filter input"
        )
        search_input_el.send_keys(search_term)

    def click_first_rule_replace_link(self):
        """Click the "replace" link of the first rule in the FPR rules table
        visible on the page.
        """
        for a_el in self.driver.find_elements_by_tag_name("a"):
            if a_el.text.strip() == "Replace":
                a_el.click()
                break

    def wait_for_rule_edit_interface(self):
        self.wait_for_presence("#id_f-purpose")

    def set_fpr_command(self, command_name):
        command_select_el = self.driver.find_element_by_id("id_f-command")
        command_select_el.click()
        Select(command_select_el).select_by_visible_text(command_name)
        command_select_el.send_keys(Keys.RETURN)

    def save_fpr_command(self):
        command_select_el = self.driver.find_element_by_css_selector(
            "input[type=submit]"
        )
        command_select_el.click()
        self.wait_for_presence("#DataTables_Table_0")

    def change_normalization_rule_command(self, search_term, command_name):
        """Edit the FPR normalization rule that uniquely matches
        ``search_term`` so that its command is the one matching
        ``command_name``.
        """
        self.navigate_to_normalization_rules()
        self.search_rules(search_term)
        self.click_first_rule_replace_link()
        self.wait_for_rule_edit_interface()
        self.set_fpr_command(command_name)
        self.save_fpr_command()

    def navigate_to_first_policy_check_validation_command(self):
        """Find the first policy check validation command and navigate to it.
        Assumes that we are at the validation commands URL and that there is at
        least one policy check validation command in this AM. Returns a list of
        existing policy check command descriptions.
        """
        policy_command_url = None
        policy_command_descriptions = []
        commands_table_el = self.driver.find_element_by_id("DataTables_Table_0")
        for row_el in commands_table_el.find_elements_by_tag_name("tr"):
            try:
                anchor_el = row_el.find_element_by_tag_name("a")
            except NoSuchElementException:
                pass
            else:
                if anchor_el.text.strip().startswith("Check against policy "):
                    policy_command_url = anchor_el.get_attribute("href")
                    policy_command_descriptions.append(anchor_el.text.strip())
        if policy_command_url:
            self.navigate(policy_command_url)
            return policy_command_descriptions
        return []

    def ensure_fpr_policy_check_command(self, policy_file, policy_path):
        """Ensure there is an FPR validation command that checks a file against
        the MediaConch policy ``policy_file``.
        """
        logger.info(
            "Ensuring there is an FPR validation command that checks a"
            ' file against the policy file named "%s".',
            policy_file,
        )
        self.navigate(self.get_validation_commands_url())
        existing_policy_command_descriptions = (
            self.navigate_to_first_policy_check_validation_command()
        )
        description = self.get_policy_command_description(policy_file)
        if description in existing_policy_command_descriptions:
            logger.info("The policy command already exists; no need to re-create it.")
            return
        policy_command = self.get_policy_command(policy_file, policy_path)
        logger.info("Creating the policy check FPR command.")
        self.save_policy_check_command(policy_command, description)

    def get_policy_command(self, policy_file, policy_path):
        """Return a string representing a policy check validation command that
        references the policy file ``policy_file``. Assumes that we are
        viewing an existing validation-via-mediaconch-policy command.
        """
        # Get the text of the command.
        policy_command = None
        next_el = False
        for el in self.driver.find_element_by_tag_name(
            "dl"
        ).find_elements_by_css_selector("*"):
            if next_el:
                policy_command = el.find_element_by_tag_name("pre").text.strip()
                break
            if el.text.strip() == "Command":
                next_el = True
        # Insert our policy file name into the command text.
        lines = []
        with open(policy_path) as filei:
            policy_lines = filei.read().splitlines()
        for line in policy_command.splitlines():
            if line.strip().startswith('POLICY = """'):
                lines.append(line)
                lines += policy_lines
            elif line.strip() == "POLICY_NAME = ''":
                lines.append("POLICY_NAME = '{}'".format(policy_file))
            else:
                lines.append(line)
        return "\n".join(lines)

    def save_policy_check_command(self, policy_command, description):
        """Create and save a new FPR command using the string
        ``policy_command``.
        """
        logger.info(
            "Creating an FPR policy check command with description" ' "%s".',
            description,
        )
        self.navigate(self.get_create_command_url())
        for option in self.driver.find_element_by_id(
            "id_tool"
        ).find_elements_by_tag_name("option"):
            if "MediaConch" in option.text:
                option.click()
                break
        self.driver.find_element_by_id("id_description").send_keys(description)
        js_script = 'document.getElementById("id_command").value =' " `{}`;".format(
            policy_command
        )
        self.driver.execute_script(js_script)
        self.driver.find_element_by_id("id_script_type").send_keys("Python")
        self.driver.find_element_by_id("id_command_usage").send_keys("Validation")
        self.driver.find_element_by_css_selector("input[type=submit]").click()
        logger.info("Created the FPR policy check command")

    def ensure_fpr_rule(self, purpose, format_, command_description):
        """Ensure that there is a new FPR rule with the purpose, format and
        command description given in the params.
        Note that the ``format_`` param is assumed to be in the format that the
        /fpr/fprule/create/ expects, i.e., a colon-delimited triple like
        'Audio: Broadcast WAVE: Broadcast WAVE 1'.
        """
        logger.info(
            'Ensuring there is an FPR rule with purpose "%s" that runs'
            ' command "%s" against files with format "%s".',
            purpose,
            command_description,
            format_,
        )
        if self.fpr_rule_already_exists(purpose, format_, command_description):
            logger.info("Such an FPR rule already exists.")
            return
        logger.info("Creating the needed FPR rule.")
        self.navigate(self.get_create_rule_url())
        Select(self.driver.find_element_by_id("id_f-purpose")).select_by_visible_text(
            purpose
        )
        Select(self.driver.find_element_by_id("id_f-format")).select_by_visible_text(
            format_
        )
        Select(self.driver.find_element_by_id("id_f-command")).select_by_visible_text(
            command_description
        )
        self.driver.find_element_by_css_selector("input[type=submit]").click()
        logger.info("Created the needed FPR rule.")

    def fpr_rule_already_exists(self, purpose, format_, command_description):
        """Return ``True`` if an FPR rule already exists with the purpose,
        format and command description given in the params; ``False`` otherwise.
        """
        self.navigate(self.get_rules_url())
        self.search_for_fpr_rule(purpose, format_, command_description)
        info_el = self.driver.find_element_by_id("DataTables_Table_0_info")
        if info_el.text.strip().startswith("Showing 0 to 0 of 0 entries"):
            return False
        return True

    def search_for_fpr_rule(self, purpose, format_, command_description):
        """Search for an FPR rule with the supplied purpose, format and command
        description. Uses the FPR asynchronous search input.
        """
        terse_format = format_.split(":")[2].strip()
        search_term = '"{}" "{}" "{}"'.format(
            purpose, terse_format, command_description
        )
        self.search_rules(search_term)

    def ensure_fpr_rule_enabled(self, purpose, format_, command_description):
        self.navigate(self.get_rules_url())
        self.search_for_fpr_rule(purpose, format_, command_description)
        self.wait_for_presence("#DataTables_Table_0_info")
        info_el = self.driver.find_element_by_id("DataTables_Table_0_info")
        if info_el.text.strip().startswith("Showing 0 to 0 of 0 entries"):
            return
        disabled_rules = [
            row
            for row in self.driver.find_elements_by_css_selector(
                "#DataTables_Table_0 tbody tr"
            )
            if row.find_element_by_css_selector("td:nth-child(5)").text == "No"
        ]
        if not disabled_rules:
            logger.info(
                'Tried to enable FPR rule with purpose "{}" that runs command "{}"'
                ' against files with format "{}" but did not find it'.format(
                    purpose, command_description, format_
                )
            )
            return
        assert len(disabled_rules) == 1, (
            'Expected to enable one FPR rule with purpose "{}" that runs command "{}"'
            ' against files with format "{}" but found {} disabled rules'.format(
                purpose, command_description, format_, len(disabled_rules)
            )
        )
        rule = disabled_rules[0]
        rule.find_element_by_css_selector("td:nth-child(6) a:nth-child(3)").click()
        self.driver.find_element_by_css_selector("input[value=Enable]").click()

    @staticmethod
    def get_policy_command_description(policy_file):
        return "Check against policy {} using MediaConch".format(policy_file)
