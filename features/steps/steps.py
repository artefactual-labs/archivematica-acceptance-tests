import filecmp
import json
import logging
from lxml import etree
import os
import pprint
import re
import tarfile
import time

from behave import when, then, given, use_step_matcher


MC_EVENT_DETAIL_PREFIX = 'program="MediaConch"'
MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX = \
    'MediaConch implementation check result:'
MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX = \
    'MediaConch policy check result'
POLICIES_DIR = 'etc/mediaconch-policies'
GPG_KEYS_DIR = 'etc/gpgkeys'

STDRD_GPG_TB_REL_PATH = (
    'var/archivematica/sharedDirectory/www/AIPsStore/transferBacklogEncrypted')


logger = logging.getLogger(__file__)
log_filename, _ = os.path.splitext(os.path.basename(__file__))
log_filename = log_filename + '.log'
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_filename)
handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


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
                          ' complete during {}'.format(microservice_name,
                                                       unit_type))


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
                          ' appear during {}'.format(microservice_name,
                                                     unit_type))


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
                          ' during {}'.format(choice, decision_point,
                                              unit_type))


@when('the user waits for the AIP to appear in archival storage')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'sip')
    context.am_sel_cli.wait_for_aip_in_archival_storage(uuid_val)


@when('the user searches for the AIP UUID in the Storage Service')
def step_impl(context):
    the_aip_uuid = get_uuid_val(context, 'sip')
    context.scenario.aip_search_results = (
        context.am_sel_cli.search_for_aip_in_storage_service(the_aip_uuid))


@then('the master AIP and its replica are returned by the search')
def step_impl(context):
    """Assert that ``context.scenario.aip_search_results`` is a list of exactly
    two dicts, one of which represents "the master AIP" (whose UUID is in
    ``context.scenariosip_uuid``) and the other representing the replica AIP.
    Store both AIP representations in ``context.scenario``.
    """
    the_aip_uuid = get_uuid_val(context, 'sip')
    search_results = context.scenario.aip_search_results
    assert len(search_results) == 2
    the_aips = [dct for dct in search_results if dct['uuid'] == the_aip_uuid]
    not_the_aips = [dct for dct in search_results
                    if dct['uuid'] != the_aip_uuid]
    assert len(the_aips) == 1
    assert len(not_the_aips) == 1
    the_aip = the_aips[0]
    replica = not_the_aips[0]
    replica_uuid = replica['uuid']
    assert the_aip['replicas'] == replica['uuid']
    assert replica['is_replica_of'] == the_aip['uuid']
    assert (set([x.strip() for x in replica['actions'].split()]) ==
            set(['Download']))
    assert (set([x.strip() for x in the_aip['actions'].split()]) ==
            set(['Download', 'Re-ingest']))
    context.scenario.master_aip_uuid = the_aip_uuid
    context.scenario.replica_aip_uuid = replica_uuid


def aip_descr_to_attr(aip_description):
    return aip_description.lower().strip().replace(' ', '_') + '_uuid'


def aip_descr_to_ptr_attr(aip_description):
    return aip_description.lower().strip().replace(' ', '_') + '_ptr'


def get_event_attr(event_type):
    return '{}_event_uuid'.format(event_type)


use_step_matcher('re')


@when('the user downloads the (?P<aip_description>.*)AIP')
def step_impl(context, aip_description):
    aip_description = aip_description.strip()
    if aip_description:
        aip_description = aip_description + '_aip'
        aip_attr = aip_descr_to_attr(aip_description)
        uuid_val = getattr(context.scenario, aip_attr)
    else:
        uuid_val = get_uuid_val(context, 'sip')
    transfer_name = context.scenario.transfer_name
    context.scenario.aip_path = context.am_sel_cli.download_aip(
        transfer_name, uuid_val)


use_step_matcher('parse')


@when('the user downloads the AIP pointer file')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'sip')
    # FOR DEV
    # uuid_val = 'c20be1aa-0e7a-434e-a67d-07978360437c'
    # context.scenario.transfer_name = 'BagTransfer_1506466171'

    # For some reason, it is necessary to pause a moment before downloading the
    # AIP pointer file because otherwise, e.g., after a re-ingest, it can be
    # out of date. See @reencrypt-different-key.
    time.sleep(5)
    context.scenario.aip_pointer_path = app = (
        context.am_sel_cli.download_aip_pointer_file(
            uuid_val))
    logger.info('downloaded AIP pointer file for AIP %s to %s', uuid_val, app)


@when('the user downloads the {aip_description} pointer file')
def step_impl(context, aip_description):
    aip_attr = aip_descr_to_attr(aip_description)
    aip_ptr_attr = aip_descr_to_ptr_attr(aip_description)
    aip_uuid = getattr(context.scenario, aip_attr)
    time.sleep(5)
    setattr(context.scenario, aip_ptr_attr,
            context.am_sel_cli.download_aip_pointer_file(aip_uuid))
    logger.info('downloaded AIP pointer file for %s AIP %s to %s',
                aip_description, aip_uuid, getattr(context.scenario, aip_ptr_attr))


@then('the {aip_description} pointer file contains a PREMIS:OBJECT with a'
      ' derivation relationship pointing to the {second_aip_description} and'
      ' the {event_type} PREMIS:EVENT')
def step_impl(context, aip_description, second_aip_description, event_type):
    aip_ptr_attr = aip_descr_to_ptr_attr(aip_description)
    pointer_path = getattr(context.scenario, aip_ptr_attr)
    aip_attr = aip_descr_to_attr(aip_description)
    aip_uuid = getattr(context.scenario, aip_attr)
    second_aip_attr = aip_descr_to_attr(second_aip_description)
    second_aip_uuid = getattr(context.scenario, second_aip_attr)
    event_uuid_attr = get_event_attr(event_type)
    event_uuid = getattr(context.scenario, event_uuid_attr)

    with open(pointer_path) as filei:
        doc = etree.parse(filei)
        premis_object_el = doc.find(
            './/mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
            context.am_sel_cli.mets_nsmap)
        premis_relationship = premis_object_el.find(
            'mets:xmlData/premis:object/premis:relationship',
            context.am_sel_cli.mets_nsmap)
        premis_relationship_type = premis_relationship.find(
            'premis:relationshipType',
            context.am_sel_cli.mets_nsmap).text.strip()
        assert premis_relationship_type == 'derivation'
        premis_related_object_uuid = premis_relationship.find(
            'premis:relatedObjectIdentification/'
            'premis:relatedObjectIdentifierValue',
            context.am_sel_cli.mets_nsmap).text.strip()
        assert second_aip_uuid == premis_related_object_uuid
        premis_related_event_uuid = premis_relationship.find(
            'premis:relatedEventIdentification/'
            'premis:relatedEventIdentifierValue',
            context.am_sel_cli.mets_nsmap).text.strip()
        assert event_uuid == premis_related_event_uuid


@then('the {aip_description} pointer file contains a(n) {event_type}'
      ' PREMIS:EVENT')
def step_impl(context, aip_description, event_type):
    aip_ptr_attr = aip_descr_to_ptr_attr(aip_description)
    pointer_path = getattr(context.scenario, aip_ptr_attr)
    event_uuid = assert_pointer_premis_event(
        context, pointer_path, event_type, in_evt_out=['success'])
    event_uuid_attr = get_event_attr(event_type)
    setattr(context.scenario, event_uuid_attr, event_uuid)


def assert_pointer_premis_event(context, mets_path, event_type, in_evt_dtl=None,
                                in_evt_out=None, in_evt_out_dtl_nt=None):
    """Make assertions about the PREMIS event of premis:eventType
    ``event_type`` in the METS pointer file at ``mets_path``. Minimally assert
    that such an event exists. The optional params should hold lists of strings
    that are all expected to be in eventDetail, eventOutcome, and
    eventOutcomeDetailNote, respectively. Return the UUID of the relevant event.
    """
    with open(mets_path) as filei:
        doc = etree.parse(filei)
        premis_event = None
        for premis_event_el in doc.findall(
                './/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]',
                context.am_sel_cli.mets_nsmap):
            premis_event_type_el = premis_event_el.find(
                'mets:xmlData/premis:event/premis:eventType',
                context.am_sel_cli.mets_nsmap)
            if premis_event_type_el.text.strip() == event_type:
                premis_event = premis_event_el
                break
        assert premis_event is not None
        premis_event_uuid = premis_event.find(
            'mets:xmlData/premis:event/premis:eventIdentifier/'
            'premis:eventIdentifierValue',
            context.am_sel_cli.mets_nsmap).text.strip()
        if in_evt_dtl:
            in_evt_dtl = in_evt_dtl or []
            premis_event_detail = premis_event.find(
                'mets:xmlData/premis:event/premis:eventDetail',
                context.am_sel_cli.mets_nsmap).text.strip()
            for substr in in_evt_dtl:
                assert substr in premis_event_detail
        if in_evt_out:
            in_evt_out = in_evt_out or []
            premis_event_out = premis_event.find(
                'mets:xmlData/premis:event/premis:eventOutcomeInformation/'
                'premis:eventOutcome',
                context.am_sel_cli.mets_nsmap).text.strip()
            for substr in in_evt_out:
                assert substr in premis_event_out
        if in_evt_out_dtl_nt:
            in_evt_out_dtl_nt = in_evt_out_dtl_nt or []
            premis_event_od_note = premis_event.find(
                'mets:xmlData/premis:event/premis:eventOutcomeInformation/'
                'premis:eventOutcomeDetail/premis:eventOutcomeDetailNote',
                context.am_sel_cli.mets_nsmap).text.strip()
            for substr in in_evt_out_dtl_nt:
                assert substr in premis_event_od_note
        return premis_event_uuid


@then('the pointer file contains a PREMIS:EVENT element for the encryption event')
def step_impl(context):
    """This asserts that the pointer file contains a ``<mets:mdWrap
    MDTYPE="PREMIS:EVENT">`` element with the following type of descendants:
    - <mets:xmlData>
    - <premis:eventType>encryption</premis:eventType>
    - <premis:eventDetail>program=gpg (GPG); version=1.4.16; python-gnupg; version=0.4.0</premis:eventDetail>
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
        # <premis:eventDetail>program=gpg (GPG); version=1.4.16; python-gnupg; version=0.4.0</premis:eventDetail>
        premis_event_detail = premis_event.find(
            'mets:xmlData/premis:event/premis:eventDetail',
            context.am_sel_cli.mets_nsmap).text
        assert 'GPG' in premis_event_detail
        assert 'version=' in premis_event_detail
        premis_event_od_note = premis_event.find(
            'mets:xmlData/premis:event/premis:eventOutcomeInformation/'
            'premis:eventOutcomeDetail/premis:eventOutcomeDetailNote',
            context.am_sel_cli.mets_nsmap).text.strip()
        assert 'Status="encryption ok"' in premis_event_od_note


use_step_matcher('re')


@then('the (?P<aip_description>.*)pointer file contains a mets:transformFile element'
      ' for the encryption event')
def step_impl(context, aip_description):
    """Makes the following assertions about the first (and presumably only)
    <mets:file> element in the AIP's pointer file:
    1. the xlink:href attribute's value of <mets:FLocat> is a path with
       extension .gpg
    2. the decompression-type <mets:transformFile> has TRANSFORMORDER 2
    3. there is a new <mets:transformFile> element for the decryption event
       needed to get at this AIP.
    4. <premis:compositionLevel> incremented
    5. <premis:inhibitors> added
    """
    aip_description = aip_description.strip()
    if aip_description:
        aip_ptr_attr = aip_descr_to_ptr_attr(aip_description)
        pointer_path = getattr(context.scenario, aip_ptr_attr)
    else:
        pointer_path = context.scenario.aip_pointer_path
    ns = context.am_sel_cli.mets_nsmap
    assert_pointer_transform_file_encryption(pointer_path, ns)



@then('the (?P<aip_description>.*)AIP on disk is encrypted')
def step_impl(context, aip_description):
    """Asserts that the AIP on the server (pointed to within the AIP pointer
    file stored in context.scenario.aip_pointer_path) is encrypted. To do this,
    we use scp to copy the remote AIP to a local directory and then we attempt
    to decompress it and expect to fail.
    """
    assert get_aip_is_encrypted(context, aip_description) is True


@then('the (?P<aip_description>.*)AIP on disk is not encrypted')
def step_impl(context, aip_description):
    """Asserts that the AIP is NOT encrypted."""
    assert get_aip_is_encrypted(context, aip_description) is False


def get_aip_is_encrypted(context, aip_description):
    aip_description = aip_description.strip()
    if aip_description:
        aip_ptr_attr = aip_descr_to_ptr_attr(aip_description + '_aip')
        pointer_path = getattr(context.scenario, aip_ptr_attr)
    else:
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
            logger.warning(
                'Unable to copy file {} from the server to the local file'
                ' system. Server is not accessible via SSH. Abandoning'
                ' attempt to assert that the AIP on disk is'
                ' encrypted.'.format(xlink_href))
            return
        elif aip_local_path is False:
            logger.warning(
                'Unable to copy file {} from the server to the local file'
                ' system. Attempt to scp the file failed. Abandoning attempt'
                ' to assert that the AIP on disk is'
                ' encrypted.'.format(xlink_href))
            return
    aip_local_path = context.am_sel_cli.decompress_package(aip_local_path)
    # ``decompress_package`` will attempt to decompress the package with 7z and
    # we expect it to fail because the AIP file is encrypted with GPG.
    aip_is_encrypted = aip_local_path is None
    return aip_is_encrypted


use_step_matcher('parse')


@then('the transfer on disk is encrypted')
def step_impl(context):
    """Asserts that the DIP on the server (pointed to within the AIP pointer
    file stored in context.scenario.aip_pointer_path) is encrypted. To do this,
    we use scp to copy the remote AIP to a local directory and then we attempt
    to decompress it and expect to fail.
    """
    path_on_disk = '/{}/originals/{}-{}'.format(
        STDRD_GPG_TB_REL_PATH,
        context.scenario.transfer_name,
        context.scenario.transfer_uuid)
    logger.info('expecting encrypted transfer to be at %s on server',
                path_on_disk)
    dip_local_path = context.am_sel_cli.scp_server_file_to_local(
        path_on_disk)
    if dip_local_path is None:
        logger.info(
            'Unable to copy file {} from the server to the local file'
            ' system. Server is not accessible via SSH. Abandoning'
            ' attempt to assert that the DIP on disk is'
            ' encrypted.'.format(path_on_disk))
        return
    elif dip_local_path is False:
        logger.info(
            'Unable to copy file {} from the server to the local file'
            ' system. Attempt to scp the file failed. Abandoning attempt'
            ' to assert that the DIP on disk is'
            ' encrypted.'.format(path_on_disk))
        return
    assert not os.path.isdir(dip_local_path)
    assert not tarfile.is_tarfile(dip_local_path)


@when('the user waits for the DIP to appear in transfer backlog')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'transfer')
    context.am_sel_cli.wait_for_dip_in_transfer_backlog(uuid_val)


@then('the uncompressed AIP on disk at {aips_store_path} is encrypted')
def step_impl(context, aips_store_path):
    """
    """
    tmp = context.scenario.sip_uuid.replace('-', '')
    parts = [tmp[i:i + 4] for i in range(0, len(tmp), 4)]
    subpath = '/'.join(parts)
    aip_server_path = '{}{}/{}-{}'.format(
        aips_store_path, subpath, context.scenario.transfer_name,
        context.scenario.sip_uuid)
    aip_local_path = context.am_sel_cli.scp_server_file_to_local(
        aip_server_path)
    if aip_local_path is None:
        logger.info(
            'Unable to copy file {} from the server to the local file'
            ' system. Server is not accessible via SSH. Abandoning'
            ' attempt to assert that the AIP on disk is'
            ' encrypted.'.format(aip_server_path))
        return
    elif aip_local_path is False:
        logger.info(
            'Unable to copy file {} from the server to the local file'
            ' system. Attempt to scp the file failed. Abandoning attempt'
            ' to assert that the AIP on disk is'
            ' encrypted.'.format(aip_server_path))
        return
    assert not os.path.isdir(aip_local_path)
    assert not tarfile.is_tarfile(aip_local_path)


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
        assert os.path.isfile(aip_policy_path), (
            'There is no MediaConch policy file in the AIP at'
            ' {}!'.format(aip_policy_path))
        with open(original_policy_path) as filei:
            original_policy = filei.read().strip()
        with open(aip_policy_path) as filei:
            aip_policy = filei.read().strip()
        assert aip_policy == original_policy, (
            'The local policy file at {} is different from the one in the AIP'
            ' at {}'.format(original_policy_path, aip_policy_path))
        # assert filecmp.cmp(original_policy_path, aip_policy_path), (
        #     'The local policy file at {} is different from the one in the AIP'
        #     ' at {}'.format(original_policy_path, aip_policy_path))
    else:
        assert not os.path.isfile(aip_policy_path), (
            'There is a MediaConch policy file in the AIP at {} but there'
            ' shouldn\'t be!'.format( aip_policy_path))


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
        assert os.path.isfile(aip_policy_path), (
            'There is no MediaConch policy file in the AIP at'
            ' {}!'.format(aip_policy_path))
        with open(original_policy_path) as filei:
            original_policy = filei.read().strip()
        with open(aip_policy_path) as filei:
            aip_policy = filei.read().strip()
        assert aip_policy == original_policy, (
            'The local policy file at {} is different from the one in the AIP'
            ' at {}'.format(original_policy_path, aip_policy_path))
        # assert filecmp.cmp(original_policy_path, aip_policy_path)
    else:
        assert not os.path.isfile(aip_policy_path), (
            'There is a MediaConch policy file in the AIP at {} but there'
            ' shouldn\'t be!'.format( aip_policy_path))


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
    assert os.path.isdir(aip_policy_outputs_path), (
        'We expected {} to be a directory but it either does not exist or it is'
        ' not a directory'.format(aip_policy_outputs_path))
    contents = os.listdir(aip_policy_outputs_path)
    assert len(contents) > 0
    file_paths = [x for x in
                  [os.path.join(aip_policy_outputs_path, y) for y in contents]
                  if os.path.isfile(x) and os.path.splitext(x)[1] == '.xml']
    assert len(file_paths) > 0, (
        'There are no files in dir {}!'.format(aip_policy_outputs_path))
    for fp in file_paths:
        with open(fp) as f:
            doc = etree.parse(f)
            root_tag = doc.getroot().tag
            expected_root_tag = '{https://mediaarea.net/mediaconch}MediaConch'
            assert root_tag == expected_root_tag, (
                'The root tag of file {} was expected to be {} but was actually'
                ' {}'.format(fp, expected_root_tag, root_tag))


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
    file_paths = [x for x in
                  [os.path.join(aip_policy_outputs_path, y) for y in contents]
                  if os.path.isfile(x) and
                  os.path.splitext(x)[1] == '.xml']
    assert len(file_paths) > 0, (
        'There are no files in dir {}!'.format(aip_policy_outputs_path))
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


@when('standard AIP-creation decisions are made')
def step_impl(context):
    """Standard AIP-creation decisions after a transfer is initiated and up
    until (but not including) the "Store AIP location" decision:

    - file identification via Fido
    - create SIP
    - normalize for preservation
    - store AIP
    """
    context.execute_steps(
        'When the user waits for the "Assign UUIDs to directories?" decision'
            ' point to appear and chooses "No" during transfer\n'
        'And the user waits for the "Select file format identification command"'
            ' decision point to appear and chooses "Identify using Fido" during'
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
            ' appear and chooses "Identify using Fido" during ingest\n'
        'And the user waits for the "Bind PIDs?" decision point to appear and'
            ' chooses "No" during ingest\n'
        'And the user waits for the "Store AIP (review)" decision point to'
            ' appear and chooses "Store AIP" during ingest'
    )


@given('the default processing config is in its default state')
def step_impl(context):
    context.execute_steps(
        'Given that the user has ensured that the default processing config is'
        ' in its default state')


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


@then('in the METS file the metsHdr element has {quant} dmdSec next sibling'
      ' element(s)')
def step_impl(context, quant):
    mets = get_mets_from_scenario(context)
    mets_dmd_sec_els = mets.findall('.//mets:dmdSec', context.am_sel_cli.mets_nsmap)
    try:
        quant = {
            'no': 0,
            'zero': 0,
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4,
            'five': 5,
            'six': 6,
            'seven': 7,
            'eight': 8,
            'nine': 9,
        }[quant]
    except KeyError:
        raise ArchivematicaSeleniumStepsError('Unable to recognize the'
            ' quantifier {} when checking for dmdSec elements in the METS'
            ' file'.format(quant))
    else:
        assert len(mets_dmd_sec_els) == quant


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
    context.scenario.accession_no = accession_no
    initiate_transfer(context, transfer_path, accession_no=accession_no)


@when('a {transfer_type} transfer is initiated on directory {transfer_path}')
def step_impl(context, transfer_type, transfer_path):
    initiate_transfer(context, transfer_path, transfer_type=transfer_type)


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


@given('remote directory {dir_path} contains a hierarchy of subfolders'
       ' containing digital objects')
def step_impl(context, dir_path):
    """Get a local copy of ``dir_path`` and assert that it contains at least
    one subfolder (subdirectory) and at least one file in a subfolder and then
    record the directory structure in ``context``.
    """
    if dir_path.startswith('~/'):
        dir_path = dir_path[2:]

    dir_is_zipped = bool(os.path.splitext(dir_path)[1])
    if dir_is_zipped:
        local_path = context.am_sel_cli.scp_server_file_to_local(
            dir_path)
    else:
        local_path = context.am_sel_cli.scp_server_dir_to_local(
            dir_path)
    if local_path is None:
        msg = (
            'Unable to copy item {} from the server to the local file'
            ' system. Server is not accessible via SSH.'.format(dir_path))
        logger.warning(msg)
        raise Exception(msg)
    elif local_path is False:
        msg = (
            'Unable to copy item {} from the server to the local file'
            ' system. Attempt to scp the file failed.'.format(dir_path))
        logger.warning(msg)
        raise Exception(msg)
    dir_local_path = local_path
    if dir_is_zipped:
        dir_local_path = context.utils.unzip(local_path)
    assert os.path.isdir(dir_local_path)
    non_root_paths = []
    non_root_file_paths = []

    # These are the names of the files that Archivematica will remove by
    # default. See MCPClient/lib/settings/common.py,
    # clientScripts/removeHiddenFilesAndDirectories.py, and
    # clientScripts/removeUnneededFiles.py.
    to_be_removed_files = [
        e.strip() for e in 'Thumbs.db, Icon, Icon\r, .DS_Store'.split(',')]

    for path, dirs, files in os.walk(dir_local_path):
        if path != dir_local_path:
            path = path.replace(dir_local_path, '', 1)
            non_root_paths.append(path)
            non_root_file_paths += [os.path.join(path, file_) for file_ in
                                    files if file_ not in to_be_removed_files]

    if dir_is_zipped:
        # If the "directory" from the server was a zip file, assume it is a
        # zipped bag and simulate "debagging" it, i.e., removing everything not
        # under data/ and removing the data/ prefix.
        non_root_paths = debag(non_root_paths)
        non_root_file_paths = debag(non_root_file_paths)

    assert len(non_root_paths) > 0
    assert len(non_root_file_paths) > 0
    context.scenario.remote_dir_subfolders = non_root_paths
    context.scenario.remote_dir_files = non_root_file_paths


@then('the METS file includes the original directory structure')
def step_impl(context):
    """Asserts that the <mets:structMap> element of the AIP METS file correctly
    encodes the directory structure of the transfer that was recorded in an
    earlier step under the following attributes::

        context.scenario.remote_dir_subfolders
        context.scenario.remote_dir_files

    NOTE: empty directories in the transfer are not indicated in the resulting
    AIP METS.
    """
    context.scenario.mets = mets = get_mets_from_scenario(context)
    ns = context.am_sel_cli.mets_nsmap
    struct_map_el = mets.find('.//mets:structMap[@TYPE="physical"]', ns)
    subpaths = _get_subpaths_from_struct_map(struct_map_el, ns)
    subpaths = [p.replace('/objects', '', 1) for p in
                filter(None, _remove_common_prefix(subpaths))]
    for dirpath in context.scenario.remote_dir_subfolders:
        assert dirpath in subpaths, (
            'Expected directory path\n{}\nis not in METS structmap'
            ' paths\n{}'.format(dirpath, pprint.pformat(subpaths)))
    for filepath in context.scenario.remote_dir_files:
        if os.path.basename(filepath) == '.gitignore':
            continue
        assert filepath in subpaths, (
            'Expected file path\n{}\nis not in METS structmap'
            ' paths\n{}'.format(filepath, pprint.pformat(subpaths)))


@then('the UUIDs for the subfolders and digital objects are written to the METS'
      ' file')
def step_impl(context):
    mets = context.scenario.mets
    ns = context.am_sel_cli.mets_nsmap
    struct_map_el = mets.find('.//mets:structMap[@TYPE="physical"]', ns)
    for dirpath in context.scenario.remote_dir_subfolders:
        dirname = os.path.basename(dirpath)
        mets_div_el = struct_map_el.find(
            './/mets:div[@LABEL="{}"]'.format(dirname), ns)
        assert mets_div_el is not None, (
            'Could not find a <mets:div> for directory at {}'.format(
                dirpath))
        dmdid = mets_div_el.get('DMDID')
        dmdSec_el = mets.find('.//mets:dmdSec[@ID="{}"]'.format(dmdid), ns)
        assert dmdSec_el is not None, (
            'Could not find a <mets:dmdSec> for directory at {}'.format(
                dirpath))
        try:
            id_type = dmdSec_el.find('.//premis3:objectIdentifierType', ns).text.strip()
            id_val = dmdSec_el.find('.//premis3:objectIdentifierValue', ns).text.strip()
        except AttributeError:
            logger.info(ns)
            msg = etree.tostring(dmdSec_el, pretty_print=True)
            print(msg)
            logger.info(msg)
            #raise AssertionError('Unable to find objectIdentifierType/Value')
            raise
        assert id_type == 'UUID'
        assert is_uuid(id_val)


def is_uuid(val):
    return (
        (''.join(x for x in val if x in '-abcdef0123456789') == val) and
        ([len(x) for x in val.split('-')] == [8, 4, 4, 4, 12]))


def _remove_common_prefix(seq):
    """Recursively remove a common prefix from all strings in a sequence of
    strings.
    """
    try:
        prefixes = set([x[0] for x in seq])
    except IndexError:
        return seq
    if len(prefixes) == 1:
        return _remove_common_prefix([x[1:] for x in seq])
    return seq



def _get_subpaths_from_struct_map(elem, ns, base_path='', paths=None):
    if not paths:
        paths = set()
    for div_el in elem.findall('mets:div', ns):
        path = os.path.join(base_path, div_el.get('LABEL'))
        paths.add(path)
        for subpath in _get_subpaths_from_struct_map(
                div_el, ns, base_path=path, paths=paths):
            paths.add(subpath)
    return list(paths)


@given('a processing configuration that assigns UUIDs to directories')
def step_impl(context):
    """Create a processing configuration that tells AM to assign UUIDs to
    directories.
    """
    context.execute_steps(
        'Given that the user has ensured that the default processing config is'
            ' in its default state\n'
        'And the processing config decision "Assign UUIDs to directories" is'
            ' set to "Yes"\n'
        'And the processing config decision "Select file format identification'
            ' command (Transfer)" is set to "Identify using Fido"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
            ' single SIP and continue processing"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
            ' for preservation"\n'
        'And the processing config decision "Approve normalization" is set to'
            ' "Yes"\n'
        'And the processing config decision "Bind PIDs" is set to "No"\n'
        'And the processing config decision "Select file format identification'
            ' command (Submission documentation & metadata)" is set to'
            ' "Identify using Fido"\n'
        'And the processing config decision "Perform policy checks on'
            ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
            ' derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on'
            ' originals" is set to "No"\n'
    )


@given('a base processing configuration for MediaConch tests')
def step_impl(context):
    """Create a processing configuration that is a base for all policy
    check-targetted workflows.
    """
    context.execute_steps(
        'Given that the user has ensured that the default processing config is'
            ' in its default state\n'
        'And the processing config decision "Perform policy checks on'
            ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
            ' derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on'
            ' originals" is set to "No"\n'
        'And the processing config decision "Select file format identification'
            ' command (Transfer)" is set to "Identify using Fido"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
            ' single SIP and continue processing"\n'
        'And the processing config decision "Approve normalization" is set to'
            ' "Yes"\n'
        'And the processing config decision "Select file format identification'
            ' command (Submission documentation & metadata)" is set to'
            ' "Identify using Fido"\n'
        'And the processing config decision "Store AIP location" is set to'
            ' "Store AIP in standard Archivematica Directory"\n'
        'And the processing config decision "Upload DIP" is set to'
            ' "Do not upload DIP"'
    )


@given('a processing configuration for policy checks on preservation'
       ' derivatives')
def step_impl(context):
    context.execute_steps(
        'Given a base processing configuration for MediaConch tests\n'
        'And the processing config decision "Perform policy checks on'
            ' preservation derivatives" is set to "Yes"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
            ' for preservation"'
    )


@given('a processing configuration for conformance checks on preservation'
       ' derivatives')
def step_impl(context):
    context.execute_steps(
        'Given a base processing configuration for MediaConch tests\n'
        'And the processing config decision "Approve normalization" is set to'
            ' "None"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
            ' for preservation"'
    )


@given('a processing configuration for conformance checks on access'
       ' derivatives')
def step_impl(context):
    context.execute_steps(
        'Given a base processing configuration for MediaConch tests\n'
        'And the processing config decision "Approve normalization" is set to'
            ' "None"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
            ' for access"'
    )


@given('a processing configuration for policy checks on access derivatives')
def step_impl(context):
    context.execute_steps(
        'Given a base processing configuration for MediaConch tests\n'
        'And the processing config decision "Perform policy checks on'
            ' access derivatives" is set to "Yes"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
            ' for access"\n'
        'And the processing config decision "Store AIP" is set to "Yes"'
    )


@given('a processing configuration for policy checks on originals')
def step_impl(context):
    context.execute_steps(
        'Given a base processing configuration for MediaConch tests\n'
        'And the processing config decision "Perform policy checks on'
            ' originals" is set to "Yes"\n'
        'And the processing config decision "Normalize" is set to "Do not'
            ' normalize"\n'
        'And the processing config decision "Store AIP" is set to "Yes"'
    )


@given('a processing configuration for conformance checks on originals')
def step_impl(context):
    context.execute_steps(
        'Given a base processing configuration for MediaConch tests\n'
        'And the processing config decision "Normalize" is set to "Do not'
            ' normalize"\n'
    )


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
    policy_path = get_policy_path(policy_file)
    context.am_sel_cli.ensure_fpr_policy_check_command(policy_file, policy_path)


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


@given('an FPR rule with purpose "{purpose}", format "{format}", and command'
       ' "{command}"')
def step_impl(context, purpose, format, command):
    context.am_sel_cli.ensure_fpr_rule(purpose, format, command)


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


@given('there is a standard GPG-encrypted space in the storage service')
def step_impl(context):
    context.execute_steps(
        'Given the user has ensured that there is a storage service space with'
        ' attributes'
        ' Access protocol: GPG encryption on Local Filesystem;'
        ' Path: /;'
        ' Staging path: /var/archivematica/storage_service_encrypted;'
        ' GnuPG Private Key: Archivematica Storage Service GPG Key;')


@given('the user has ensured that there is a storage service space with'
       ' attributes {attributes}')
def step_impl(context, attributes):
    """Ensure that there is a storage space with the attributes in
    ``attributes``. These are :-delimited pairs delimited by ';'.
    """
    attributes = _parse_k_v_attributes(attributes)
    context.scenario.space_uuid = context.am_sel_cli.ensure_ss_space_exists(
        attributes)


@given('the user has disabled the default transfer backlog location')
def step_impl(context):
    context.am_sel_cli.disable_default_transfer_backlog()


@given('there is a standard GPG-encrypted AIP Storage location in the storage'
       ' service')
def step_impl(context):
    context.execute_steps(
        'Given the user has ensured that there is a location in the GPG Space with'
        ' attributes'
        ' Purpose: AIP Storage;'
        ' Relative path: var/archivematica/sharedDirectory/www/AIPsStoreEncrypted;'
        ' Description: Store AIP Encrypted in standard Archivematica Directory;')


@given('there is a standard GPG-encrypted Transfer Backlog location in the'
       ' storage service')
def step_impl(context):
    context.execute_steps(
        'Given the user has ensured that there is a location in the GPG Space with'
        ' attributes'
        ' Purpose: Transfer Backlog;'
        ' Relative path: {};'
        ' Description: Store Transfers Encrypted in standard Archivematica'
            ' Directory;'.format(STDRD_GPG_TB_REL_PATH))


@given('there is a standard GPG-encrypted Replicator location in the storage'
       ' service')
def step_impl(context):
    context.execute_steps(
        'Given the user has ensured that there is a location in the GPG Space with'
        ' attributes'
        ' Purpose: Replicator;'
        ' Relative path: var/archivematica/sharedDirectory/www/EncryptedReplicas;'
        ' Description: Encrypted Replicas;')


@given('the default AIP Storage location has the GPG-encrypted Replicator'
       ' location as its replicator')
def step_impl(context):
    """Presumes that the GPG-encrypted replicator location's UUID is
    in ``context.scenario.location_uuid``.
    """
    replicator_location_uuid = context.scenario.location_uuid
    context.am_sel_cli.add_replicator_to_default_aip_stor_loc(
        replicator_location_uuid)


@given('the user has ensured that there is a location in the GPG Space with'
       ' attributes {attributes}')
def step_impl(context, attributes):
    """Ensure that there is a storage location in the space referenced in
    ``context.scenario.space_uuid`` with the attributes in ``attributes``.
    These are :-delimited pairs delimited by ';'.
    """
    attributes = _parse_k_v_attributes(attributes)
    space_uuid = context.scenario.space_uuid
    context.scenario.location_uuid = \
        context.am_sel_cli.ensure_ss_location_exists(space_uuid, attributes)


use_step_matcher('re')


@then('the downloaded (?P<aip_description>.*)AIP is not encrypted')
def step_impl(context, aip_description):
    context.scenario.aip_path = context.am_sel_cli.decompress_aip(
        context.scenario.aip_path)
    assert os.path.isdir(context.scenario.aip_path)


use_step_matcher('parse')


@then('the downloaded uncompressed AIP is an unencrypted tarfile')
def step_impl(context):
    assert tarfile.is_tarfile(context.scenario.aip_path)


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


def get_gpg_key_path(key_fname):
    return os.path.realpath(os.path.join(GPG_KEYS_DIR, key_fname))


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
                context.am_sel_cli.get_sip_uuid(context.scenario.transfer_name))
    return uuid_val


def initiate_transfer(context, transfer_path, accession_no=None,
                      transfer_type=None):
    if transfer_path.startswith('~'):
        context.scenario.transfer_path = os.path.join(
            context.HOME, transfer_path[2:])
    else:
        context.scenario.transfer_path = os.path.join(
            context.TRANSFER_SOURCE_PATH, transfer_path)
    context.scenario.transfer_name = context.am_sel_cli.unique_name(
        transfer_path2name(transfer_path))
    context.scenario.transfer_uuid, context.scenario.transfer_name = (
        context.am_sel_cli.start_transfer(
            context.scenario.transfer_path, context.scenario.transfer_name,
            accession_no=accession_no, transfer_type=transfer_type))


def _parse_k_v_attributes(attributes):
    """Parse a string of key-value attributes formatted like "key 1: value 1;
    key 2: value 2;".
    """
    return {pair.split(':')[0].strip(): pair.split(':')[1].strip() for
            pair in attributes.split(';') if pair.strip()}


@when('the user attempts to import GPG key {key_fname}')
def step_impl(context, key_fname):
    key_path = get_gpg_key_path(key_fname)
    context.scenario.import_gpg_key_result = context.am_sel_cli.import_gpg_key(key_path)


@then('the user succeeds in importing the GPG key {key_name}')
def step_impl(context, key_name):
    assert context.scenario.import_gpg_key_result.startswith('New key')
    assert context.scenario.import_gpg_key_result.endswith('created.')
    assert len(context.am_sel_cli.get_gpg_key_search_matches(key_name)) == 1


@then('the user fails to import the GPG key {key_name} because it requires a'
      ' passphrase')
def step_impl(context, key_name):
    assert context.scenario.import_gpg_key_result == (
        'Import failed. The GPG key provided requires a passphrase. GPG keys'
        ' with passphrases cannot be imported')
    assert len(context.am_sel_cli.get_gpg_key_search_matches(key_name)) == 0


@when('the user creates a new GPG key and assigns it to the standard'
       ' GPG-encrypted space')
def step_impl(context):
    # Create the new GPG key
    new_key_name, new_key_email, new_key_fingerprint = (
        context.am_sel_cli.create_new_gpg_key())
    context.scenario.new_key_name = new_key_name
    context.scenario.new_key_fingerprint = new_key_fingerprint
    # Edit the "standard GPG-encrypted space" to use the new GPG key
    standard_encr_space_uuid = context.am_sel_cli.search_for_ss_space({
        'Access protocol': 'GPG encryption on Local Filesystem',
        'Path': '/',
        'Staging path': '/var/archivematica/storage_service_encrypted',
        'GnuPG Private Key': 'Archivematica Storage Service GPG Key'
    })['uuid']
    new_key_repr = '{} <{}>'.format(new_key_name, new_key_email)
    logger.info('Created a new GPG key "%s"', new_key_repr)
    context.am_sel_cli.change_encrypted_space_key(standard_encr_space_uuid,
                                                  new_key_repr)


@then('the AIP pointer file references the fingerprint of the new GPG key')
def step_impl(context):
    pointer_path = context.scenario.aip_pointer_path
    ns = context.am_sel_cli.mets_nsmap
    fingerprint = context.scenario.new_key_fingerprint
    assert_pointer_transform_file_encryption(pointer_path, ns, fingerprint)


def assert_pointer_transform_file_encryption(pointer_path, ns,
                                             fingerprint=None):
    """Make standard assertions to confirm that the pointer file at
    ``pointer_path`` has <mets:transformFile> element(s) that indicate that the
    AIP has been encrypted via GPG.
    """
    with open(pointer_path) as filei:
        doc = etree.parse(filei)
        file_el = doc.find(
            'mets:fileSec/mets:fileGrp/mets:file', ns)
        # <tranformFile> decryption element added, and decompression one
        # modified.
        deco_tran_el = file_el.find(
            'mets:transformFile[@TRANSFORMTYPE="decompression"]', ns)
        assert deco_tran_el is not None
        deco_transform_order = deco_tran_el.get('TRANSFORMORDER', ns)
        assert deco_transform_order == '2'
        decr_tran_el = file_el.find(
            'mets:transformFile[@TRANSFORMTYPE="decryption"]', ns)
        assert decr_tran_el is not None
        assert decr_tran_el.get('TRANSFORMORDER', ns) == '1'
        assert decr_tran_el.get('TRANSFORMALGORITHM', ns) == 'GPG'
        assert bool(decr_tran_el.get('TRANSFORMTYPE', ns)) is True
        if fingerprint:
            transform_key = decr_tran_el.get('TRANSFORMKEY', ns)
            assert transform_key == fingerprint, (
                'TRANSFORMKEY fingerprint {} does not match expected'
                ' fingerprint {}'.format(transform_key, fingerprint))
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
            'GPG')
        assert inhibitors_el.find('premis:inhibitorTarget', ns).text.strip() == (
            'All content')


@when('an encrypted AIP is created from the directory at {transfer_path}')
def step_impl(context, transfer_path):
    context.execute_steps(
        'When a transfer is initiated on directory {}\n'
        'And standard AIP-creation decisions are made\n'
        'And the user waits for the "Store AIP location" decision point to'
            ' appear and chooses "Store AIP Encrypted in standard Archivematica'
            ' Directory" during ingest\n'
        'And the user waits for the AIP to appear in archival storage'.format(
            transfer_path))


@when('the user attempts to delete the new GPG key')
def step_impl(context):
    new_key_name = context.scenario.new_key_name
    logger.info('Attempting to delete GPG key "%s"', new_key_name)
    (context.scenario.delete_gpg_key_success,
        context.scenario.delete_gpg_key_msg) = (
            context.am_sel_cli.delete_gpg_key(new_key_name))
    if context.scenario.delete_gpg_key_success:
        logger.info('Attempt to delete GPG key "%s" was SUCCESSFUL',
                    new_key_name)
    else:
        logger.info('Attempt to delete GPG key "%s" FAILED: "%s"',
                    new_key_name, context.scenario.delete_gpg_key_msg)


@then('the user is prevented from deleting the key because {reason}')
def step_impl(context, reason):
    assert context.scenario.delete_gpg_key_success == False
    if reason == 'it is attached to a space':
        assert context.scenario.delete_gpg_key_msg.startswith(
            'GPG key')
        assert context.scenario.delete_gpg_key_msg.endswith(
            'cannot be deleted because at least one GPG Space is using it for'
            ' encryption.')
    elif reason == 'it is attached to a package':
        assert context.scenario.delete_gpg_key_msg.startswith(
            'GPG key')
        assert context.scenario.delete_gpg_key_msg.endswith(
            'cannot be deleted because at least one package (AIP, transfer)'
            ' needs it in order to be decrypted.'), ('Reason is actually'
                ' {}'.format(context.scenario.delete_gpg_key_msg))


@then('the user succeeds in deleting the GPG key')
def step_impl(context):
    assert context.scenario.delete_gpg_key_success == True, (
        context.scenario.delete_gpg_key_msg)
    assert context.scenario.delete_gpg_key_msg.endswith(
        'successfully deleted.')


@when('the user assigns a different GPG key to the standard GPG-encrypted'
      ' space')
def step_impl(context):
    """Edit the standard GPG-encrypted space so that it is using a GPG key
    other than the one stored in ``context.scenario.new_key_name``.
    """
    # Edit the "standard GPG-encrypted space" to use the new GPG key
    standard_encr_space_uuid = context.am_sel_cli.search_for_ss_space({
        'Access protocol': 'GPG encryption on Local Filesystem',
        'Path': '/',
        'Staging path': '/var/archivematica/storage_service_encrypted',
        'GnuPG Private Key': context.scenario.new_key_name
    })['uuid']
    context.am_sel_cli.change_encrypted_space_key(standard_encr_space_uuid)


@when('the AIP is deleted')
def step_impl(context):
    uuid_val = get_uuid_val(context, 'sip')
    context.am_sel_cli.request_aip_delete(uuid_val)
    context.am_sel_cli.approve_aip_delete_request(uuid_val)


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
        'And the user waits for the "Store AIP (review)" decision point to'
            ' appear and chooses "Store AIP" during ingest\n'
        'And the user waits for the "Store AIP location" decision point to'
            ' appear and chooses "Store AIP Encrypted in standard Archivematica'
            ' Directory" during ingest\n'
        'And the user waits for the AIP to appear in archival storage'
    )


@given('an encrypted AIP in the standard GPG-encrypted space')
def step_impl(context):
    """Create an AIP in the standard GPG-encrypted space and wait for it to
    appear in archival storage.
    """
    context.execute_steps(
        'Given the default processing config is in its default state\n'
        'And there is a standard GPG-encrypted space in the storage service\n'
        'And there is a standard GPG-encrypted AIP Storage location in the'
            ' storage service\n'
        'When an encrypted AIP is created from the directory at'
            ' ~/archivematica-sampledata/SampleTransfers/BagTransfer'
    )


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
    )


@given('default processing configured to assign UUIDs to directories')
def step_impl(context):
    context.execute_steps(
        'Given the processing config decision "Assign UUIDs to directories" is'
        ' set to "Yes"\n')


@given('default processing configured to bind PIDs')
def step_impl(context):
    context.execute_steps(
        'Given the processing config decision "Bind PIDs" is set to "Yes"\n')


@given('a Handle server client configured to create qualified PURLs')
def step_impl(context):
    """Configure the handle server settings in the dashboard so that PIDs can
    be minted and resolved (a.k.a. "bound").
    NOTE: this step requires user-supplied values for runtime-specific
    parameters like handle web service endpoint and web service key that must
    be passed in as behave userdata (i.e., -D) arguments.
    """
    nodice = 'no dice'
    # Runtime-specific parameters for the Handle configuration to test against
    # must be passed in by the user at test runtime, e.g., as
    # ``behave -D base_resolve_url='https://foobar.org'``, etc.
    base_resolve_url = getattr(context.am_sel_cli, 'base_resolve_url', nodice)
    pid_xml_namespace = getattr(context.am_sel_cli, 'pid_xml_namespace', nodice)
    context.am_sel_cli.configure_handle(**{
        # More runtime-specific parameters:
        'pid_web_service_endpoint': getattr(
            context.am_sel_cli, 'pid_web_service_endpoint', nodice),
        'pid_web_service_key': getattr(
            context.am_sel_cli, 'pid_web_service_key', nodice),
        'handle_resolver_url': getattr(
            context.am_sel_cli, 'handle_resolver_url', nodice),
        'naming_authority': getattr(
            context.am_sel_cli, 'naming_authority', '12345'),
        # Baked in:
        'pid_request_verify_certs': False,
        'resolve_url_template_archive': (
            base_resolve_url + '/dip/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_mets': (
            base_resolve_url + '/mets/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file': (
            base_resolve_url + '/access/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file_access': (
            base_resolve_url + '/access/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file_preservation': (
            base_resolve_url + '/preservation/{{ naming_authority }}/{{ pid }}'),
        'resolve_url_template_file_original': (
            base_resolve_url + '/original/{{ naming_authority }}/{{ pid }}'),
        'pid_request_body_template': '''<?xml version='1.0' encoding='UTF-8'?>
        <soapenv:Envelope
            xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'
            xmlns:pid='{pid_xml_namespace}'>
            <soapenv:Body>
                <pid:UpsertPidRequest>
                    <pid:na>{{{{ naming_authority }}}}</pid:na>
                    <pid:handle>
                        <pid:pid>{{{{ naming_authority }}}}/{{{{ pid }}}}</pid:pid>
                        <pid:locAtt>
                            <pid:location weight='1' href='{{{{ base_resolve_url }}}}'/>
                            {{% for qrurl in qualified_resolve_urls %}}
                                <pid:location
                                    weight='0'
                                    href='{{{{ qrurl.url }}}}'
                                    view='{{{{ qrurl.qualifier }}}}'/>
                            {{% endfor %}}
                        </pid:locAtt>
                    </pid:handle>
                </pid:UpsertPidRequest>
            </soapenv:Body>
        </soapenv:Envelope>'''.format(pid_xml_namespace=pid_xml_namespace)
    })


@given('a Handle server client configured to use the accession number as the'
       ' PID for the AIP')
def step_impl(context):
    context.am_sel_cli.configure_handle(
        handle_archive_pid_source='Accession number')


@then('the AIP METS file documents PIDs, PURLs, and UUIDs for all files,'
      ' directories and the package itself')
def step_impl(context):
    accession_no = getattr(context.scenario, 'accession_no', None)
    mets = get_mets_from_scenario(context)
    context.am_sel_cli.validate_mets_for_pids(mets, accession_no=accession_no)
