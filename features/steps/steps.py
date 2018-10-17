"""General-purpose Steps."""

import logging
import time

from behave import when, then, given, use_step_matcher

from features.steps import utils


logger = logging.getLogger('amauat.steps')


# Givens
# ------------------------------------------------------------------------------

@given('the user waits for the "{microservice_name}" micro-service to complete'
       ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    utils.wait_for_micro_service_to_complete(context, microservice_name, unit_type)


@given('the user waits for the "{microservice_name}" decision point to appear'
       ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    utils.wait_for_decision_point_to_appear(
        context, microservice_name, unit_type)


@given('the user chooses "{choice}" at decision point "{decision_point}" during'
       ' {unit_type}')
def step_impl(context, choice, decision_point, unit_type):
    utils.make_choice(context, choice, decision_point, unit_type)


@given('the default processing config is in its default state')
def step_impl(context):
    context.execute_steps(
        'Given that the user has ensured that the default processing config is'
        ' in its default state')


@given('that the user has ensured that the default processing config is in its'
       ' default state')
def step_impl(context):
    context.am_user.browser.ensure_default_processing_config_in_default_state()


@given('the reminder to add metadata is enabled')
def step_impl(context):
    context.am_user.browser.set_processing_config_decision(
        decision_label='Reminder: add metadata if desired',
        choice_value='None')
    context.am_user.browser.save_default_processing_config()


@given('the processing config decision "{decision_label}" is set to'
       ' "{choice_value}"')
def step_impl(context, decision_label, choice_value):
    context.am_user.browser.set_processing_config_decision(
        decision_label=decision_label,
        choice_value=choice_value)
    context.am_user.browser.save_default_processing_config()


@given('a transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_path):
    context.execute_steps(
        'When a transfer is initiated on directory {}'.format(transfer_path))


@given('the user has ensured that there is a storage service space with'
       ' attributes {attributes}')
def step_impl(context, attributes):
    """Ensure that there is a storage space with the attributes in
    ``attributes``. These are :-delimited pairs delimited by ';'.
    """
    attributes = utils.parse_k_v_attributes(attributes)
    context.scenario.space_uuid = context.am_user.browser.ensure_ss_space_exists(
        attributes)


@given('the user has disabled the default transfer backlog location')
def step_impl(context):
    context.am_user.browser.disable_default_transfer_backlog()


@given('a fully automated default processing config')
def step_impl(context):
    """Note: step description should be changed. This fully automates the
    creation of a DIP and an AIP in the context of testing the PID binding
    feature.
    """
    context.execute_steps(
        'Given that the user has ensured that the default processing config is'
        ' in its default state\n'
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Identify using Fido"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
        ' single SIP and continue processing"\n'
        'And the processing config decision "Select file format identification'
        ' command (Ingest)" is set to "Identify using Fido"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation and access"\n'
        'And the processing config decision "Approve normalization" is set to'
        ' "Yes"\n'
        'And the processing config decision "Select file format identification'
        ' command (Submission documentation & metadata)" is set to'
        ' "Identify using Fido"\n'
        'And the processing config decision "Perform policy checks on'
        ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
        ' derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "No"\n'
        'And the processing config decision "Document empty directories"'
        ' is set to "No"\n'
        'And the processing config decision "Generate thumbnails" is set to'
        ' "No"\n'
        'And the processing config decision "Upload DIP" is set to'
        ' "Do not upload DIP"\n'
        'And the processing config decision "Store DIP" is set to'
        ' "Do not store"\n'
        'And the processing config decision "Store AIP" is set to "None"\n'
    )


@given('the default processing config is set to automate a transfer through to'
       ' "Store AIP"')
def step_impl(context):
    context.execute_steps(
        'Given the default processing config is in its default state\n'
        'And the processing config decision "Assign UUIDs to directories" is'
        ' set to "No"\n'
        'And the processing config decision "Document empty directories" is'
        ' set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Identify using Siegfried"\n'
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "No"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
        ' single SIP and continue processing"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"\n'
        'And the processing config decision "Approve normalization" is set to'
        ' "Yes"\n'
        'And the processing config decision "Perform policy checks on'
        ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
        ' derivatives" is set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Submission documentation & metadata)" is set to'
        ' "Identify using Siegfried"\n'
        'And the processing config decision "Bind PIDs" is set to "No"'
    )


@given('a default processing config that creates and stores an AIP')
def step_impl(context):
    context.execute_steps(
        'Given the default processing config is in its default state\n'
        'And the processing config decision "Document empty directories" is'
        ' set to "No"\n'
        'And the processing config decision "Assign UUIDs to directories" is'
        ' set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Identify using Siegfried"\n'
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "No"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
        ' single SIP and continue processing"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"\n'
        'And the processing config decision "Approve normalization" is set to'
        ' "Yes"\n'
        'And the processing config decision "Perform policy checks on'
        ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
        ' derivatives" is set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Submission documentation & metadata)" is set to'
        ' "Identify using Siegfried"\n'
        'And the processing config decision "Bind PIDs" is set to "No"\n'
        'And the processing config decision "Store AIP" is set to "Yes"\n'
        'And the processing config decision "Store AIP location" is set to'
        ' "Default location"\n'
    )


@given('a default processing config that gets a transfer to the "Create SIP(s)"'
       ' decision point')
def step_impl(context):
    context.execute_steps(
        'Given the default processing config is in its default state\n'
        'And the processing config decision "Assign UUIDs to directories" is'
        ' set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Identify using Siegfried"\n'
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "No"\n'
    )


# Whens
# ------------------------------------------------------------------------------

@when('the user waits for the "{microservice_name}" micro-service to complete'
      ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    utils.wait_for_micro_service_to_complete(context, microservice_name,
                                             unit_type)


@when('the user waits for the "{microservice_name}" decision point to appear'
      ' during {unit_type}')
def step_impl(context, microservice_name, unit_type):
    utils.wait_for_decision_point_to_appear(
        context, microservice_name, unit_type)


@when('the user waits for the "{microservice_name}" decision point to appear'
      ' and chooses "{choice}" during {unit_type}')
def step_impl(context, microservice_name, choice, unit_type):
    utils.wait_for_decision_point_to_appear(
        context, microservice_name, unit_type)
    utils.make_choice(context, choice, microservice_name, unit_type)


@when('the user chooses "{choice}" at decision point "{decision_point}" during'
      ' {unit_type}')
def step_impl(context, choice, decision_point, unit_type):
    utils.make_choice(context, choice, decision_point, unit_type)


@when('the user waits for the AIP to appear in archival storage')
def step_impl(context):
    uuid_val = utils.get_uuid_val(context, 'sip')
    context.am_user.browser.wait_for_aip_in_archival_storage(uuid_val)
    time.sleep(context.am_user.medium_wait)


@when('the user searches for the AIP UUID in the Storage Service')
def step_impl(context):
    time.sleep(context.am_user.optimistic_wait)
    the_aip_uuid = utils.get_uuid_val(context, 'sip')
    context.scenario.aip_search_results = (
        context.am_user.browser.search_for_aip_in_storage_service(the_aip_uuid))


use_step_matcher('re')


@when('the user downloads the (?P<aip_description>.*)AIP')
def step_impl(context, aip_description):
    aip_description = aip_description.strip()
    if aip_description:
        aip_description = aip_description + '_aip'
        aip_attr = utils.aip_descr_to_attr(aip_description)
        uuid_val = getattr(context.scenario, aip_attr)
    else:
        uuid_val = utils.get_uuid_val(context, 'sip')
    transfer_name = context.scenario.transfer_name
    context.scenario.aip_path = context.am_user.api.download_aip(
        transfer_name, uuid_val, context.am_user.browser.ss_api_key)
    attr_name = aip_description.replace(' ', '')
    logger.info('setting attribute %s to %s',
                attr_name, context.scenario.aip_path)
    setattr(context.scenario, attr_name, context.scenario.aip_path)


use_step_matcher('parse')


@when('the user downloads the AIP pointer file')
def step_impl(context):
    uuid_val = utils.get_uuid_val(context, 'sip')
    # For some reason, it is necessary to pause a moment before downloading the
    # AIP pointer file because otherwise, e.g., after a re-ingest, it can be
    # out of date. See @reencrypt-different-key.
    time.sleep(context.am_user.pessimistic_wait)
    context.scenario.aip_pointer_path = app = (
        context.am_user.api.download_aip_pointer_file(
            uuid_val, context.am_user.browser.ss_api_key))
    logger.info('downloaded AIP pointer file for AIP %s to %s', uuid_val,
                app)


@when('the user downloads the {aip_description} pointer file')
def step_impl(context, aip_description):
    aip_attr = utils.aip_descr_to_attr(aip_description)
    aip_ptr_attr = utils.aip_descr_to_ptr_attr(aip_description)
    aip_uuid = getattr(context.scenario, aip_attr)
    time.sleep(context.am_user.pessimistic_wait)
    setattr(context.scenario, aip_ptr_attr,
            context.am_user.api.download_aip_pointer_file(
                aip_uuid, context.am_user.browser.ss_api_key))
    logger.info('downloaded AIP pointer file for %s AIP %s to %s',
                aip_description, aip_uuid,
                getattr(context.scenario, aip_ptr_attr))


@when('the user waits for the DIP to appear in transfer backlog')
def step_impl(context):
    uuid_val = utils.get_uuid_val(context, 'transfer')
    context.am_user.browser.wait_for_dip_in_transfer_backlog(uuid_val)


@when('the user decompresses the AIP')
def step_impl(context):
    context.scenario.aip_path = context.am_user.decompress_aip(
        context.scenario.aip_path)


@when('the user adds metadata')
def step_impl(context):
    context.am_user.browser.add_dummy_metadata(utils.get_uuid_val(context, 'sip'))


@when('the user initiates a {reingest_type} re-ingest on the AIP')
def step_impl(context, reingest_type):
    uuid_val = utils.get_uuid_val(context, 'sip')
    context.am_user.browser.initiate_reingest(
        uuid_val, reingest_type=reingest_type)


@when('standard AIP-creation decisions are made')
def step_impl(context):
    """Standard AIP-creation decisions after a transfer is initiated and up
    until (but not including) the "Store AIP location" decision:

    - file identification via Siegfried
    - create SIP
    - normalize for preservation
    - store AIP
    """
    context.execute_steps(
        'When the user waits for the "Assign UUIDs to directories?" decision'
        ' point to appear and chooses "No" during transfer\n'
        'And the user waits for the "Select file format identification command"'
        ' decision point to appear and chooses "Identify using Siegfried" during'
        ' transfer\n'
        'And the user waits for the "Perform policy checks on originals?"'
        ' decision point to appear and chooses "No" during transfer\n'
        'And the user waits for the "Create SIP(s)" decision point to appear'
        ' and chooses "Create single SIP and continue processing" during'
        ' transfer\n'
        'And the user waits for the "Normalize" decision point to appear and'
        ' chooses "Normalize for preservation" during ingest\n'
        'And the user waits for the "Approve normalization (review)" decision'
        ' point to appear and chooses "Approve" during ingest\n'
        'And the user waits for the "Perform policy checks on preservation'
        ' derivatives?" decision point to appear and chooses "No" during'
        ' ingest\n'
        'And the user waits for the "Perform policy checks on access'
        ' derivatives?" decision point to appear and chooses "No" during'
        ' ingest\n'
        'And the user waits for the "Select file format identification'
        ' command|Process submission documentation" decision point to'
        ' appear and chooses "Identify using Siegfried" during ingest\n'
        'And the user waits for the "Bind PIDs?" decision point to appear and'
        ' chooses "No" during ingest\n'
        'And the user waits for the "Document empty directories?" decision'
        ' point to appear and chooses "No" during ingest\n'
        'And the user waits for the "Store AIP (review)" decision point to'
        ' appear and chooses "Store AIP" during ingest'
    )


@when('a transfer is initiated on directory {transfer_path} with accession'
      ' number {accession_no}')
def step_impl(context, transfer_path, accession_no):
    context.scenario.accession_no = accession_no
    utils.initiate_transfer(context, transfer_path, accession_no=accession_no)


@when('a {transfer_type} transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_type, transfer_path):
    utils.initiate_transfer(context, transfer_path, transfer_type=transfer_type)


@when('a transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_path):
    utils.initiate_transfer(context, transfer_path)


@when('the user closes all {unit_type}')
def step_impl(context, unit_type):
    getattr(context.am_user.browser, 'remove_all_' + unit_type)()


@when('the AIP is deleted')
def step_impl(context):
    uuid_val = utils.get_uuid_val(context, 'sip')
    context.am_user.browser.request_aip_delete(uuid_val)
    context.am_user.browser.approve_aip_delete_request(uuid_val)


@when('the user performs a metadata-only re-ingest on the AIP')
def step_impl(context):
    """Perform a metadata-only AIP re-ingest on the AIP referenced in
    ``context.scenario`` and wait for the re-ingested AIP to appear in archival
    storage.
    """
    context.execute_steps(
        'When the user initiates a metadata-only re-ingest on the AIP\n'
        'And the user waits for the "Approve AIP reingest" decision point to'
        ' appear and chooses "Approve AIP reingest" during ingest\n'
        'And the user waits for the "Normalize" decision point to appear and'
        ' chooses "Do not normalize" during ingest\n'
        'And the user waits for the "Perform policy checks on preservation'
        ' derivatives?" decision point to appear and chooses "No" during'
        ' ingest\n'
        'And the user waits for the "Perform policy checks on access'
        ' derivatives?" decision point to appear and chooses "No" during'
        ' ingest\n'
        'And the user waits for the "Reminder: add metadata if desired"'
        ' decision point to appear during ingest\n'
        'And the user adds metadata\n'
        'And the user chooses "Continue" at decision point "Reminder: add'
        ' metadata if desired" during ingest\n'
        'And the user waits for the "Select file format identification'
        ' command|Process submission documentation" decision point to appear'
        ' and chooses "Identify using Fido" during ingest\n'
        'And the user waits for the "Bind PIDs?" decision point to appear'
        ' and chooses "No" during ingest\n'
        'And the user waits for the "Document empty directories?" decision'
        ' point to appear and chooses "No" during ingest\n'
        'And the user waits for the "Store AIP (review)" decision point to'
        ' appear and chooses "Store AIP" during ingest\n'
        'And the user waits for the "Store AIP location" decision point to'
        ' appear and chooses "Store AIP Encrypted in standard Archivematica'
        ' Directory" during ingest\n'
        'And the user waits for the AIP to appear in archival storage'
    )


# Thens
# ------------------------------------------------------------------------------

@then('the "{microservice_name}" micro-service output is'
      ' "{microservice_output}" during {unit_type}')
def step_impl(context, microservice_name, microservice_output, unit_type):
    unit_type = utils.get_normalized_unit_type(unit_type)
    uuid_val = utils.get_uuid_val(context, unit_type)
    context.scenario.job = context.am_user.browser.parse_job(
        microservice_name, uuid_val, unit_type=unit_type)
    assert context.scenario.job.get('job_output') == microservice_output
