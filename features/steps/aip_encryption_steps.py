"""Steps for the AIP Encryption Feature."""

import os
import tarfile

from lxml import etree
from behave import when, then, given, use_step_matcher

from features.steps import utils


GPG_KEYS_DIR = 'etc/gpgkeys'
STDRD_GPG_TB_REL_PATH = (
    'var/archivematica/sharedDirectory/www/AIPsStore/transferBacklogEncrypted')

# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------

@given('there is a standard GPG-encrypted space in the storage service')
def step_impl(context):
    context.execute_steps(
        'Given the user has ensured that there is a storage service space with'
        ' attributes'
        ' Access protocol: GPG encryption on Local Filesystem;'
        ' Path: /;'
        ' Staging path: /var/archivematica/storage_service/storage_service_encrypted;'
        ' GnuPG Private Key: Archivematica Storage Service GPG Key;')


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
    context.am_user.browser.add_replicator_to_default_aip_stor_loc(
        replicator_location_uuid)


@given('the user has ensured that there is a location in the GPG Space with'
       ' attributes {attributes}')
def step_impl(context, attributes):
    """Ensure that there is a storage location in the space referenced in
    ``context.scenario.space_uuid`` with the attributes in ``attributes``.
    These are :-delimited pairs delimited by ';'.
    """
    attributes = utils.parse_k_v_attributes(attributes)
    space_uuid = context.scenario.space_uuid
    context.scenario.location_uuid = \
        context.am_user.browser.ensure_ss_location_exists(space_uuid, attributes)


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


# Whens
# ------------------------------------------------------------------------------

@when('the user attempts to import GPG key {key_fname}')
def step_impl(context, key_fname):
    key_path = get_gpg_key_path(key_fname)
    context.scenario.import_gpg_key_result = context.am_user.browser.import_gpg_key(key_path)


@when('the user creates a new GPG key and assigns it to the standard'
      ' GPG-encrypted space')
def step_impl(context):
    # Create the new GPG key
    new_key_name, new_key_email, new_key_fingerprint = (
        context.am_user.browser.create_new_gpg_key())
    context.scenario.new_key_name = new_key_name
    context.scenario.new_key_fingerprint = new_key_fingerprint
    # Edit the "standard GPG-encrypted space" to use the new GPG key
    standard_encr_space_uuid = context.am_user.browser.search_for_ss_space({
        'Access protocol': 'GPG encryption on Local Filesystem',
        'Path': '/',
        'Staging path': '/var/archivematica/storage_service/storage_service_encrypted',
        'GnuPG Private Key': 'Archivematica Storage Service GPG Key'
    })['uuid']
    new_key_repr = '{} <{}>'.format(new_key_name, new_key_email)
    utils.logger.info('Created a new GPG key "%s"', new_key_repr)
    context.am_user.browser.change_encrypted_space_key(standard_encr_space_uuid,
                                                       new_key_repr)


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
    utils.logger.info('Attempting to delete GPG key "%s"', new_key_name)
    (context.scenario.delete_gpg_key_success,
     context.scenario.delete_gpg_key_msg) = (
         context.am_user.browser.delete_gpg_key(new_key_name))
    if context.scenario.delete_gpg_key_success:
        utils.logger.info('Attempt to delete GPG key "%s" was SUCCESSFUL',
                          new_key_name)
    else:
        utils.logger.info('Attempt to delete GPG key "%s" FAILED: "%s"',
                          new_key_name, context.scenario.delete_gpg_key_msg)


@when('the user assigns a different GPG key to the standard GPG-encrypted'
      ' space')
def step_impl(context):
    """Edit the standard GPG-encrypted space so that it is using a GPG key
    other than the one stored in ``context.scenario.new_key_name``.
    """
    # Edit the "standard GPG-encrypted space" to use the new GPG key
    standard_encr_space_uuid = context.am_user.browser.search_for_ss_space({
        'Access protocol': 'GPG encryption on Local Filesystem',
        'Path': '/',
        'Staging path': '/var/archivematica/storage_service/storage_service_encrypted',
        'GnuPG Private Key': context.scenario.new_key_name
    })['uuid']
    context.am_user.browser.change_encrypted_space_key(standard_encr_space_uuid)


# Thens
# ------------------------------------------------------------------------------

@then('the master AIP and its replica are returned by the search')
def step_impl(context):
    """Assert that ``context.scenario.aip_search_results`` is a list of exactly
    two dicts, one of which represents "the master AIP" (whose UUID is in
    ``context.scenariosip_uuid``) and the other representing the replica AIP.
    Store both AIP representations in ``context.scenario``.
    """
    the_aip_uuid = utils.get_uuid_val(context, 'sip')
    search_results = context.scenario.aip_search_results
    assert len(search_results) == 2, (
        'We expected 2 search results but there are {} in {}'.format(
            len(search_results), str(search_results)))
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


@then('the {aip_description} pointer file contains a PREMIS:OBJECT with a'
      ' derivation relationship pointing to the {second_aip_description} and'
      ' the {event_type} PREMIS:EVENT')
def step_impl(context, aip_description, second_aip_description, event_type):
    aip_ptr_attr = utils.aip_descr_to_ptr_attr(aip_description)
    pointer_path = getattr(context.scenario, aip_ptr_attr)
    second_aip_attr = utils.aip_descr_to_attr(second_aip_description)
    second_aip_uuid = getattr(context.scenario, second_aip_attr)
    event_uuid_attr = utils.get_event_attr(event_type)
    event_uuid = getattr(context.scenario, event_uuid_attr)
    with open(pointer_path) as filei:
        doc = etree.parse(filei)
        premis_object_el = doc.find(
            './/mets:mdWrap[@MDTYPE="PREMIS:OBJECT"]',
            context.am_user.mets.mets_nsmap)
        premis_relationship = premis_object_el.find(
            'mets:xmlData/premis:object/premis:relationship',
            context.am_user.mets.mets_nsmap)
        premis_relationship_type = premis_relationship.find(
            'premis:relationshipType',
            context.am_user.mets.mets_nsmap).text.strip()
        assert premis_relationship_type == 'derivation'
        premis_related_object_uuid = premis_relationship.find(
            'premis:relatedObjectIdentification/'
            'premis:relatedObjectIdentifierValue',
            context.am_user.mets.mets_nsmap).text.strip()
        assert second_aip_uuid == premis_related_object_uuid
        premis_related_event_uuid = premis_relationship.find(
            'premis:relatedEventIdentification/'
            'premis:relatedEventIdentifierValue',
            context.am_user.mets.mets_nsmap).text.strip()
        assert event_uuid == premis_related_event_uuid


@then('the {aip_description} pointer file contains a(n) {event_type}'
      ' PREMIS:EVENT')
def step_impl(context, aip_description, event_type):
    aip_ptr_attr = utils.aip_descr_to_ptr_attr(aip_description)
    pointer_path = getattr(context.scenario, aip_ptr_attr)
    event_uuid = assert_pointer_premis_event(
        context=context, pointer_path=pointer_path, event_type=event_type,
        in_evt_out=['success'])
    event_uuid_attr = utils.get_event_attr(event_type)
    setattr(context.scenario, event_uuid_attr, event_uuid)


@then('the pointer file contains a PREMIS:EVENT element for the encryption event')
def step_impl(context):
    """This asserts that the pointer file contains a ``<mets:mdWrap
    MDTYPE="PREMIS:EVENT">`` element with the following type of descendants:
    - <mets:xmlData>
    - <premis:eventType>encryption</premis:eventType>
    - <premis:eventDetail>program=gpg (GPG); version=1.4.16; python-gnupg;
       version=0.4.0</premis:eventDetail>
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
                context.am_user.mets.mets_nsmap):
            premis_event_type_el = premis_event_el.find(
                'mets:xmlData/premis:event/premis:eventType',
                context.am_user.mets.mets_nsmap)
            if premis_event_type_el.text.strip() == 'encryption':
                premis_event = premis_event_el
                break
        assert premis_event is not None
        # <premis:eventDetail>program=gpg (GPG); version=1.4.16; python-gnupg;
        # version=0.4.0</premis:eventDetail>
        premis_event_detail = premis_event.find(
            'mets:xmlData/premis:event/premis:eventDetail',
            context.am_user.mets.mets_nsmap).text
        assert 'GPG' in premis_event_detail
        assert 'version=' in premis_event_detail
        premis_event_od_note = premis_event.find(
            'mets:xmlData/premis:event/premis:eventOutcomeInformation/'
            'premis:eventOutcomeDetail/premis:eventOutcomeDetailNote',
            context.am_user.mets.mets_nsmap).text.strip()
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
        aip_ptr_attr = utils.aip_descr_to_ptr_attr(aip_description)
        pointer_path = getattr(context.scenario, aip_ptr_attr)
    else:
        pointer_path = context.scenario.aip_pointer_path
    ns = context.am_user.mets.mets_nsmap
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


@then('the downloaded (?P<aip_description>.*)AIP is not encrypted')
def step_impl(context, aip_description):
    context.scenario.aip_path = context.am_user.decompress_aip(
        context.scenario.aip_path)
    assert os.path.isdir(context.scenario.aip_path)


@then('the master and replica AIPs are byte-for-byte identical')
def step_impl(context):
    assert os.path.isfile(context.scenario.master_aip)
    assert os.path.isfile(context.scenario.replica_aip)
    with open(context.scenario.master_aip, 'rb') as filei:
        master_bytes = filei.read()
    with open(context.scenario.replica_aip, 'rb') as filei:
        replica_bytes = filei.read()
    assert master_bytes == replica_bytes


@then('the downloaded uncompressed AIP is an unencrypted tarfile')
def step_impl(context):
    assert tarfile.is_tarfile(context.scenario.aip_path)


@then('the user succeeds in importing the GPG key {key_name}')
def step_impl(context, key_name):
    assert context.scenario.import_gpg_key_result.startswith('New key')
    assert context.scenario.import_gpg_key_result.endswith('created.')
    assert len(context.am_user.browser.get_gpg_key_search_matches(key_name)) == 1


@then('the user fails to import the GPG key {key_name} because it requires a'
      ' passphrase')
def step_impl(context, key_name):
    assert context.scenario.import_gpg_key_result == (
        'Import failed. The GPG key provided requires a passphrase. GPG keys'
        ' with passphrases cannot be imported')
    assert not context.am_user.browser.get_gpg_key_search_matches(key_name)


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
    utils.logger.info('expecting encrypted transfer to be at %s on server',
                      path_on_disk)
    if getattr(context.am_user.docker, 'docker_compose_path', None):
        dip_local_path = context.am_user.docker.cp_server_file_to_local(
            path_on_disk)
    else:
        dip_local_path = context.am_user.ssh.scp_server_file_to_local(
            path_on_disk)
    if dip_local_path is None:
        utils.logger.info(
            'Unable to copy file %s from the server to the local file'
            ' system. Server is not accessible via SSH. Abandoning'
            ' attempt to assert that the DIP on disk is'
            ' encrypted.', path_on_disk)
        return
    elif dip_local_path is False:
        utils.logger.info(
            'Unable to copy file %s from the server to the local file'
            ' system. Attempt to scp the file failed. Abandoning attempt'
            ' to assert that the DIP on disk is'
            ' encrypted.', path_on_disk)
        return
    assert not os.path.isdir(dip_local_path)
    assert not tarfile.is_tarfile(dip_local_path)


@then('the uncompressed AIP on disk at {aips_store_path} is encrypted')
def step_impl(context, aips_store_path):
    tmp = context.scenario.sip_uuid.replace('-', '')
    parts = [tmp[i:i + 4] for i in range(0, len(tmp), 4)]
    subpath = '/'.join(parts)
    aip_server_path = '{}{}/{}-{}'.format(
        aips_store_path, subpath, context.scenario.transfer_name,
        context.scenario.sip_uuid)
    aip_local_path = context.am_user.ssh.scp_server_file_to_local(
        aip_server_path)
    if aip_local_path is None:
        utils.logger.info(
            'Unable to copy file %s from the server to the local file'
            ' system. Server is not accessible via SSH. Abandoning'
            ' attempt to assert that the AIP on disk is'
            ' encrypted.', aip_server_path)
        return
    elif aip_local_path is False:
        utils.logger.info(
            'Unable to copy file %s from the server to the local file'
            ' system. Attempt to scp the file failed. Abandoning attempt'
            ' to assert that the AIP on disk is'
            ' encrypted.', aip_server_path)
        return
    assert not os.path.isdir(aip_local_path)
    assert not tarfile.is_tarfile(aip_local_path)


@then('the AIP pointer file references the fingerprint of the new GPG key')
def step_impl(context):
    pointer_path = context.scenario.aip_pointer_path
    ns = context.am_user.mets.mets_nsmap
    fingerprint = context.scenario.new_key_fingerprint
    assert_pointer_transform_file_encryption(pointer_path, ns, fingerprint)


@then('the user is prevented from deleting the key because {reason}')
def step_impl(context, reason):
    assert context.scenario.delete_gpg_key_success is False
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
            ' needs it in order to be decrypted.'), (
                'Reason is actually {}'.format(
                    context.scenario.delete_gpg_key_msg))


@then('the user succeeds in deleting the GPG key')
def step_impl(context):
    assert context.scenario.delete_gpg_key_success is True, (
        context.scenario.delete_gpg_key_msg)
    assert context.scenario.delete_gpg_key_msg.endswith(
        'successfully deleted.')


# ==============================================================================
# Helper Functions
# ==============================================================================

def assert_pointer_premis_event(**kwargs):
    """Make assertions about the PREMIS event of premis:eventType
    ``event_type`` in the METS pointer file at ``pointer_path``. Minimally
    assert that such an event exists. The optional params should hold lists of
    strings that are all expected to be in eventDetail, eventOutcome, and
    eventOutcomeDetailNote, respectively. Return the UUID of the relevant event.
    """
    with open(kwargs['pointer_path']) as filei:
        doc = etree.parse(filei)
        premis_event = None
        for premis_event_el in doc.findall(
                './/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]',
                kwargs['context'].am_user.mets.mets_nsmap):
            premis_event_type_el = premis_event_el.find(
                'mets:xmlData/premis:event/premis:eventType',
                kwargs['context'].am_user.mets.mets_nsmap)
            if premis_event_type_el.text.strip() == kwargs['event_type']:
                premis_event = premis_event_el
                break
        assert premis_event is not None
        premis_event_uuid = premis_event.find(
            'mets:xmlData/premis:event/premis:eventIdentifier/'
            'premis:eventIdentifierValue',
            kwargs['context'].am_user.mets.mets_nsmap).text.strip()
        if kwargs.get('in_evt_dtl'):
            in_evt_dtl = kwargs['in_evt_dtl'] or []
            premis_event_detail = premis_event.find(
                'mets:xmlData/premis:event/premis:eventDetail',
                kwargs['context'].am_user.mets.mets_nsmap).text.strip()
            for substr in in_evt_dtl:
                assert substr in premis_event_detail
        if kwargs.get('in_evt_out'):
            in_evt_out = kwargs['in_evt_out'] or []
            premis_event_out = premis_event.find(
                'mets:xmlData/premis:event/premis:eventOutcomeInformation/'
                'premis:eventOutcome',
                kwargs['context'].am_user.mets.mets_nsmap).text.strip()
            for substr in in_evt_out:
                assert substr in premis_event_out
        if kwargs.get('in_evt_out_dtl_nt'):
            in_evt_out_dtl_nt = kwargs['in_evt_out_dtl_nt'] or []
            premis_event_od_note = premis_event.find(
                'mets:xmlData/premis:event/premis:eventOutcomeInformation/'
                'premis:eventOutcomeDetail/premis:eventOutcomeDetailNote',
                kwargs['context'].am_user.mets.mets_nsmap).text.strip()
            for substr in in_evt_out_dtl_nt:
                assert substr in premis_event_od_note
        return premis_event_uuid


def get_aip_is_encrypted(context, aip_description):
    aip_description = aip_description.strip()
    if aip_description:
        aip_ptr_attr = utils.aip_descr_to_ptr_attr(aip_description + '_aip')
        pointer_path = getattr(context.scenario, aip_ptr_attr)
    else:
        pointer_path = context.scenario.aip_pointer_path
    ns = context.am_user.mets.mets_nsmap
    with open(pointer_path) as filei:
        doc = etree.parse(filei)
        file_el = doc.find('mets:fileSec/mets:fileGrp/mets:file', ns)
        flocat_el = file_el.find('mets:FLocat', ns)
        xlink_href = flocat_el.get('{' + ns['xlink'] + '}href')
        # Use `scp` or `docker cp` to copy the AIP on the server to a local
        # directory.
        if getattr(context.am_user.docker, 'docker_compose_path', None):
            aip_local_path = context.am_user.docker.cp_server_file_to_local(xlink_href)
        else:
            aip_local_path = context.am_user.ssh.scp_server_file_to_local(xlink_href)
        if aip_local_path is None:
            utils.logger.warning(
                'Unable to copy file %s from the server to the local file'
                ' system. Server is not accessible via SSH. Abandoning'
                ' attempt to assert that the AIP on disk is'
                ' encrypted.', xlink_href)
            return
        elif aip_local_path is False:
            utils.logger.warning(
                'Unable to copy file %s from the server to the local file'
                ' system. Attempt to scp the file failed. Abandoning attempt'
                ' to assert that the AIP on disk is'
                ' encrypted.', xlink_href)
            return
    aip_local_path = context.am_user.decompress_package(aip_local_path)
    # ``decompress_package`` will attempt to decompress the package with 7z and
    # we expect it to fail because the AIP file is encrypted with GPG.
    aip_is_encrypted = aip_local_path is None
    return aip_is_encrypted


def get_gpg_key_path(key_fname):
    return os.path.realpath(os.path.join(GPG_KEYS_DIR, key_fname))


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
