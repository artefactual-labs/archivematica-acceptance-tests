import filecmp
import json
import os
import pprint
import re

from behave import when, then, given

MC_EVENT_DETAIL_PREFIX = 'program="MediaConch"'
MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX = \
    'MediaConch implementation check result:'
MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX = \
    'MediaConch policy check result'
POLICIES_DIR = 'etc/mediaconch-policies'


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
    #raise Exception('fuckyou, microservice_name {}, choice {}, unit_type {}\n\nsteps:\n{}'.format(microservice_name, choice, unit_type, steps))
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
    #uuid_val = 'd0eaa220-a328-4559-83d8-fb2dea6538b5'
    #transfer_name = 'all_conform_policy_1477433177'
    print('downloading aip {} for transfer named {}'.format(uuid_val, transfer_name))
    context.scenario.aip_path = context.am_sel_cli.download_aip(
        transfer_name, uuid_val)


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
    from lxml import etree
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
    from lxml import etree
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
    # DEV DELETE
    #context.scenario.sip_uuid = 'ededf16f-5877-4d22-b6ba-28520f999bce'
    #context.scenario.transfer_name = 'BagTransfer_1478123709'
    uuid_val = get_uuid_val(context, 'sip')
    context.am_sel_cli.initiate_reingest(
        uuid_val, reingest_type=reingest_type)


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
                assert desc_el.text.strip() == value, '{} does not equal {}'.format(desc_el.text.strip(), value)
            elif relation == 'contains':
                assert value in desc_el.text.strip(), '{} does not substring-contain {}'.format(desc_el.text.strip(), value)
            elif relation == 'regex':
                assert re.search(value, desc_el.text.strip()), '{} does not contain regex {}'.format(desc_el.text.strip(), value)


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
       ' etc/mediaconch-policies/ directory')
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


@when('the user closes all {unit_type}')
def step_impl(context, unit_type):
    getattr(context.am_sel_cli, 'remove_all_' + unit_type)()


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
