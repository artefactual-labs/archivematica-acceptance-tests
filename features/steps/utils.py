"""Utilities for Steps files."""

import logging
import os
import re


logger = logging.getLogger(__file__)
log_filename = 'steps.log'
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        log_filename)
handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class ArchivematicaStepsError(Exception):
    pass


def wait_for_micro_service_to_complete(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_user.browser.await_job_completion(
        microservice_name, uuid_val, unit_type=unit_type)


def wait_for_decision_point_to_appear(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    job_uuid, _ = context.am_user.browser.await_decision_point(
        microservice_name, uuid_val, unit_type=unit_type)
    context.scenario.awaiting_job_uuid = job_uuid


def make_choice(context, choice, decision_point, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_user.browser.make_choice(
        choice, decision_point, uuid_val, unit_type=unit_type)


def get_normalized_unit_type(unit_type):
    return {'transfer': 'transfer'}.get(unit_type, 'sip')


def get_uuid_val(context, unit_type):
    """Return the UUID value corresponding to the ``unit_type`` ('transfer' or
    'sip') of the unit being tested in this scenario.
    """
    if unit_type == 'transfer':
        uuid_val = context.scenario.transfer_uuid
    else:
        uuid_val = getattr(context.scenario, 'sip_uuid', None)
        if not uuid_val:
            # If we are getting a SIP UUID from a transfer name, it is possible
            # that the transfer name is a .zip file name, in which case we must
            # remove the '.zip'. This is possible because zipped bag type
            # transfers are named after the transfer source file yet when they
            # become SIPs the extension is removed.
            context.scenario.transfer_name = (
                context.scenario.transfer_name.rstrip('.zip'))
            uuid_val = context.scenario.sip_uuid = (
                context.am_user.browser.get_sip_uuid(context.scenario.transfer_name))
    return uuid_val


def aip_descr_to_attr(aip_description):
    return aip_description.lower().strip().replace(' ', '_') + '_uuid'


def aip_descr_to_ptr_attr(aip_description):
    return aip_description.lower().strip().replace(' ', '_') + '_ptr'


def get_event_attr(event_type):
    return '{}_event_uuid'.format(event_type)


def get_mets_from_scenario(context):
    return context.am_user.browser.get_mets(
        context.scenario.transfer_name,
        context.am_user.browser.get_sip_uuid(context.scenario.transfer_name))


def assert_premis_event(event_type, event, context):
    """Make PREMIS-event-type-specific assertions about ``event``."""
    if event_type == 'unpacking':
        premis_evt_detail_el = event.find(
            'premis:eventDetail', context.am_user.mets.mets_nsmap)
        assert premis_evt_detail_el.text.strip().startswith('Unpacked from: ')
    elif event_type == 'message digest calculation':
        event_detail = event.find('premis:eventDetail', context.am_user.mets.mets_nsmap).text
        event_odn = event.find(
            'premis:eventOutcomeInformation/'
            'premis:eventOutcomeDetail/'
            'premis:eventOutcomeDetailNote',
            context.am_user.mets.mets_nsmap).text
        assert 'program="python"' in event_detail
        assert 'module="hashlib.sha256()"' in event_detail
        assert re.search('^[a-f0-9]+$', event_odn)
    elif event_type == 'virus check':
        event_detail = event.find(
            'premis:eventDetail', context.am_user.mets.mets_nsmap).text
        event_outcome = event.find(
            'premis:eventOutcomeInformation/premis:eventOutcome',
            context.am_user.mets.mets_nsmap).text
        assert 'program="Clam AV"' in event_detail
        assert event_outcome == 'Pass'


def assert_premis_properties(event, context, properties):
    """Make assertions about the ``event`` element using the user-supplied
    ``properties`` dict, which maps descendants of ``event`` to dicts that map
    relations on those descendants to values.
    """
    for xpath, predicates in properties.items():
        xpath = '/'.join(['premis:' + part for part in xpath.split('/')])
        desc_el = event.find(xpath, context.am_user.mets.mets_nsmap)
        for relation, value in predicates:
            if relation == 'equals':
                assert desc_el.text.strip() == value, (
                    '{} does not equal {}'.format(desc_el.text.strip(), value))
            elif relation == 'contains':
                assert value in desc_el.text.strip(), (
                    '{} does not substring-contain {}'.format(
                        desc_el.text.strip(), value))
            elif relation == 'regex':
                assert re.search(value, desc_el.text.strip()), (
                    '{} does not contain regex {}'.format(
                        desc_el.text.strip(), value))


def initiate_transfer(context, transfer_path, accession_no=None,
                      transfer_type=None):
    if transfer_path.startswith('~'):
        context.scenario.transfer_path = os.path.join(
            context.HOME, transfer_path[2:])
    else:
        context.scenario.transfer_path = os.path.join(
            context.TRANSFER_SOURCE_PATH, transfer_path)
    context.scenario.transfer_name = context.am_user.browser.unique_name(
        transfer_path2name(transfer_path))
    context.scenario.transfer_uuid, context.scenario.transfer_name = (
        context.am_user.browser.start_transfer(
            context.scenario.transfer_path, context.scenario.transfer_name,
            accession_no=accession_no, transfer_type=transfer_type))


def ingest_ms_output_is(name, output, context):
    """Wait for the Ingest micro-service with name ``name`` to appear and
    assert that its output is ``output``.
    """
    context.scenario.sip_uuid = context.am_user.browser.get_sip_uuid(
        context.scenario.transfer_name)
    context.scenario.job = context.am_user.browser.parse_job(
        name, context.scenario.sip_uuid, 'sip')
    assert context.scenario.job.get('job_output') == output


def debag(paths):
    """Given an array of paths like::

        >>> ['/BagTransfer/bag-info.txt',
        ...  '/BagTransfer/bagit.txt',
        ...  '/BagTransfer/manifest-sha512.txt',
        ...  '/BagTransfer/data/bagTest/LICENSE',
        ...  '/BagTransfer/data/bagTest/README',
        ...  '/BagTransfer/data/bagTest/TRADEMARK']

    return an array like::

        >>> ['/bagTest/LICENSE', '/bagTest/README', '/bagTest/TRADEMARK']

    """
    new_paths = []
    for path in paths:
        parts = path.split(os.path.sep)
        if len(parts) > 3 and parts[2] == 'data':
            new_paths.append(os.path.sep.join([''] + parts[3:]))
    return new_paths


def is_uuid(val):
    return (
        (''.join(x for x in val if x in '-abcdef0123456789') == val) and
        ([len(x) for x in val.split('-')] == [8, 4, 4, 4, 12]))


def remove_common_prefix(seq):
    """Recursively remove a common prefix from all strings in a sequence of
    strings.
    """
    try:
        prefixes = set([x[0] for x in seq])
    except IndexError:
        return seq
    if len(prefixes) == 1:
        return remove_common_prefix([x[1:] for x in seq])
    return seq


def get_subpaths_from_struct_map(elem, ns, base_path='', paths=None):
    if not paths:
        paths = set()
    for div_el in elem.findall('mets:div', ns):
        path = os.path.join(base_path, div_el.get('LABEL'))
        paths.add(path)
        for subpath in get_subpaths_from_struct_map(
                div_el, ns, base_path=path, paths=paths):
            paths.add(subpath)
    return list(paths)


def all_normalization_report_columns_are(column, expected_value, context):
    """Wait for the normalization report to be generated then assert that all
    values in ``column`` have value ``expected_value``.
    """
    normalization_report = context.am_user.browser.parse_normalization_report(
        context.scenario.sip_uuid)
    for file_dict in normalization_report:
        if file_dict['file_format'] != 'None':
            assert file_dict[column] == expected_value


def transfer_path2name(transfer_path):
    """Return a transfer name, given a transfer path."""
    return os.path.split(transfer_path.replace('-', '_'))[1]


def parse_k_v_attributes(attributes):
    """Parse a string of key-value attributes formatted like "key 1: value 1;
    key 2: value 2;".
    """
    return {pair.split(':')[0].strip(): pair.split(':')[1].strip() for
            pair in attributes.split(';') if pair.strip()}
