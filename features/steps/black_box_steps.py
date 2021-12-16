#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Steps for the black_box features.

These steps use the AM APIs to initiate transfers and validate the
contents of their AIPs without relying on user interface interactions.
"""

from __future__ import print_function, unicode_literals
import os

from behave import given, when, then, use_step_matcher
from lxml import etree
import metsrw

from features.steps import utils


# map the event types as written in the feature file
# to what AM outputs in the METS
PREMIS_EVENT_TYPES = {
    "file format identification": "format identification",
    "ingestion": "ingestion",
    "message digest calculation": "message digest calculation",
    "reingestion": "reingestion",
    "validation": "validation",
    "virus scanning": "virus check",
}


def format_original_files_error(transfer):
    return 'The {} file does not contain any "original" files in its fileSec'.format(
        transfer["aip_mets_location"]
    )


def format_no_files_error(transfer):
    return "The {} file does not contain any files in its fileSec".format(
        transfer["aip_mets_location"]
    )


@given('a "{transfer_type}" transfer type located in "{sample_transfer_path}"')
def step_impl(context, transfer_type, sample_transfer_path):
    transfer = utils.create_sample_transfer(
        context.api_clients_config, sample_transfer_path, transfer_type=transfer_type
    )
    context.current_transfer = transfer


@given("a processing configuration for metadata only reingests")
def step_impl(context):
    context.am_user.browser.reset_default_processing_config()
    context.am_user.browser.set_processing_config_decision(
        decision_label="Normalize", choice_value="Do not normalize"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Reminder: add metadata if desired", choice_value="Continue"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Transcribe files (OCR)", choice_value="No"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Store AIP", choice_value="Yes"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Store AIP location", choice_value="Default location"
    )
    context.am_user.browser.save_default_processing_config()


@given("a processing configuration for partial reingests")
def step_impl(context):
    context.am_user.browser.reset_default_processing_config()
    context.am_user.browser.set_processing_config_decision(
        decision_label="Normalize", choice_value="Normalize for access"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Approve normalization", choice_value="Yes"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Reminder: add metadata if desired", choice_value="Continue"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Transcribe files (OCR)", choice_value="No"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Store AIP", choice_value="Yes"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Store AIP location", choice_value="Default location"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Upload DIP", choice_value="Do not upload DIP"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Store DIP", choice_value="Store DIP"
    )
    context.am_user.browser.set_processing_config_decision(
        decision_label="Store DIP location", choice_value="Default location"
    )
    context.am_user.browser.save_default_processing_config()


@when(
    'a "{reingest_type}" reingest is started using the "{processing_config}" processing configuration'
)
def step_impl(context, reingest_type, processing_config):
    reingest = utils.create_reingest(
        context.api_clients_config,
        context.current_transfer,
        reingest_type,
        processing_config,
    )
    context.current_transfer.update(reingest)


@when("the reingest is approved")
def step_impl(context):
    if context.current_transfer["reingest_type"] == "FULL":
        approve_handler = utils.approve_transfer
    else:
        approve_handler = utils.approve_partial_reingest
    approve_handler(
        context.api_clients_config, context.current_transfer["reingest_uuid"]
    )


@when("the AIP is downloaded")
def step_impl(context):
    utils.is_valid_download(context.current_transfer["aip_mets_location"])


@when("the transfer is approved")
def step_impl(context):
    utils.assert_jobs_completed_successfully(
        context.api_clients_config,
        context.current_transfer["transfer_uuid"],
        job_microservice="Approve transfer",
    )


@when("the transfer compliance is verified")
def step_impl(context):
    utils.assert_jobs_completed_successfully(
        context.api_clients_config,
        context.current_transfer["transfer_uuid"],
        job_microservice="Verify transfer compliance",
    )


@when("the reingest has been processed")
def step_impl(context):
    context.current_transfer.update(
        utils.finish_reingest(
            context.api_clients_config,
            context.current_transfer["transfer_name"],
            context.current_transfer["transfer_uuid"],
            context.current_transfer["reingest_type"],
            context.current_transfer["reingest_uuid"],
        )
    )
    utils.is_valid_download(context.current_transfer["aip_mets_location"])
    utils.is_valid_download(context.current_transfer["reingest_aip_mets_location"])


@when('the "{metadata_file}" metadata file is added')
def step_impl(context, metadata_file):
    utils.copy_metadata_files(
        context.api_clients_config,
        context.current_transfer["sip_uuid"],
        [metadata_file],
    )


@then("the AIP METS can be accessed and parsed by mets-reader-writer")
def step_impl(context):
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    error = (
        "METS read successfully by metsrw but does not contain an "
        "objects directory structure"
    )
    assert mets.get_file(type="Directory", label="objects") is not None, error


@then("the AIP contains all files that were present in the transfer")
def step_impl(context):
    """Compare METS file entries with transfer contents.

    For each 'original' file entry assert that its path exists in the
    transfer directory.
    """
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    # cache each query to the SS browse endpoint by directory name
    cached_directories = {}
    original_files_dir = context.current_transfer["transfer_path"]
    # look for an 'objects' directory in the transfer directory
    contains_objects_dir = False
    objects_dir = os.path.join(context.current_transfer["transfer_path"], "objects")
    objects_dir_browse_result = utils.browse_default_ts_location(
        context.api_clients_config, objects_dir
    )
    if objects_dir_browse_result:
        contains_objects_dir = True
        cached_directories[objects_dir] = objects_dir_browse_result
    else:
        # transfer is a bag
        data_dir = os.path.join(context.current_transfer["transfer_path"], "data")
        data_dir_browse_result = utils.browse_default_ts_location(
            context.api_clients_config, data_dir
        )
        if data_dir_browse_result:
            original_files_dir = data_dir
            cached_directories[data_dir] = data_dir_browse_result
    # get the paths (before filename change) of each 'original' file
    original_file_paths = [
        utils.get_path_before_filename_change(fsentry, contains_objects_dir)
        for fsentry in mets.all_files()
        if fsentry.use == "original"
    ]
    assert original_file_paths, format_original_files_error(context.current_transfer)
    # verify each path has an entry in the transfer directory
    for file_path in original_file_paths:
        file_dir = os.path.join(original_files_dir, os.path.dirname(file_path))
        file_name = os.path.basename(file_path)
        if file_dir not in cached_directories:
            file_dir_browse_result = utils.browse_default_ts_location(
                context.api_clients_config, file_dir
            )
            cached_directories[file_dir] = file_dir_browse_result
        assert file_name in cached_directories[file_dir]["entries"]


@then("the AIP contains a file called README.html in the data directory")
def step_impl(context):
    readme_file = utils.get_aip_file_location(
        context.current_transfer["extracted_aip_dir"],
        os.path.join("data", "README.html"),
    )
    utils.is_valid_download(readme_file)


@then("the AIP contains the METS file in the data directory")
def step_impl(context):
    mets_file = utils.get_aip_mets_location(
        context.current_transfer["extracted_aip_dir"],
        context.current_transfer["sip_uuid"],
    )
    utils.is_valid_download(mets_file)


@then("the AIP conforms to expected content and structure")
def step_impl(context):
    expected_directories = [
        "objects",
        "logs",
        os.path.join("objects", "submissionDocumentation"),
    ]
    for directory in expected_directories:
        assert os.path.isdir(
            os.path.join(
                context.current_transfer["extracted_aip_dir"], "data", directory
            )
        )


@then(
    "the fileSec of the AIP METS will record every file in the objects "
    "and metadata directories of the AIP"
)
def step_impl(context):
    tree = etree.parse(context.current_transfer["aip_mets_location"])
    filesec_files = utils.get_filesec_files(tree, nsmap=context.mets_nsmap)
    assert filesec_files, format_no_files_error(context.current_transfer)
    for filesec_file in filesec_files:
        flocat = filesec_file.find("mets:FLocat", namespaces=context.mets_nsmap)
        href = flocat.attrib["{http://www.w3.org/1999/xlink}href"]
        assert os.path.exists(
            os.path.join(context.current_transfer["extracted_aip_dir"], "data", href)
        )


@then(
    "the physical structMap of the AIP METS accurately reflects the physical layout of the AIP"
)
def step_impl(context):
    root_path = os.path.join(context.current_transfer["extracted_aip_dir"], "data")
    tree = etree.parse(context.current_transfer["aip_mets_location"])
    transfer_dir = utils.get_transfer_dir_from_structmap(
        tree,
        context.current_transfer["transfer_name"],
        context.current_transfer["sip_uuid"],
        nsmap=context.mets_nsmap,
    )
    error = (
        'The {} file does not contain any "Directory" entries in its physical '
        "structMap".format(context.current_transfer["aip_mets_location"])
    )
    assert len(transfer_dir), error
    for item in transfer_dir:
        utils.assert_structmap_item_path_exists(item, root_path)


@then("every object in the AIP has been assigned a UUID in the AIP METS")
def step_impl(context):
    tree = etree.parse(context.current_transfer["aip_mets_location"])
    filesec_files = utils.get_filesec_files(tree, nsmap=context.mets_nsmap)
    assert filesec_files, format_no_files_error(context.current_transfer)
    for filesec_file in filesec_files:
        # remove the 'file-' prefix from the UUID of the file
        file_uuid = filesec_file.attrib["ID"].split("file-")[-1]
        amdsec_id = filesec_file.attrib["ADMID"]
        amdsec = tree.find(
            'mets:amdSec[@ID="{}"]'.format(amdsec_id), namespaces=context.mets_nsmap
        )
        object_uuid = amdsec.xpath(
            "mets:techMD/mets:mdWrap/mets:xmlData/premis:object/"
            'premis:objectIdentifier/premis:objectIdentifierType[text()="UUID"]/'
            "../premis:objectIdentifierValue",
            namespaces=context.mets_nsmap,
        )[0].text
        assert object_uuid == file_uuid


@then("every object in the objects and metadata directories has an amdSec")
def step_impl(context):
    tree = etree.parse(context.current_transfer["aip_mets_location"])
    filesec_files = utils.get_filesec_files(tree, nsmap=context.mets_nsmap)
    assert filesec_files, format_no_files_error(context.current_transfer)
    for filesec_file in filesec_files:
        amdsec_id = filesec_file.attrib["ADMID"]
        amdsec = tree.find(
            'mets:amdSec[@ID="{}"]'.format(amdsec_id), namespaces=context.mets_nsmap
        )
        assert amdsec is not None


@then(
    "every PREMIS event recorded in the AIP METS records the logged-in "
    "user, the organization and the software as PREMIS agents"
)
def step_impl(context):
    expected_agent_types = set(
        ["Archivematica user pk", "repository code", "preservation system"]
    )
    tree = etree.parse(context.current_transfer["aip_mets_location"])
    premis_events = tree.findall(
        'mets:amdSec/mets:digiprovMD/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]/'
        "mets:xmlData/premis:event",
        namespaces=context.mets_nsmap,
    )
    error = "The {} file does not contain any PREMIS events".format(
        context.current_transfer["aip_mets_location"]
    )
    assert premis_events, error
    for event in premis_events:
        event_agents = event.findall(
            "premis:linkingAgentIdentifier", namespaces=context.mets_nsmap
        )
        event_agent_types = set(
            [
                event_agent.findtext(
                    "premis:linkingAgentIdentifierType", namespaces=context.mets_nsmap
                )
                for event_agent in event_agents
            ]
        )
        assert event_agent_types == expected_agent_types


@then("the AIP can be successfully stored")
def step_impl(context):
    context.execute_steps(
        "Then the AIP METS can be accessed and parsed by mets-reader-writer\n"
    )


use_step_matcher("re")


@then("there is a.? (?P<event_type>.*) event for each original object in the AIP METS")
def step_impl(context, event_type):
    mets_path = context.current_transfer["aip_mets_location"]
    if event_type == "reingestion":
        mets_path = context.current_transfer["reingest_aip_mets_location"]
    mets = metsrw.METSDocument.fromfile(mets_path)
    original_files = [
        fsentry for fsentry in mets.all_files() if fsentry.use == "original"
    ]
    assert original_files, format_original_files_error(context.current_transfer)
    for fsentry in original_files:
        events = utils.get_premis_events_by_type(
            fsentry, PREMIS_EVENT_TYPES[event_type]
        )
        error = "Expected one {} event in the METS for file {}".format(
            event_type, fsentry.path
        )
        assert len(events) == 1, error


use_step_matcher("parse")


@then(
    "there are {expected_files_count:d} original objects in the AIP METS with"
    " a {event_type} event"
)
def step_impl(context, expected_files_count, event_type):
    if not expected_files_count:
        return
    mets_path = context.current_transfer["aip_mets_location"]
    mets = metsrw.METSDocument.fromfile(mets_path)
    original_files = [
        fsentry for fsentry in mets.all_files() if fsentry.use == "original"
    ]
    assert original_files, format_original_files_error(context.current_transfer)
    files_with_event_type = []
    for fsentry in original_files:
        if utils.get_premis_events_by_type(fsentry, PREMIS_EVENT_TYPES[event_type]):
            files_with_event_type.append(fsentry)
    error = (
        "In the {mets} file only the following files had {event_type} events"
        " when {expected} were expected to have: {files}".format(
            mets=context.current_transfer["aip_mets_location"],
            event_type=event_type,
            expected=expected_files_count,
            files=", ".join([entry.path for entry in files_with_event_type]),
        )
    )
    assert len(files_with_event_type) == expected_files_count, error


@then("there is a current and a superseded techMD for each original object")
def step_impl(context):
    mets = metsrw.METSDocument.fromfile(
        context.current_transfer["reingest_aip_mets_location"]
    )
    original_files = [
        fsentry for fsentry in mets.all_files() if fsentry.use == "original"
    ]
    assert original_files, format_original_files_error(context.current_transfer)
    for fsentry in original_files:
        techmds = mets.tree.findall(
            'mets:amdSec[@ID="{}"]/mets:techMD'.format(fsentry.admids[0]),
            namespaces=context.mets_nsmap,
        )
        techmds_status = sorted([techmd.attrib["STATUS"] for techmd in techmds])
        error = (
            "Expected two techMD elements (current and superseded) for"
            " file {}. Got {} instead".format(fsentry.path, techmds_status)
        )
        assert techmds_status == ["current", "superseded"], error


@then("there is a sourceMD containing a BagIt mdWrap in the AIP METS")
def step_impl(context):
    utils.assert_source_md_in_bagit_mets(
        etree.parse(context.current_transfer["aip_mets_location"]), context.mets_nsmap
    )


@then("there is a sourceMD containing a BagIt mdWrap in the reingested AIP METS")
def step_impl(context):
    utils.assert_source_md_in_bagit_mets(
        etree.parse(context.current_transfer["reingest_aip_mets_location"]),
        context.mets_nsmap,
    )


@then("there is a fileSec for deleted files for objects that were re-normalized")
def step_impl(context):
    # get files that were deleted after reingest
    reingest_mets = metsrw.METSDocument.fromfile(
        context.current_transfer["reingest_aip_mets_location"]
    )
    deleted_files = utils.get_filesec_files(
        reingest_mets.tree, use="deleted", nsmap=context.mets_nsmap
    )
    # the GROUPID represents the UUID of the deleted file before being reingested
    # remove the "Group-" prefix to get its initial UUID
    deleted_file_uuids = [
        deleted_file.attrib["GROUPID"][6:] for deleted_file in deleted_files
    ]
    # go through each normalized file in the original METS (before reingest)
    # and verify that its file_uuid is included in the deleted file uuids
    initial_mets = metsrw.METSDocument.fromfile(
        context.current_transfer["aip_mets_location"]
    )
    original_files = [
        fsentry for fsentry in initial_mets.all_files() if fsentry.use == "original"
    ]
    assert original_files, format_original_files_error(context.current_transfer)
    for fsentry in original_files:
        if utils.get_premis_events_by_type(fsentry, "normalization"):
            error = "Expected normalized file {} to be deleted after reingest".format(
                fsentry.path
            )
            assert fsentry.file_uuid in deleted_file_uuids, error


@then('the "{job_name}" job completes successfully')
def step_impl(context, job_name):
    default_valid_exit_codes = (0,)
    valid_exit_codes_by_job_name = {
        "Assign UUIDs to directories": (0, 1),
        "Determine if transfer contains packages": (0, 1),
        "Determine if transfer still contains packages": (0, 1),
    }
    valid_exit_codes = valid_exit_codes_by_job_name.get(
        job_name, default_valid_exit_codes
    )
    utils.assert_jobs_completed_successfully(
        context.api_clients_config,
        context.current_transfer["transfer_uuid"],
        job_name=job_name,
        valid_exit_codes=valid_exit_codes,
    )


@then('the "{job_name}" ingest job completes successfully')
def step_impl(context, job_name):
    default_valid_exit_codes = (0,)
    valid_exit_codes_by_job_name = {
        "Bind PID": (0, 1),
        "Check for Access directory": (0, 179),
        "Check for manual normalized files": (0, 179),
        "Check if AIP is a file or directory": (0, 1),
        "Check if DIP should be generated": (0, 1),
        "Check if SIP is from Maildir Transfer": (0, 179),
        "Index AIP": (0, 179),
        "Is maildir AIP": (0, 179),
        "Normalize for access": (0, 1, 2),
        "Normalize for preservation": (0, 1, 2),
        "Normalize for thumbnails": (0, 1, 2),
        "Normalize service files for access": (0, 1, 2),
        "Normalize service files for thumbnails": (0, 1, 2),
        "Policy checks for access derivatives": (0, 1),
        "Policy checks for preservation derivatives": (0, 1),
        "Validate access derivatives": (0, 1),
        "Validate preservation derivatives": (0, 1),
    }
    valid_exit_codes = valid_exit_codes_by_job_name.get(
        job_name, default_valid_exit_codes
    )
    utils.assert_jobs_completed_successfully(
        context.api_clients_config,
        context.current_transfer["sip_uuid"],
        job_name=job_name,
        valid_exit_codes=valid_exit_codes,
    )


@then('the "{job_name}" job fails')
def step_impl(context, job_name):
    utils.assert_jobs_fail(
        context.api_clients_config,
        context.current_transfer["transfer_uuid"],
        job_name=job_name,
    )


@then('the "{job_name}" ingest job fails')
def step_impl(context, job_name):
    utils.assert_jobs_fail(
        context.api_clients_config,
        context.current_transfer["sip_uuid"],
        job_name=job_name,
    )


@then('the "{microservice_name}" microservice is executed')
def step_impl(context, microservice_name):
    utils.assert_microservice_executes(
        context.api_clients_config,
        context.current_transfer["transfer_uuid"],
        microservice_name,
    )


@then('the "{microservice_name}" ingest microservice is executed')
def step_impl(context, microservice_name):
    utils.assert_microservice_executes(
        context.api_clients_config,
        context.current_transfer["sip_uuid"],
        microservice_name,
    )


@then('the "{microservice_name}" microservice completes successfully')
def step_impl(context, microservice_name):
    utils.assert_jobs_completed_successfully(
        context.api_clients_config,
        context.current_transfer["transfer_uuid"],
        job_microservice=microservice_name,
    )


@then('the "{microservice_name}" ingest microservice completes successfully')
def step_impl(context, microservice_name):
    utils.assert_jobs_completed_successfully(
        context.api_clients_config,
        context.current_transfer["sip_uuid"],
        job_microservice=microservice_name,
    )


@then("the METS file contains a dmdSec with DDI metadata")
def step_impl(context):
    tree = etree.parse(context.current_transfer["aip_mets_location"])
    structmap = tree.find(
        'mets:structMap[@TYPE="physical"]', namespaces=context.mets_nsmap
    )
    transfer_dir = structmap.find(
        'mets:div[@LABEL="{}-{}"][@TYPE="Directory"]'.format(
            context.current_transfer["transfer_name"],
            context.current_transfer["sip_uuid"],
        ),
        namespaces=context.mets_nsmap,
    )
    error = (
        'The {} file does not contain any "Directory" entries in its physical '
        "structMap".format(context.current_transfer["aip_mets_location"])
    )
    assert len(transfer_dir), error
    objects_dir = transfer_dir.find(
        'mets:div[@LABEL="objects"]', namespaces=context.mets_nsmap
    )
    error = (
        'The {} file does not contain an "objects" directory entry in its physical '
        "structMap".format(context.current_transfer["aip_mets_location"])
    )
    assert len(objects_dir), error
    dmdsec_ids = objects_dir.attrib["DMDID"].strip().split(" ")
    dmdsecs_contain_ddi_metadata = False
    namespaces = context.mets_nsmap.copy()
    namespaces["ddi"] = "http://www.icpsr.umich.edu/DDI"
    for dmdsec_id in dmdsec_ids:
        ddi_codebook = tree.find(
            'mets:dmdSec[@ID="{}"]/mets:mdWrap/mets:xmlData/ddi:codebook'.format(
                dmdsec_id
            ),
            namespaces=namespaces,
        )
        if ddi_codebook is not None:
            dmdsecs_contain_ddi_metadata = True
    error = (
        "The {} file does not contain any ddi metadata in any of the dmdSec of "
        "the objects directory ({}) of the physical structMap".format(
            context.current_transfer["aip_mets_location"], dmdsec_ids
        )
    )
    assert dmdsecs_contain_ddi_metadata, error


@then(
    "there are {expected_object_count:d} {object_type} in the AIP METS with a DMDSEC containing DC metadata"
)
def step_impl(context, expected_object_count, object_type):
    ORIGINAL = "original objects"
    DIRS = "directories"
    dir_ids = []
    item_ids = []
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    dmd_sec_ids = utils.retrieve_md_section_ids(
        mets.tree, section="mets:dmdSec", md_type="DC", nsmap=context.mets_nsmap
    )
    for file in mets.all_files():
        for dmd_sec in file.dmdsecs:
            if dmd_sec.id_string in dmd_sec_ids:
                if file.mets_div_type == "Directory":
                    dir_ids.append(dmd_sec.id_string)
                elif file.mets_div_type == "Item" and file.use == "original":
                    item_ids.append(dmd_sec.id_string)
    err = (
        "The {} file does not contain the correct number of DC dmdSecs: {} expected {}"
    )
    if object_type == ORIGINAL:
        error = err.format(
            context.current_transfer["aip_mets_location"],
            len(item_ids),
            expected_object_count,
        )
        assert len(item_ids) == expected_object_count, error
    elif object_type == DIRS:
        error = err.format(
            context.current_transfer["aip_mets_location"],
            len(dir_ids),
            expected_object_count,
        )
        assert len(dir_ids) == expected_object_count, error
    else:
        raise NotImplementedError("Object type cannot be parsed out of METS yet")


@then(
    "there are {expected_entries_count:d} objects in the AIP METS with a rightsMD section containing PREMIS:RIGHTS"
)
def step_impl(context, expected_entries_count):
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    rights_linking_ids = utils.retrieve_rights_linking_object_identifiers(
        mets.tree, nsmap=context.mets_nsmap
    )
    error = "Expected objects with rightsMD sections: {} is incorrect: {}".format(
        expected_entries_count, len(rights_linking_ids)
    )
    assert len(rights_linking_ids) == expected_entries_count, error


@then("there are {expected_entries_count:d} PREMIS:RIGHTS entries")
def step_impl(context, expected_entries_count):
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    rights_md_ids = utils.retrieve_md_section_ids(
        mets.tree,
        section="mets:amdSec/mets:rightsMD",
        md_type="PREMIS:RIGHTS",
        nsmap=context.mets_nsmap,
    )
    error = "Expected objects with rightsMD sections: {} is incorrect: {}".format(
        expected_entries_count, len(rights_md_ids)
    )
    assert len(rights_md_ids) == expected_entries_count, error


@then(
    "there are {expected_entries_count:d} submission documents listed in the AIP METS as submission documentation"
)
def step_impl(context, expected_entries_count):
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    # Archivematica added submission documentation. We only care about
    # user submitted docs.
    METS = "METS.xml"
    submission_docs = [
        doc
        for doc in utils.get_submission_docs_from_structmap(
            mets.tree,
            context.current_transfer["transfer_name"],
            context.current_transfer["sip_uuid"],
            nsmap=context.mets_nsmap,
        )
        if doc.get("LABEL") != METS
    ]
    error = "Expected submission documents: {} is incorrect: {}".format(
        expected_entries_count, len(submission_docs)
    )
    assert len(submission_docs) == expected_entries_count, error


@then('the "{metadata_file}" file is in the reingest metadata directory')
def step_impl(context, metadata_file):
    utils.is_valid_download(
        utils.get_aip_file_location(
            context.current_transfer["reingest_extracted_aip_dir"],
            os.path.join("data", "objects", "metadata", metadata_file),
        )
    )


@then("the DIP is downloaded")
def step_impl(context):
    context.current_transfer.update(
        utils.get_dip(context.api_clients_config, context.current_transfer["sip_uuid"])
    )


@then("the DIP contains access copies for each original object in the transfer")
def step_impl(context):
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    # get the UUID of each 'original' file
    original_file_uuids = set(
        [fsentry.file_uuid for fsentry in mets.all_files() if fsentry.use == "original"]
    )
    assert original_file_uuids, format_original_files_error(context.current_transfer)
    # verify each file UUID has a matching entry in the objects directory of the DIP
    dip_file_uuids = set(
        [
            f[:36]
            for f in os.listdir(
                os.path.join(context.current_transfer["extracted_dip_dir"], "objects")
            )
        ]
    )
    error = "The DIP at {} does not contain access copies for all the original files of the {} AIP".format(
        context.current_transfer["extracted_dip_dir"],
        context.current_transfer["sip_uuid"],
    )
    assert original_file_uuids == dip_file_uuids, error


@then(
    "every metadata XML file in source-metadata.csv has a dmdSec with STATUS original "
    "that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content"
)
def step_impl(context):
    expected_dmdsec_status = ("original",)
    expected_mdwrap_mdtype = ("OTHER",)
    source_metadata_files = context.current_transfer["source_metadata_files"]
    assert (
        source_metadata_files
    ), "Could not extract the rows of source-metadata.csv in {}".format(
        context.current_transfer["extracted_aip_dir"]
    )
    mets = metsrw.METSDocument.fromfile(context.current_transfer["aip_mets_location"])
    errors = []
    for row in source_metadata_files:
        entry = mets.get_file(label=row["original_filename"])
        dmdsecs = [
            dmdsec
            for dmdsec in entry.dmdsecs
            if dmdsec.status in expected_dmdsec_status
            and dmdsec.contents.mdtype in expected_mdwrap_mdtype
            and dmdsec.contents.othermdtype == row["type_id"]
        ]
        if len(dmdsecs) != 1:
            errors.append(
                'Expected one dmdSec for filename "{}" with STATUS="{}" containing a '
                'mdWrap with OTHERMDTYPE="{}" in source-metadata.csv but got {}'.format(
                    row["original_filename"],
                    ", ".join(expected_dmdsec_status),
                    row["type_id"],
                    len(dmdsecs),
                )
            )
            continue
        mdwrap_text = utils.extract_document_text(dmdsecs[0].contents.document)
        metadata_file_text = utils.extract_document_text(row["document"])
        if (
            not mdwrap_text
            or not metadata_file_text
            or mdwrap_text != metadata_file_text
        ):
            errors.append(
                'Wrapped text of mdWrap[OTHERMDTYPE="{}"] does not match the text '
                'of the original metadata XML file "{}"'.format(
                    row["type_id"], row["metadata_filename"]
                )
            )
    assert not errors, "\n".join(errors)


@then(
    "every existing metadata XML file in the reingested source-metadata.csv has "
    "two dmdSecs with the same GROUPID, one with the original XML content which "
    "has been superseded by a new one that contains the updated XML content"
)
def step_impl(context):
    expected_dmdsec_status = ("original-superseded", "update")
    expected_mdwrap_mdtype = ("OTHER",)
    assert context.current_transfer[
        "source_metadata_files"
    ], "Could not extract the rows of the original source-metadata.csv in {}".format(
        context.current_transfer["reingest_extracted_aip_dir"]
    )
    assert context.current_transfer[
        "reingest_source_metadata_files"
    ], "Could not extract the rows of the reingested source-metadata.csv in {}".format(
        context.current_transfer["reingest_extracted_aip_dir"]
    )
    reingest_mets = metsrw.METSDocument.fromfile(
        context.current_transfer["reingest_aip_mets_location"]
    )
    # XXX: using lxml to bypass an issue with metsrw where a dmdSec with status
    #      `updated` resets the status of the previous dmdSec to `None`
    reingest_tree = etree.parse(context.current_transfer["reingest_aip_mets_location"])
    original_source_metadata_filenames = [
        row["metadata_filename"]
        for row in context.current_transfer["source_metadata_files"]
    ]
    rows = [
        row
        for row in context.current_transfer["reingest_source_metadata_files"]
        if row["metadata_filename"] in original_source_metadata_filenames
    ]
    assert rows, (
        "This reingest does not look like an update to existing metadata XML files. "
        "Could not find any of the original metadata XML files in the reingested "
        "source-metadata.csv file"
    )
    errors = []
    dmdsec_error_template = (
        'Expected one dmdSec for filename "{}" with STATUS="{}" containing a '
        'mdWrap with OTHERMDTYPE="{}" in source-metadata.csv but got {}'
    )
    for row in rows:
        entry = reingest_mets.get_file(label=row["original_filename"])
        all_dmdsecs = {}
        dmdsecs_errors = []
        for expected_status in expected_dmdsec_status:
            dmdsecs = []
            for dmdsec in entry.dmdsecs:
                # XXX: using lxml to bypass an issue with metsrw mentioned above
                if (
                    len(
                        reingest_tree.xpath(
                            '//mets:dmdSec[@ID="{}"][@STATUS="{}"]'.format(
                                dmdsec.id_string, expected_status
                            ),
                            namespaces=context.mets_nsmap,
                        )
                    )
                    == 1
                    and dmdsec.contents.mdtype in expected_mdwrap_mdtype
                    and dmdsec.contents.othermdtype == row["type_id"]
                ):
                    dmdsecs.append(dmdsec)
            if len(dmdsecs) != 1:
                dmdsecs_errors.append(
                    dmdsec_error_template.format(
                        row["original_filename"],
                        expected_status,
                        row["type_id"],
                        len(dmdsecs),
                    )
                )
                continue
            all_dmdsecs[expected_status] = dmdsecs[0]
        if dmdsecs_errors:
            errors.extend(dmdsecs_errors)
            continue
        group_ids = set([dmdsec.group_id for dmdsec in all_dmdsecs.values()])
        if len(group_ids) != 1:
            errors.append(
                'Expected the {} dmdSecs for filename "{}" to have the same '
                "GROUPID attribute but got {}".format(
                    " and ".join(expected_dmdsec_status),
                    row["original_filename"],
                    " and ".join(group_ids),
                )
            )
            continue
        update_dmdsec = all_dmdsecs["update"]
        mdwrap_text = utils.extract_document_text(update_dmdsec.contents.document)
        metadata_file_text = utils.extract_document_text(row["document"])
        if (
            not mdwrap_text
            or not metadata_file_text
            or mdwrap_text != metadata_file_text
        ):
            errors.append(
                'Wrapped text of mdWrap[OTHERMDTYPE="{}"] does not match the text '
                'of the updated metadata XML file "{}"'.format(
                    row["type_id"], row["metadata_filename"]
                )
            )
    assert not errors, "\n".join(errors)


@then(
    "every new metadata XML file in the reingested source-metadata.csv has a dmdSec "
    "with STATUS update that has a mdWrap with the specified OTHERMDTYPE which "
    "wraps the XML content"
)
def step_impl(context):
    expected_dmdsec_status = ("update",)
    expected_mdwrap_mdtype = ("OTHER",)
    assert context.current_transfer[
        "source_metadata_files"
    ], "Could not extract the rows of the original source-metadata.csv in {}".format(
        context.current_transfer["reingest_extracted_aip_dir"]
    )
    original_source_metadata_filenames = [
        row["metadata_filename"]
        for row in context.current_transfer["source_metadata_files"]
    ]
    assert context.current_transfer[
        "reingest_source_metadata_files"
    ], "Could not extract the rows of the reingested source-metadata.csv in {}".format(
        context.current_transfer["reingest_extracted_aip_dir"]
    )
    reingest_mets = metsrw.METSDocument.fromfile(
        context.current_transfer["reingest_aip_mets_location"]
    )
    # XXX: using lxml to bypass an issue with metsrw where a dmdSec with status
    #      `updated` resets the status of the previous dmdSec to `None`
    reingest_tree = etree.parse(context.current_transfer["reingest_aip_mets_location"])
    rows = [
        row
        for row in context.current_transfer["reingest_source_metadata_files"]
        if row["metadata_filename"] in original_source_metadata_filenames
    ]
    assert rows, (
        "Could not find any new metadata XML files in the reingested "
        "source-metadata.csv file"
    )
    errors = []
    dmdsec_error_template = (
        'Expected one dmdSec for filename "{}" with STATUS="{}" containing a '
        'mdWrap with OTHERMDTYPE="{}" in the reingested source-metadata.csv '
        "but got {}"
    )
    for row in rows:
        entry = reingest_mets.get_file(label=row["original_filename"])
        all_dmdsecs = {}
        dmdsecs_errors = []
        for expected_status in expected_dmdsec_status:
            dmdsecs = []
            for dmdsec in entry.dmdsecs:
                # XXX: using lxml to bypass an issue with metsrw mentioned above
                if (
                    len(
                        reingest_tree.xpath(
                            '//mets:dmdSec[@ID="{}"][@STATUS="{}"]'.format(
                                dmdsec.id_string, expected_status
                            ),
                            namespaces=context.mets_nsmap,
                        )
                    )
                    == 1
                    and dmdsec.contents.mdtype in expected_mdwrap_mdtype
                    and dmdsec.contents.othermdtype == row["type_id"]
                ):
                    dmdsecs.append(dmdsec)
            if len(dmdsecs) != 1:
                dmdsecs_errors.append(
                    dmdsec_error_template.format(
                        row["original_filename"],
                        ", ".join(expected_dmdsec_status),
                        row["type_id"],
                        len(dmdsecs),
                    )
                )
                continue
            all_dmdsecs[expected_status] = dmdsecs[0]
        if dmdsecs_errors:
            errors.extend(dmdsecs_errors)
            continue
        mdwrap_text = utils.extract_document_text(dmdsecs[0].contents.document)
        metadata_file_text = utils.extract_document_text(row["document"])
        if (
            not mdwrap_text
            or not metadata_file_text
            or mdwrap_text != metadata_file_text
        ):
            errors.append(
                'Wrapped text of mdWrap[OTHERMDTYPE="{}"] does not match the text '
                'of the original metadata XML file "{}"'.format(
                    row["type_id"], row["metadata_filename"]
                )
            )
    assert not errors, "\n".join(errors)
