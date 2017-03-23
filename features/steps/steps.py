import filecmp
import json
import logging
from lxml import etree
import os
import pprint
import re
import time

from behave import when, then, given

logger = logging.getLogger(__file__)
log_filename, _ = os.path.splitext(os.path.basename(__file__))
log_filename = log_filename + '.log'
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_filename)
handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

MC_EVENT_DETAIL_PREFIX = 'program="MediaConch"'
MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX = \
    'MediaConch implementation check result:'
MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX = \
    'MediaConch policy check result'
POLICIES_DIR = 'mediaconch-policies'


class ArchivematicaSeleniumStepsError(Exception):
    pass


@when('the user waits for the "{microservice_name}" micro-service to complete'
      ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_sel_cli.await_job_completion(
        microservice_name, uuid_val, unit_type=unit_type)


@given('the user waits for the "{microservice_name}" micro-service to complete'
      ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    context.execute_steps('When the user waits for the "{}" micro-service to'
        ' complete during {}'.format(microservice_name, unit_type))


@when('the user waits for the "{microservice_name}" decision point to appear'
      ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    job_uuid, job_output = context.am_sel_cli.await_decision_point(
        microservice_name, uuid_val, unit_type=unit_type)
    context.scenario.awaiting_job_uuid = job_uuid


@given('the user waits for the "{microservice_name}" decision point to appear'
       ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    context.execute_steps('When the user waits for the "{}" decision point to'
        ' appear during {}'.format(microservice_name, unit_type))


@when('the user waits for the "{microservice_name}" decision point to appear'
      ' and chooses "{choice}" during {unit_type}')
def step_impl(context, microservice_name, choice, unit_type):
    steps = (
        'When the user waits for the "{}" decision point to appear during {}\n'
        'When the user chooses "{}" at decision point "{}" during {}\n'
    ).format(microservice_name, unit_type, choice, microservice_name,
             unit_type)
    context.execute_steps(steps)



@when('the user chooses "{choice}" at decision point "{decision_point}" during'
      ' {unit_type}')
def step_impl(context, choice, decision_point, unit_type):
    step = ('when the user waits for the "{}" decision point to appear during'
            ' {}'.format(decision_point, unit_type))
    context.execute_steps(step)
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_sel_cli.make_choice(
        choice, decision_point, uuid_val, unit_type=unit_type)


@given('the user chooses "{choice}" at decision point "{decision_point}" during'
      ' {unit_type}')
def step_impl(context, choice, decision_point, unit_type):
    context.execute_steps('When the user chooses "{}" at decision point "{}"'
        ' during {}'.format(choice, decision_point, unit_type))


@when('the user waits for the AIP to appear in archival storage')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'sip')
    context.am_sel_cli.wait_for_aip_in_archival_storage(uuid_val)


@when('the user downloads the AIP')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'sip')
    transfer_name = context.scenario.transfer_name
    context.scenario.aip_path = context.am_sel_cli.download_aip(
        transfer_name, uuid_val)


@when('the user downloads the AIP pointer file')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'sip')
    transfer_name = context.scenario.transfer_name
    context.scenario.aip_pointer_path = context.am_sel_cli.download_aip_pointer_file(
        transfer_name, uuid_val)


@then('the pointer file contains a PREMIS:EVENT element for the encryption event')
def step_impl(context):
    """This asserts that the pointer file contains a ``<mets:mdWrap
    MDTYPE="PREMIS:EVENT">`` element with the following type of descendants:
    - <mets:xmlData>
    - <premis:eventType>encryption</premis:eventType>
    - <premis:eventDetail>program=gpg (GnuPG); version=1.4.16; python-gnupg; version=0.4.0</premis:eventDetail>
    - <premis:eventOutcomeInformation>
          <premis:eventOutcome/>
          <premis:eventOutcomeDetail>
              <premis:eventOutcomeDetailNote>
                  Status="encryption ok"; Standard Error="gpg:
                  reading options from
                  `/var/lib/archivematica/.gnupg/gpg.conf'
                  [GNUPG:] BEGIN_ENCRYPTION 2 9 [GNUPG:]
                  END_ENCRYPTION"
              </premis:eventOutcomeDetailNote>
          </premis:eventOutcomeDetail>
      </premis:eventOutcomeInformation>

    """
    pointer_path = context.scenario.aip_pointer_path
    with open(pointer_path) as filei:
        doc = etree.parse(filei)
        # 'mets:transformFile[@TRANSFORMTYPE="decompression"]',
        premis_event = None
        for premis_event_el in doc.findall(
                './/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]',
                context.am_sel_cli.mets_nsmap):
            premis_event_type_el = premis_event_el.find(
                'mets:xmlData/premis:event/premis:eventType',
                context.am_sel_cli.mets_nsmap)
            if premis_event_type_el.text.strip() == 'encryption':
                premis_event = premis_event_el
                break
        assert premis_event is not None
        # <premis:eventDetail>program=gpg (GnuPG); version=1.4.16; python-gnupg; version=0.4.0</premis:eventDetail>
        premis_event_detail = premis_event.find(
            'mets:xmlData/premis:event/premis:eventDetail',
            context.am_sel_cli.mets_nsmap).text
        assert 'GnuPG' in premis_event_detail
        assert 'version=' in premis_event_detail
        premis_event_od_note = premis_event.find(
            'mets:xmlData/premis:event/premis:eventOutcomeInformation/'
            'premis:eventOutcomeDetail/premis:eventOutcomeDetailNote',
            context.am_sel_cli.mets_nsmap).text.strip()
        assert 'Status="encryption ok"' in premis_event_od_note


@then('the pointer file contains a mets:transformFile element for the encryption event')
def step_impl(context):
    """Makes the following assertions abou the first (and presumably only)
    <mets:file> element in the AIP's pointer file:
    1. the xlink:href attribute's value of <mets:FLocat> is a path with
       extension .gpg
    2. the decompression-type <mets:transformFile> has TRANSFORMORDER 2
    3. there is a new <mets:transformFile> element for the decryption event
       needed to get at this AIP.
    4. <premis:compositionLevel> incremented
    5. <premis:inhibitors> added
    """
    pointer_path = context.scenario.aip_pointer_path
    ns = context.am_sel_cli.mets_nsmap
    with open(pointer_path) as filei:
        doc = etree.parse(filei)
        file_el = doc.find(
            'mets:fileSec/mets:fileGrp/mets:file', ns)
        # <tranformFile> decryption element added, and decompression one
        # modified.
        deco_tran_el = file_el.find(
            'mets:transformFile[@TRANSFORMTYPE="decompression"]', ns)
        assert deco_tran_el is not None
        assert deco_tran_el.get('TRANSFORMORDER', ns) == '2'
        decr_tran_el = file_el.find(
            'mets:transformFile[@TRANSFORMTYPE="decryption"]', ns)
        assert decr_tran_el is not None
        assert decr_tran_el.get('TRANSFORMORDER', ns) == '1'
        assert decr_tran_el.get('TRANSFORMALGORITHM', ns) == 'gpg'
        assert bool(decr_tran_el.get('TRANSFORMTYPE', ns)) is True
        # premis:compositionLevel incremented
        compos_lvl_el = doc.find(
            'mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/'
            'premis:objectCharacteristics/premis:compositionLevel', ns)
        assert compos_lvl_el is not None
        assert compos_lvl_el.text.strip() == '2'
        # premis:inhibitors added
        inhibitors_el = doc.find(
            'mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/'
            'premis:objectCharacteristics/premis:inhibitors', ns)
        assert inhibitors_el is not None
        assert inhibitors_el.find('premis:inhibitorType', ns).text.strip() == (
            'PGP')
        assert inhibitors_el.find('premis:inhibitorTarget', ns).text.strip() == (
            'All content')


@then('the AIP on disk is encrypted')
def step_impl(context):
    """Asserts that the AIP on the server (pointed to within the AIP pointer
    file stored in context.scenario.aip_pointer_path) is encrypted. To do this,
    we use scp to copy the remote AIP to a local directory and then we attemt
    to decompress it and expect to fail.
    """
    pointer_path = context.scenario.aip_pointer_path
    ns = context.am_sel_cli.mets_nsmap
    with open(pointer_path) as filei:
        doc = etree.parse(filei)
        file_el = doc.find('mets:fileSec/mets:fileGrp/mets:file', ns)
        flocat_el = file_el.find('mets:FLocat', ns)
        xlink_href = flocat_el.get('{' + ns['xlink'] + '}href')
        # Use scp to copy the AIP on the server to a local directory.
        aip_local_path = context.am_sel_cli.scp_server_file_to_local(xlink_href)
        if aip_local_path is None:
            print('Unable to copy file {} from the server to the local file'
                  ' system. Server is not accessible via SSH. Abandoning'
                  ' attempt to assert that the AIP on disk is'
                  ' encrypted.'.format(xlink_href))
            return
        elif aip_local_path is False:
            print('Unable to copy file {} from the server to the local file'
                  ' system. Attempt to scp the file failed. Abandoning attempt'
                  ' to assert that the AIP on disk is'
                  ' encrypted.'.format(xlink_href))
            return
    aip_local_path = context.am_sel_cli.decompress_package(aip_local_path)
    # ``decompress_package`` will attempt to decompress the package with 7z and
    # we expect it to fail because the AIP file is encrypted with GPG.
    assert aip_local_path is None


@when('the user decompresses the AIP')
def step_impl(context):
    context.scenario.aip_path = context.am_sel_cli.decompress_aip(
        context.scenario.aip_path)


@then('the submissionDocumentation directory of the AIP {contains} a copy of'
      ' the MediaConch policy file {policy_file}')
def step_impl(context, contains, policy_file):
    aip_path = context.scenario.aip_path
    original_policy_path = os.path.join(POLICIES_DIR, policy_file)
    aip_policy_path = os.path.join(
        aip_path, 'data', 'objects', 'submissionDocumentation', 'policies',
        policy_file)
    if contains in ('contains', 'does contain'):
        assert os.path.isfile(original_policy_path)
        assert os.path.isfile(aip_policy_path), ('There is no MediaConch policy'
            ' file in the AIP at {}!'.format(aip_policy_path))
        assert filecmp.cmp(original_policy_path, aip_policy_path)
    else:
        assert not os.path.isfile(aip_policy_path), ('There is a MediaConch policy'
            ' file in the AIP at {} but there shouldn\'t be!'.format(
                aip_policy_path))


@then('the transfer logs directory of the AIP {contains} a copy of the'
      ' MediaConch policy file {policy_file}')
def step_impl(context, contains, policy_file):
    aip_path = context.scenario.aip_path
    original_policy_path = os.path.join(POLICIES_DIR, policy_file)
    policy_file_no_ext, _ = os.path.splitext(policy_file)
    transfer_dirname = '{}-{}'.format(context.scenario.transfer_name,
                                      context.scenario.transfer_uuid)
    aip_policy_path = os.path.join(aip_path, 'data', 'logs', 'transfers',
                                   transfer_dirname, 'logs', 'policyChecks',
                                   policy_file_no_ext, policy_file)
    if contains in ('contains', 'does contain'):
        assert os.path.isfile(original_policy_path)
        assert os.path.isfile(aip_policy_path), ('There is no MediaConch policy'
            ' file in the AIP at {}!'.format(aip_policy_path))
        assert filecmp.cmp(original_policy_path, aip_policy_path)
    else:
        assert not os.path.isfile(aip_policy_path), ('There is a MediaConch policy'
            ' file in the AIP at {} but there shouldn\'t be!'.format(
                aip_policy_path))


@then('the transfer logs directory of the AIP contains a MediaConch policy'
      ' check output file for each policy file tested against {policy_file}')
def step_impl(context, policy_file):
    policy_file_no_ext, _ = os.path.splitext(policy_file)
    aip_path = context.scenario.aip_path
    assert policy_file_no_ext, 'policy_file_no_ext is falsey!'
    transfer_dirname = '{}-{}'.format(context.scenario.transfer_name,
                                      context.scenario.transfer_uuid)
    aip_policy_outputs_path = os.path.join(
        aip_path, 'data', 'logs', 'transfers', transfer_dirname, 'logs',
        'policyChecks', policy_file_no_ext)
    assert os.path.isdir(aip_policy_outputs_path)
    contents = os.listdir(aip_policy_outputs_path)
    assert len(contents) > 0
    file_paths = [x for x in [os.path.join(aip_policy_outputs_path, y) for y in
                  contents] if os.path.isfile(x) and
                  os.path.splitext(x)[1] == '.xml']
    assert len(file_paths) > 0, ('There are no files in dir'
        ' {}!'.format(aip_policy_outputs_path))
    for fp in file_paths:
        with open(fp) as f:
            doc = etree.parse(f)
            root_tag = doc.getroot().tag
            expected_root_tag = '{https://mediaarea.net/mediaconch}MediaConch'
            assert root_tag == expected_root_tag, ('The root tag of file {} was'
                ' expected to be {} but was actually {}'.format(
                    fp, expected_root_tag, root_tag))


@then('the logs directory of the AIP contains a MediaConch policy check output'
      ' file for each policy file tested against {policy_file}')
def step_impl(context, policy_file):
    policy_file_no_ext, _ = os.path.splitext(policy_file)
    aip_path = context.scenario.aip_path
    assert policy_file_no_ext, 'policy_file_no_ext is falsey!'
    aip_policy_outputs_path = os.path.join(
        aip_path, 'data', 'logs', 'policyChecks', policy_file_no_ext)
    assert os.path.isdir(aip_policy_outputs_path)
    contents = os.listdir(aip_policy_outputs_path)
    assert len(contents) > 0
    file_paths = [x for x in [os.path.join(aip_policy_outputs_path, y) for y in
                  contents] if os.path.isfile(x) and
                  os.path.splitext(x)[1] == '.xml']
    assert len(file_paths) > 0, ('There are no files in dir'
        ' {}!'.format(aip_policy_outputs_path))
    for fp in file_paths:
        with open(fp) as f:
            doc = etree.parse(f)
            assert doc.getroot().tag == '{https://mediaarea.net/mediaconch}MediaConch'


@then('the "{microservice_name}" micro-service output is'
      ' "{microservice_output}" during {unit_type}')
def step_impl(context, microservice_name, microservice_output, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.scenario.job = context.am_sel_cli.parse_job(
        microservice_name, uuid_val, unit_type=unit_type)
    assert context.scenario.job.get('job_output') == microservice_output


###############################################################################
# FEATURE: Metadata-only AIP Re-ingest
###############################################################################

@when('the user adds metadata')
def step_impl(context):
    context.am_sel_cli.add_dummy_metadata(get_uuid_val(context, 'sip'))


@when('the user initiates a {reingest_type} re-ingest on the AIP')
def step_impl(context, reingest_type):
    uuid_val = get_uuid_val(context, 'sip')
    context.am_sel_cli.initiate_reingest(
        uuid_val, reingest_type=reingest_type)


# For DEVELOPMENT
@when('the user initiates a {reingest_type} re-ingest on the AIP and waits')
def step_impl(context, reingest_type):
    uuid_val = get_uuid_val(context, 'sip')
    context.am_sel_cli.initiate_reingest(
        uuid_val, reingest_type=reingest_type, wait=True)


@given('that the user has ensured that the default processing config is in its'
       ' default state')
def step_impl(context):
    context.am_sel_cli.ensure_default_processing_config_in_default_state()


@given('the reminder to add metadata is enabled')
def step_impl(context):
    context.am_sel_cli.set_processing_config_decision(
        decision_label='Reminder: add metadata if desired',
        choice_value='None')
    context.am_sel_cli.save_default_processing_config()


@given('the processing config decision "{decision_label}" is set to'
       ' "{choice_value}"')
def step_impl(context, decision_label, choice_value):
    context.am_sel_cli.set_processing_config_decision(
        decision_label=decision_label,
        choice_value=choice_value)
    context.am_sel_cli.save_default_processing_config()


def get_mets_from_scenario(context):
    return context.am_sel_cli.get_mets(
        context.scenario.transfer_name,
        context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name))


def get_mets_from_scenario_DEPRECATED(context):
    try:
        mets = context.scenario.mets
    except AttributeError:
        mets = context.scenario.mets = context.am_sel_cli.get_mets(
            context.scenario.transfer_name,
            context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name))
    return mets


def assert_premis_event(event_type, event, context):
    """Make PREMIS-event-type-specific assertions about ``event``."""
    if event_type == 'unpacking':
        premis_evt_detail_el = event.find(
            'premis:eventDetail', context.am_sel_cli.mets_nsmap)
        assert premis_evt_detail_el.text.strip().startswith('Unpacked from: ')
    elif event_type == 'message digest calculation':
        event_detail = event.find('premis:eventDetail', context.am_sel_cli.mets_nsmap).text
        event_odn = event.find(
            'premis:eventOutcomeInformation/'
            'premis:eventOutcomeDetail/'
            'premis:eventOutcomeDetailNote',
            context.am_sel_cli.mets_nsmap).text
        assert 'program="python"' in event_detail
        assert 'module="hashlib.sha256()"' in event_detail
        assert re.search('^[a-f0-9]+$', event_odn)
    elif event_type == 'virus check':
        event_detail = event.find('premis:eventDetail',
            context.am_sel_cli.mets_nsmap).text
        event_outcome = event.find(
            'premis:eventOutcomeInformation/premis:eventOutcome',
            context.am_sel_cli.mets_nsmap).text
        assert 'program="Clam AV"' in event_detail
        assert event_outcome == 'Pass'


def assert_premis_properties(event, context, properties):
    """Make assertions about the ``event`` element using the user-supplied
    ``properties`` dict, which maps descendants of ``event`` to dicts that map
    relations on those descendants to values.
    """
    for xpath, predicates in properties.items():
        xpath = '/'.join(['premis:' + part for part in xpath.split('/')])
        desc_el = event.find(xpath, context.am_sel_cli.mets_nsmap)
        for relation, value in predicates:
            if relation == 'equals':
                assert desc_el.text.strip() == value
            elif relation == 'contains':
                assert value in desc_el.text.strip()
            elif relation == 'regex':
                assert re.search(value, desc_el.text.strip())


@then('in the METS file there are/is {count} PREMIS event(s) of type'
      ' {event_type} with properties {properties}')
def step_impl(context, count, event_type, properties):
    mets = get_mets_from_scenario(context)
    events = []
    properties = json.loads(properties)
    for premis_evt_el in mets.findall('.//premis:event', context.am_sel_cli.mets_nsmap):
        premis_evt_type_el = premis_evt_el.find(
            'premis:eventType', context.am_sel_cli.mets_nsmap)
        if premis_evt_type_el.text == event_type:
            events.append(premis_evt_el)
            assert_premis_event(event_type, premis_evt_el, context)
            assert_premis_properties(premis_evt_el, context, properties)
    assert len(events) == int(count)


@then('in the METS file there are/is {count} PREMIS event(s) of type {event_type}')
def step_impl(context, count, event_type):
    mets = get_mets_from_scenario(context)
    events = []
    for premis_evt_el in mets.findall('.//premis:event', context.am_sel_cli.mets_nsmap):
        premis_evt_type_el = premis_evt_el.find(
            'premis:eventType', context.am_sel_cli.mets_nsmap)
        if premis_evt_type_el.text == event_type:
            events.append(premis_evt_el)
            assert_premis_event(event_type, premis_evt_el, context)
    assert len(events) == int(count)


@then('in the METS file the metsHdr element has a CREATEDATE attribute {conj_quant}'
      ' LASTMODDATE attribute')
def step_impl(context, conj_quant):
    """``conj_quant`` is 'but no' or 'and a', a conjunction followed by a
    quantifier, of course.
    """
    mets = get_mets_from_scenario(context)
    mets_hdr_els = mets.findall('.//mets:metsHdr', context.am_sel_cli.mets_nsmap)
    assert len(mets_hdr_els) == 1
    mets_hdr_el = mets_hdr_els[0]
    assert mets_hdr_el.get('CREATEDATE')
    if conj_quant == 'but no':
        assert mets_hdr_el.get('LASTMODDATE') is None
    else:
        assert mets_hdr_el.get('LASTMODDATE') is not None, ('<mets:metsHdr>'
            ' element is lacking a LASTMODDATE attribute:'
            ' {}'.format(mets_hdr_el.attrib))
        # TODO: assert that value is ISO datetime
    # Crucial, otherwise we'll be looking at the previous METS in subsequent
    # tests.
    # del context.scenario.mets


@then('in the METS file the metsHdr element has {quant} dmdSec element as a next'
      ' sibling')
def step_impl(context, quant):
    mets = get_mets_from_scenario(context)
    mets_dmd_sec_els = mets.findall('.//mets:dmdSec', context.am_sel_cli.mets_nsmap)
    if quant == 'no':
        assert len(mets_dmd_sec_els) == 0
    elif quant == 'one':
        assert len(mets_dmd_sec_els) == 1
    else:
        raise ArchivematicaSeleniumStepsError('Unable to recognize the'
            ' quantifier {} when checking for dmdSec elements in the METS'
            ' file'.format(quant))


@then('in the METS file the dmdSec element contains the metadata added')
def step_impl(context):
    mets = get_mets_from_scenario(context)
    dublincore_el = mets.find(
        './/mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:dublincore',
        context.am_sel_cli.mets_nsmap)
    assert dublincore_el
    for attr in context.am_sel_cli.metadata_attrs:
        dc_el = dublincore_el.find('dc:{}'.format(attr),
                                   context.am_sel_cli.mets_nsmap)
        assert dc_el is not None
        assert dc_el.text == context.am_sel_cli.dummy_val


###############################################################################
# FEATURE: PRE-INGEST CONFORMANCE CHECK
###############################################################################


@given('directory {transfer_path} contains files that are all {file_validity}'
       ' .mkv')
def step_impl(context, transfer_path, file_validity):
    pass


@then('validation micro-service output is {microservice_output}')
def step_impl(context, microservice_output):
    context.scenario.job = context.am_sel_cli.parse_job(
        'Validate formats', context.scenario.transfer_uuid)
    assert context.scenario.job.get('job_output') == microservice_output


@then('Archivematica continues processing')
def step_impl(context):
    print('Archivematica continues processing')


###############################################################################
# FEATURE: POST-NORMALIZATION CONFORMANCE CHECK
###############################################################################

# TODO: How to implement the following givens? Using SS API? Necessary?


@given('directory {transfer_path} contains files that will all be normalized'
       ' to {file_validity} .mkv')
def step_impl(context, transfer_path, file_validity):
    pass


@given('directory {transfer_path} contains a processing config that does'
       ' normalization for preservation, etc.')
def step_impl(context, transfer_path):
    """Details: transfer must contain a processing config that creates a SIP,
    does normalization for preservation, approves normalization, and creates an
    AIP without storing it
    """
    pass


@given('directory {transfer_path} contains a processing config that does'
       ' normalization for access, etc.')
def step_impl(context, transfer_path):
    """Details: transfer must contain a processing config that creates a SIP,
    does normalization for access, approves normalization, and creates an
    AIP without storing it
    """
    pass


# MKV-to-MKV (!) just for testing policy checks on access derivatives.
@when('the user edits the FPR rule to transcode .mkv files to .mkv for access')
def step_impl(context):
    context.am_sel_cli.change_normalization_rule_command(
        'Access Generic MKV',
        'Transcoding to mkv with ffmpeg')


@when('the user edits the FPR rule to transcode .mov files to .mkv for access')
def step_impl(context):
    context.am_sel_cli.change_normalization_rule_command(
        'Access Generic MOV',
        'Transcoding to mkv with ffmpeg')


@given('a transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_path):
    context.execute_steps('When a transfer is initiated on directory'
        ' {}'.format(transfer_path))


@when('a transfer is initiated on directory {transfer_path} with accession number {accession_no}')
def step_impl(context, transfer_path, accession_no):
    initiate_transfer(context, transfer_path, accession_no=accession_no)


@when('a transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_path):
    initiate_transfer(context, transfer_path)


@then('validate preservation derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    ingest_ms_output_is('Validate preservation derivatives',
                        microservice_output, context)


@then('validate access derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    ingest_ms_output_is('Validate access derivatives', microservice_output,
                        context)


@then('all preservation conformance checks in the normalization report have'
      ' value {validation_result}')
def step_impl(context, validation_result):
    all_normalization_report_columns_are(
        'preservation_conformance_check', validation_result, context)


@then('all access conformance checks in the normalization report have value'
      ' {validation_result}')
def step_impl(context, validation_result):
    all_normalization_report_columns_are(
        'access_conformance_check', validation_result, context)


@then('all PREMIS implementation-check-type validation events have'
      ' eventOutcome = {event_outcome}')
def step_impl(context, event_outcome):
    events = []
    for e in context.am_sel_cli.get_premis_events(context.am_sel_cli.get_mets(
            context.scenario.transfer_name,
            context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name))):
        if (e['event_type'] == 'validation' and
            e['event_detail'].startswith(MC_EVENT_DETAIL_PREFIX) and
            e['event_outcome_detail_note'].startswith(
                MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX)):
            events.append(e)
    assert len(events) > 0
    for e in events:
        assert e['event_outcome'] == event_outcome


###############################################################################
# INGEST POLICY CHECK
###############################################################################


@given('MediaConch policy file {policy_file} is present in the local'
       ' mediaconch-policies/ directory')
def step_impl(context, policy_file):
    assert policy_file in os.listdir(POLICIES_DIR)


@given('directory {transfer_path} contains files that, when normalized, will'
       ' all {do_files_conform} to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given('directory {transfer_path}/manualNormalization/preservation/ contains a'
       ' file manually normalized for preservation that will'
       '{do_files_conform} to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given('directory {transfer_path}/manualNormalization/access/ contains a'
       ' file manually normalized for access that will {do_files_conform}'
       ' to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given('directory {transfer_path} contains files that all do {do_files_conform}'
       ' to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@when('the user uploads the policy file {policy_file}')
def step_impl(context, policy_file):
    policy_path = get_policy_path(policy_file)
    context.am_sel_cli.upload_policy(policy_path)


@when('the user ensures there is an FPR command that uses policy file'
      ' {policy_file}')
def step_impl(context, policy_file):
    context.am_sel_cli.ensure_fpr_policy_check_command(policy_file)


# TODO: this step could be generalized to support any purpose/format/command
# triple.
@when('the user ensures there is an FPR rule with purpose {purpose} that'
      ' validates Generic MKV files against policy file {policy_file}')
def step_impl(context, purpose, policy_file):
    context.am_sel_cli.ensure_fpr_rule(
        purpose,
        'Video: Matroska: Generic MKV',
        context.am_sel_cli.get_policy_command_description(policy_file)
    )


@then('policy checks for preservation derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    name = 'Policy checks for preservation derivatives'
    ingest_ms_output_is(name, microservice_output, context)


@then('policy checks for access derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    name = 'Policy checks for access derivatives'
    ingest_ms_output_is(name, microservice_output, context)


@then('all policy check for access derivatives tasks indicate {event_outcome}')
def step_impl(context, event_outcome):
    policy_check_tasks = [t for t in context.scenario.job['tasks'].values() if
                          t['stdout'].startswith(
                              'Running Check against policy ')]
    assert len(policy_check_tasks) > 0
    if event_outcome == 'pass':
        for task in policy_check_tasks:
            assert 'All policy checks passed:' in task['stdout']
            assert task['exit_code'] == '0'
    else:
        for task in policy_check_tasks:
            assert '"eventOutcomeInformation": "fail"' in task['stdout']


@then('all policy check for originals tasks indicate {event_outcome}')
def step_impl(context, event_outcome):
    policy_check_tasks = [t for t in context.scenario.job['tasks'].values() if
                          t['stdout'].startswith(
                              'Running Check against policy ')]
    assert len(policy_check_tasks) > 0
    if event_outcome == 'pass':
        for task in policy_check_tasks:
            assert 'All policy checks passed:' in task['stdout']
            assert task['exit_code'] == '0'
    else:
        for task in policy_check_tasks:
            assert '"eventOutcomeInformation": "fail"' in task['stdout']


@then('all PREMIS policy-check-type validation events have eventOutcome ='
      ' {event_outcome}')
def step_impl(context, event_outcome):
    events = []
    for e in context.am_sel_cli.get_premis_events(context.am_sel_cli.get_mets(
            context.scenario.transfer_name,
            context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name))):
        if (e['event_type'] == 'validation' and
            e['event_detail'].startswith(MC_EVENT_DETAIL_PREFIX) and
            e['event_outcome_detail_note'].startswith(
                MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX)):
            events.append(e)
    assert len(events) > 0
    for e in events:
        assert e['event_outcome'] == event_outcome


@given('the user has ensured that there is a storage service space with'
       ' attributes {attributes}')
def step_impl(context, attributes):
    """Ensure that there is a storage space with the attributes in
    ``attributes``. These are :-delimited pairs delimited by ';'.
    """
    attributes = _parse_k_v_attributes(attributes)
    context.scenario.space_uuid = context.am_sel_cli.ensure_ss_space_exists(attributes)


@given('the user has ensured that there is a location in the GPG Space with'
       ' attributes {attributes}')
def step_impl(context, attributes):
    """Ensure that there is a storage location in the space referenced in
    ``context.scenario.space_uuid`` with the attributes in ``attributes``.
    These are :-delimited pairs delimited by ';'.
    """
    attributes = _parse_k_v_attributes(attributes)
    space_uuid = context.scenario.space_uuid
    # space_uuid = '974987cb-ec8b-40e6-adac-055d5418679e'
    context.scenario.location_uuid = \
        context.am_sel_cli.ensure_ss_location_exists(space_uuid, attributes)


@then('the downloaded AIP is not encrypted')
def step_impl(context):
    context.scenario.aip_path = context.am_sel_cli.decompress_aip(
        context.scenario.aip_path)
    assert os.path.isdir(context.scenario.aip_path)


###############################################################################
# HELPER FUNCS
###############################################################################


def ingest_ms_output_is(name, output, context):
    """Wait for the Ingest micro-service with name ``name`` to appear and
    assert that its output is ``output``.
    """
    context.scenario.sip_uuid = context.am_sel_cli.get_sip_uuid(
        context.scenario.transfer_name)
    context.scenario.job = context.am_sel_cli.parse_job(
        name, context.scenario.sip_uuid, 'sip')
    assert context.scenario.job.get('job_output') == output


def all_normalization_report_columns_are(column, expected_value, context):
    """Wait for the normalization report to be generated then assert that all
    values in ``column`` have value ``expected_value``.
    """
    normalization_report = context.am_sel_cli.parse_normalization_report(
        context.scenario.sip_uuid)
    for file_dict in normalization_report:
        if file_dict['file_format'] != 'None':
            assert file_dict[column] == expected_value


def transfer_path2name(transfer_path):
    """Return a transfer name, given a transfer path."""
    return os.path.split(transfer_path.replace('-', '_'))[1]


def get_policy_path(policy_file):
    return os.path.realpath(os.path.join(POLICIES_DIR, policy_file))


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
            uuid_val = context.scenario.sip_uuid = \
                context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name)
    return uuid_val


def initiate_transfer(context, transfer_path, accession_no=None):
    if transfer_path.startswith('~'):
        context.scenario.transfer_path = os.path.join(
            context.HOME, transfer_path[2:])
    else:
        context.scenario.transfer_path = os.path.join(
            context.TRANSFER_SOURCE_PATH, transfer_path)
    context.scenario.transfer_name = context.am_sel_cli.unique_name(
        transfer_path2name(transfer_path))
    context.scenario.transfer_uuid = context.am_sel_cli.start_transfer(
        context.scenario.transfer_path, context.scenario.transfer_name,
        accession_no=accession_no)


@when('the user removes the transfer')
def step_impl(context):
    context.am_sel_cli.remove_transfer(context.scenario.transfer_uuid)


@when('the user approves the full re-ingest transfer')
def step_impl(context):
    """After a full reingest, the user approves the new transfer. This is
    tricky because the UUID of the original transfer will be in ``context`` so
    we have to re-extract the UUID from the DOM.
    """
    context.scenario.transfer_uuid = context.am_sel_cli.get_transfer_uuid(
        context.scenario.transfer_name)
    logger.debug('transfer uuid for transfer named {} is {}'.format(
        context.scenario.transfer_name,
        context.scenario.transfer_uuid))
    context.execute_steps(
        'When the user waits for the "Approve standard transfer" decision point'
        ' to appear and chooses "Approve transfer" during transfer')


@then('the METS file records a deleted preservation derivative')
def step_impl(context):
    """Assert that the METS file records the deletion of a preservation
    derivative that was deleted because a new preservation derivative was made
    in its place, i.e., during a full reingest.

    1. There is a mets:file in a mets:fileGrp[@USE="deleted"]
    2. That deleted file has an amdSec containing a 'deletion' premis:eventType
       ancestor
    3. That deleted file's amdSec also has a 'derivation' relationship pointing
       to the UUID of the original file
    4. That original file has a mets:file element.
    """
    mets = get_mets_from_scenario(context)
    ns = context.am_sel_cli.mets_nsmap
    # Get the fileSec for the first deleted file
    file_sec_el = mets.find('mets:fileSec', ns)
    del_file_grp_el = mets.find('mets:fileSec/mets:fileGrp[@USE="deleted"]', ns)
    assert del_file_grp_el is not None
    del_file_el = del_file_grp_el.find('mets:file', ns)
    assert del_file_el is not None
    del_file_id = del_file_el.get('ID')
    del_file_admid = del_file_el.get('ADMID')
    # Get the amdSec for the deleted file
    del_file_amdsec_el = mets.find('mets:amdSec[@ID="{}"]'.format(del_file_admid), ns)
    assert del_file_amdsec_el is not None
    # Get the 'deletion' premis:eventType of the deleted file
    deletion_evt_type = None
    for evt_type_el in del_file_amdsec_el.findall('.//premis:eventType', ns):
        if evt_type_el.text.strip() == 'deletion':
            deletion_evt_type = True
            break
    assert deletion_evt_type is not None
    # Get the 'derivation' premis:relationship of the deleted file
    prm_rel_el = del_file_amdsec_el.find('.//premis:relationship', ns)
    assert prm_rel_el is not None
    prm_rel_type_el = prm_rel_el.find('premis:relationshipType', ns)
    assert prm_rel_type_el is not None
    assert prm_rel_type_el.text.strip() == 'derivation'
    source_uuid = prm_rel_el.find(
        'premis:relatedObjectIdentification/premis:relatedObjectIdentifierValue',
        ns).text.strip()
    # Get the original file mets:file element
    orig_file_el = mets.find(
        'mets:fileSec/mets:fileGrp[@USE="original"]/'
        'mets:file[@ID="file-{}"]'.format(source_uuid), ns)
    assert orig_file_el is not None


def _parse_k_v_attributes(attributes):
    """Parse a string of key-value attributes formatted like "key 1: value 1;
    key 2: value 2;".
    """
    return {pair.split(':')[0].strip(): pair.split(':')[1].strip() for
            pair in attributes.split(';') if pair.strip()}


@when('the user waits for {seconds} seconds')
def step_impl(context, seconds):
    time.sleep(int(seconds))
