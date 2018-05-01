"""Archivematica Browser Storage Service Ability"""

import pprint

from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

from . import utils
from . import base
from . import selenium_ability


LOGGER = utils.LOGGER


class ArchivematicaBrowserStorageServiceAbilityError(
        base.ArchivematicaUserError):
    pass


class ArchivematicaBrowserStorageServiceAbility(
        selenium_ability.ArchivematicaSeleniumAbility):
    """Archivematica Browser Storage Service Ability: the ability of an
    Archivematica user to use a browser to interact with the Archivematica
    Storage Service.
    """

    def approve_aip_delete_request(self, aip_uuid):
        """Approve the deletion request of AIP with UUID ``aip_uuid`` via the
        SS GUI.
        """
        self.navigate(self.get_ss_package_delete_request_url())
        self.driver.find_element_by_id(
            'DataTables_Table_0_filter').find_element_by_tag_name(
                'input').send_keys(aip_uuid)
        matching_rows = []
        for row_el in self.driver.find_elements_by_css_selector(
                'table#DataTables_Table_0 tbody tr'):
            if len(row_el.find_elements_by_tag_name('td')) == 7:
                matching_rows.append(row_el)
        if len(matching_rows) != 1:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                'More than one delete request row {} matches AIP'
                ' {}'.format(len(matching_rows), aip_uuid))
        matching_rows[0].find_element_by_tag_name('textarea').send_keys(
            'Cuz wanna')
        matching_rows[0].find_element_by_css_selector(
            'input[name="approve"]').click()
        assert self.driver.find_element_by_css_selector(
            'div.alert-success').text.strip() == (
                'Request approved: Package deleted successfully.')

    def search_for_aip_in_storage_service(self, aip_uuid):
        self.navigate(self.get_packages_url())
        self.driver.find_element_by_css_selector('input[type=text]').send_keys(
            aip_uuid)
        # DataTables_Table_0
        row_els = self.driver.find_elements_by_css_selector(
            '#DataTables_Table_0 tr')
        result = []
        header = row_els[0]
        keys = [th_el.text.strip().lower().replace(' ', '_')
                for th_el in header.find_elements_by_tag_name('th')]
        for row_el in row_els[1:]:
            row_dict = {}
            for index, td_el in enumerate(row_el.find_elements_by_tag_name('td')):
                row_dict[keys[index]] = td_el.text.strip()
            result.append(row_dict)
        return result

    def ensure_ss_space_exists(self, attributes):
        """Ensure there is a Storage Service space with the attributes in the
        ``attributes`` dict.
        """
        matching_space = self.search_for_ss_space(attributes)
        if matching_space:
            LOGGER.info('matching space:\n%s', pprint.pformat(matching_space))
            return matching_space['uuid']
        LOGGER.info('space with attributes %s does NOT exist', attributes)
        return self.create_ss_space(attributes)

    def search_for_ss_space(self, attributes):
        """Return first SS space matching all attrs in ``attributes`` dict."""
        for ex_space in self.get_existing_spaces():
            match = True
            for key, val in attributes.items():
                if ex_space.get(key.lower()) != val:
                    LOGGER.debug('%s\ndoes NOT match\n%s',
                                 ex_space.get(key.lower()), val)
                    match = False
                    break
            if match:
                return ex_space
        LOGGER.debug('No SS space matching attributes %s', pprint.pformat(attributes))
        return None

    def create_ss_space(self, attributes):
        """Create an AM SS Space using ``attributes``."""
        self.navigate(self.get_spaces_create_url())
        form_el = self.driver.find_element_by_css_selector(
            'form[action="/spaces/create/"]')
        protocol_el = self.driver.find_element_by_id('protocol_form')
        for parent in (form_el, protocol_el):
            for p_el in parent.find_elements_by_tag_name('p'):
                for el in p_el.find_elements_by_css_selector('*'):
                    if el.tag_name == 'label':
                        label_text = el.text.strip().lower().replace(':', '')
                        for key, val in attributes.items():
                            if key.lower() == label_text:
                                input_id = el.get_attribute('for')
                                input_el = self.driver.find_element_by_id(input_id)
                                if input_el.tag_name == 'select':
                                    Select(input_el).select_by_visible_text(val)
                                else:
                                    input_el.send_keys(val)
        self.driver.find_element_by_css_selector('input[type=submit]').click()
        header = self.driver.find_element_by_tag_name('h1').text.strip()
        space_uuid = header.split()[0].replace('"', '').replace(':', '')
        return space_uuid

    def create_ss_location(self, space_uuid, attributes):
        """Create an AM SS Location, in Space with UUID ``space_uuid``, using
        attributes ``attributes``.
        """
        self.navigate(self.get_locations_create_url(space_uuid))
        form_el = self.driver.find_element_by_css_selector(
            'form[action="/spaces/{}/location_create/"]'.format(
                space_uuid))
        for p_el in form_el.find_elements_by_tag_name('p'):
            for el in p_el.find_elements_by_css_selector('*'):
                if el.tag_name == 'label':
                    label_text = el.text.strip().lower().replace(':', '')
                    for key, val in attributes.items():
                        if key.lower() == label_text:
                            input_id = el.get_attribute('for')
                            input_el = self.driver.find_element_by_id(input_id)
                            if input_el.tag_name == 'select':
                                Select(input_el).select_by_visible_text(val)
                            else:
                                input_el.send_keys(val)
                    # Here we just choose the first available pipeline for the
                    # location. This is a hack but it's better than having a
                    # pipeline-less location. WARNING/TODO: this will need to
                    # be changed for setups with multiple pipelines.
                    if label_text == 'pipeline':
                        input_id = el.get_attribute('for')
                        select_el = self.driver.find_element_by_id(input_id)
                        select = Select(select_el)
                        select.select_by_index(0)
        self.driver.find_element_by_css_selector('input[type=submit]').click()
        header = self.driver.find_element_by_tag_name('h1').text.strip()
        location_uuid = header.split()[0].replace('"', '').replace(':', '')
        return location_uuid

    def get_existing_spaces(self):
        """Return a summary of the existing spaces in the AM SS as a list of
        dicts.
        """
        existing_spaces = []
        self.navigate(self.get_spaces_url())
        space_urls = []
        for div_el in self.driver.find_elements_by_css_selector('div.space'):
            space_detail_anchor = div_el.find_element_by_xpath(
                'dl/dd/ul/li/a[text() = "View Details and Locations"]')
            space_urls.append(space_detail_anchor.get_attribute('href'))
        for space_url in space_urls:
            self.navigate(space_url)
            space_uuid = space_url
            if space_uuid.endswith('/'):
                space_uuid = space_uuid[:-1]
            space_uuid = space_uuid.split('/')[-1]
            space = {'uuid': space_uuid}
            space_div_el = self.driver.find_element_by_css_selector('div.space dl')
            last_key = None
            for el in space_div_el.find_elements_by_css_selector('dt, dd'):
                text = el.text.strip()
                if el.tag_name == 'dt':
                    last_key = text.lower()
                elif text != 'Actions':
                    space[last_key] = text
            existing_spaces.append(space)
        return existing_spaces

    def get_existing_locations(self, space_uuid):
        """Return a summary of the existing locations in the space with UUID
        ``space_uuid`` in the AM SS as a list of dicts.
        """
        existing_locations = []
        self.navigate(self.get_space_url(space_uuid))
        location_urls = {}
        for tr_el in self.driver.find_elements_by_css_selector('tbody tr'):
            loc_uuid_td_el = tr_el.find_element_by_xpath('td[position()=5]')
            loc_uuid = loc_uuid_td_el.text.strip()
            location_urls[loc_uuid] = self.get_location_url(loc_uuid)
        for loc_uuid, loc_url in location_urls.items():
            self.navigate(loc_url)
            location = {'uuid': loc_uuid}
            loc_div_el = self.driver.find_element_by_css_selector('div.location dl')
            last_key = None
            for el in loc_div_el.find_elements_by_css_selector('dt, dd'):
                text = el.text.strip()
                if el.tag_name == 'dt':
                    last_key = text.lower()
                elif text not in ('Space', 'Actions'):
                    location[last_key] = text
            existing_locations.append(location)
        return existing_locations

    def ensure_ss_location_exists(self, space_uuid, attributes):
        """Ensure there is a Storage Service location within the space with
        UUID ``space_uuid`` that has the attributes in the ``attributes`` dict.
        Return that location's UUId.
        """
        existing_locations = self.get_existing_locations(space_uuid)
        matching_loc = None
        for ex_loc in existing_locations:
            match = True
            for key, val in attributes.items():
                if ex_loc.get(key.lower()) != val:
                    match = False
                    break
            if match:
                matching_loc = ex_loc
                break
        if matching_loc:
            loc_uuid = matching_loc['uuid']
        else:
            LOGGER.info('location with attributes %s does NOT exist',
                        attributes)
            loc_uuid = self.create_ss_location(space_uuid, attributes)
        return loc_uuid

    def add_replicator_to_default_aip_stor_loc(self, replicator_location_uuid):
        """Add the replicator location with UUID ``replicator_location_uuid``
        to the set of replicators of the default AIP Storage location. Assumes
        that the first location that matches the search term "Store AIP in
        standard Archivematica Directory" is THE default AIP Storage location.
        """
        self.navigate(self.get_locations_url())
        search_el = self.driver.find_element_by_css_selector('input[type=text]')
        search_el.send_keys('Store AIP in standard Archivematica Directory')
        row_els = self.driver.find_elements_by_css_selector(
            '#DataTables_Table_0 > tbody > tr')
        if not row_els:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                'Unable to find a default AIP storage location')
        if len(row_els) > 1:
            new_row_els = []
            for row_el in row_els:
                row_text = []
                for td_el in row_el.find_elements_by_css_selector('td'):
                    row_text.append(td_el.text.strip().lower())
                if 'encrypted' not in ''.join(row_text):
                    new_row_els.append(row_el)
            if len(new_row_els) == 1:
                row_els = new_row_els
            else:
                raise ArchivematicaBrowserStorageServiceAbilityError(
                    'Unable to find a unique default AIP storage location')
        cell_el = row_els[0].find_elements_by_css_selector('td')[9]
        edit_a_el = None
        for a_el in cell_el.find_elements_by_css_selector('a'):
            if a_el.text.strip() == 'Edit':
                edit_a_el = a_el
        if not edit_a_el:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                'Unable to find an edit button/link for the default'
                ' AIP storage location')
        edit_a_el.click()
        self.wait_for_presence('select#id_replicators')
        replicators_select_el = self.driver.find_element_by_css_selector(
            'select#id_replicators')
        replicators_select = Select(replicators_select_el)
        found_replicator = False
        for option in replicators_select.options:
            if replicator_location_uuid in option.text:
                replicators_select.select_by_visible_text(option.text)
                found_replicator = True
                break
        if not found_replicator:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                'Unable to find replicator location {} as a possible replicator'
                ' for the default AIP Storage'
                ' location'.format(replicator_location_uuid))
        self.driver.find_element_by_css_selector('input[type=submit]').click()

    def import_gpg_key(self, key_path):
        """Navigate to the GPG key import page and attempt to import the GPG
        key whose private key ASCII armor is stored in the file at
        ``key_path``. Return the alert message text displayed after the import
        attempt.
        """
        self.navigate(self.get_import_gpg_key_url())
        with open(key_path) as filei:
            self.driver.find_element_by_id('id_ascii_armor').send_keys(filei.read())
        self.driver.find_element_by_css_selector('input[type=submit]').click()
        self.wait_for_presence('div.alert', 20)
        return self.driver.find_element_by_css_selector('div.alert').text.strip()

    def get_gpg_key_search_matches(self, search_string):
        """Navigate to the GPG keys page and return the fingerprints of all
        keys matching ``search_string``.
        """
        fingerprints = []
        self.navigate(self.get_gpg_keys_url())
        self.driver.find_element_by_css_selector('input[type=text]').send_keys(
            search_string)
        for row_el in self.driver.find_elements_by_css_selector(
                'table#DataTables_Table_0 tbody tr'):
            try:
                fingerprints.append(
                    row_el.find_elements_by_tag_name('td')[1].text.strip())
            except IndexError:
                pass
        return fingerprints

    def delete_gpg_key(self, key_name):
        """Navigate to the GPG keys page, search for a key matching
        ``key_name``, and attempt to delete it. Returns a 2-tuple:
        ``(succeeded, msg)`` where ``succeeded`` is a boolean and ``msg`` is a
        string.
        """
        self.navigate(self.get_gpg_keys_url())
        self.driver.find_element_by_css_selector('input[type=text]').send_keys(
            key_name)
        matches = self.driver.find_elements_by_css_selector(
            'table#DataTables_Table_0 tbody tr')
        try:
            assert len(matches) == 1
        except AssertionError:
            LOGGER.info('Unable to delete GPG key with name "%s" because there'
                        ' are %s keys matching that name', key_name,
                        len(matches))
            raise
        else:
            matches[0].find_element_by_xpath(
                'td[3]/a[text() = "Delete"]').click()
        try:
            self.driver.find_element_by_css_selector('input[value=Delete]').click()
            try:
                return True, self.driver.find_element_by_css_selector(
                    'div.alert-success').text.strip()
            except NoSuchElementException:
                return False, 'unknown'
        except NoSuchElementException:
            return False, self.driver.find_element_by_css_selector(
                'div.alert-error').text.strip()

    def disable_default_transfer_backlog(self):
        self.navigate(self.get_locations_url())
        search_el = self.driver.find_element_by_css_selector('input[type=text]')
        search_el.send_keys('Default transfer backlog')
        row_els = self.driver.find_elements_by_css_selector(
            '#DataTables_Table_0 > tbody > tr')
        if len(row_els) != 1:
            raise ArchivematicaBrowserStorageServiceAbilityError(
                'Unable to find a unique default transfer backlog location')
        cell_el = row_els[0].find_elements_by_css_selector('td')[9]
        disable_a_el = enable_a_el = None
        for a_el in cell_el.find_elements_by_css_selector('a'):
            print(a_el.text)
            if a_el.text.strip() == 'Disable':
                disable_a_el = a_el
            if a_el.text.strip() == 'Enable':
                enable_a_el = a_el
        if not (enable_a_el or disable_a_el):
            raise ArchivematicaBrowserStorageServiceAbilityError(
                'Unable to find a disable/enable button/link for the default'
                ' transfer backlog location')
        if disable_a_el:
            disable_a_el.click()

    def create_new_gpg_key(self):
        """Create a new GPG key with a unique name."""
        self.navigate(self.get_create_gpg_key_url())
        new_key_name = 'GPGKey {}'.format(utils.unixtimestamp())
        new_key_email = '{}@example.com'.format(new_key_name.lower().replace(' ', ''))
        self.driver.find_element_by_id('id_name_real').send_keys(new_key_name)
        self.driver.find_element_by_id('id_name_email').send_keys(new_key_email)
        self.driver.find_element_by_css_selector('input[type=submit]').click()
        self.wait_for_presence('div.alert-success')
        alert_text = self.driver.find_element_by_css_selector(
            'div.alert-success').text
        new_key_fingerprint = alert_text.split()[2]
        return new_key_name, new_key_email, new_key_fingerprint

    def change_encrypted_space_key(self, space_uuid, new_key_repr=None):
        """Edit the existing space with UUID ``space_uuid`` and set its GPG key
        to the existing one matching ``new_key_repr``, if provided, or else to
        any other key.
        """
        self.navigate(self.get_space_edit_url(space_uuid))
        select = Select(self.driver.find_element_by_id('id_protocol-key'))
        if new_key_repr:
            select.select_by_visible_text(new_key_repr)
        else:
            currently_selected = select.first_selected_option.text
            for option in select.options:
                if option.text != currently_selected:
                    select.select_by_visible_text(option.text)
                    break
        self.driver.find_element_by_css_selector('input[type=submit]').click()
        self.wait_for_presence('div.alert-success')
