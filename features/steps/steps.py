import os

from behave import when, then, given

MEDIA_CONCH_EVENT_DETAIL_PREFIX = 'program="MediaConch"'
MEDIA_CONCH_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX = \
    'MediaConch implementation check result:'


###############################################################################
# FEATURE: PRE-INGEST CONFORMANCE CHECK
###############################################################################


@given('directory {transfer_path} contains files that are all {file_validity}'
       ' .mkv')
def step_impl(context, transfer_path, file_validity):
    pass


@then('validation micro-service output is {microservice_output}')
def step_impl(context, microservice_output):
    context.job = context.am_sel_cli.parse_job(
        'Validate formats', context.transfer_uuid)
    assert context.job.get('job_output') == microservice_output


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


@when('the user edits the FPR rule to transcode .mov files to .mkv for access')
def step_impl(context):
    context.am_sel_cli.change_normalization_rule_command(
        'Access Generic MOV',
        'Transcoding to mkv with ffmpeg')


@when('a transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_path):
    context.transfer_path = os.path.join(context.TRANSFER_SOURCE_PATH, transfer_path)
    context.transfer_name = context.am_sel_cli.unique_name(
        transfer_path2name(transfer_path))
    context.transfer_uuid = context.am_sel_cli.start_transfer(
        context.transfer_path, context.transfer_name)


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
    for e in context.am_sel_cli.get_premis_events(context.am_sel_cli.get_mets(
            context.transfer_name,
            context.am_sel_cli.get_sip_uuid(context.transfer_name))):
        if (e['event_type'] == 'validation' and
            e['event_detail'].startswith(MEDIA_CONCH_EVENT_DETAIL_PREFIX) and
            e['event_outcome_detail_note'].startswith(
                MEDIA_CONCH_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX)):
            assert e['event_outcome'] == event_outcome


###############################################################################
# INGEST POLICY CHECK
###############################################################################

POLICIES_DIR = 'mediaconch-policies'

@given('MediaConch policy file {policy_file} is present in the local'
       ' mediaconch-policies/ directory')
def step_impl(context, policy_file):
    print(os.listdir('.'))


@given('directory {transfer_path} contains files that, when normalized, will'
       ' all {do_files_conform} to {policy_file}')
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@when('the user uploads the policy file {policy_file}')
def step_impl(context, policy_file):
    policy_path_relative = os.path.join(POLICIES_DIR, policy_file)
    here = os.path.dirname(os.path.realpath(__file__))
    policy_path = os.path.join(here, policy_path_relative)
    context.am_sel_cli.upload_policy(policy_path)


@then('policy checks for preservation derivatives micro-service output is'
      ' {microservice_output}')
def step_impl(context, microservice_output):
    name = 'Policy checks for preservation derivatives'
    ingest_ms_output_is(name, microservice_output, context)


@then('all PREMIS policy-check-type validation events have eventOutcome ='
      ' {event_outcome}')
def step_impl(context, event_outcome):
    # TODO: change dashboard migration so that policy-check-type validation
    # events are identifiable.
    for e in context.am_sel_cli.get_premis_events(context.am_sel_cli.get_mets(
            context.transfer_name,
            context.am_sel_cli.get_sip_uuid(context.transfer_name))):
        if (e['event_type'] == 'validation' and
                e['event_detail'].startswith(MEDIA_CONCH_EVENT_DETAIL_PREFIX)):
            print('event_outcome_detail_note: {}'.format(e['event_outcome_detail_note']))
            print('event_outcome: {}'.format(e['event_outcome']))


###############################################################################
# HELPER FUNCS
###############################################################################


def ingest_ms_output_is(name, output, context):
    """Wait for the Ingest micro-service with name ``name`` to appear and
    assert that its output is ``output``.
    """
    context.sip_uuid = context.am_sel_cli.get_sip_uuid(context.transfer_name)
    context.job = context.am_sel_cli.parse_job(name, context.sip_uuid, 'sip')
    assert context.job.get('job_output') == output


def all_normalization_report_columns_are(column, expected_value, context):
    """Wait for the normalization report to be generated then assert that all
    values in ``column`` have value ``expected_value``.
    """
    normalization_report = context.am_sel_cli.parse_normalization_report(
        context.sip_uuid)
    for file_dict in normalization_report:
        if file_dict['file_format'] != 'None':
            assert file_dict[column] == expected_value


def transfer_path2name(transfer_path):
    """Return a transfer name, given a transfer path."""
    return os.path.split(transfer_path.replace('-', '_'))[1]
