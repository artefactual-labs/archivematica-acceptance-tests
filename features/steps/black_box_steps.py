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


def format_original_files_error(transfer):
    return 'The {} file does not contain any "original" files in its fileSec'.format(
        transfer["aip_mets_location"]
    )


def format_no_files_error(transfer):
    return "The {} file does not contain any files in its fileSec".format(
        transfer["aip_mets_location"]
    )


@given("an AIP has been created and stored")
def step_impl(context):
    sample_transfer_path = os.path.join("SampleTransfers", "DemoTransferCSV")
    transfer = utils.create_sample_transfer(
        context.api_clients_config, sample_transfer_path
    )
    context.current_transfer = transfer


@given("an AIP has been reingested")
def step_impl(context):
    context.execute_steps("Given an AIP has been created and stored\n")
    reingest = utils.create_reingest(
        context.api_clients_config, context.current_transfer
    )
    context.current_transfer.update(reingest)


@when("the AIP is downloaded")
def step_impl(context):
    utils.is_valid_download(context.current_transfer["aip_mets_location"])


@when("the reingest processing is complete")
def step_impl(context):
    utils.is_valid_download(context.current_transfer["aip_mets_location"])
    utils.is_valid_download(context.current_transfer["reingest_aip_mets_location"])


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
    # look for an 'objects' directory in the transfer directory
    contains_objects_dir = False
    objects_dir = os.path.join(context.current_transfer["transfer_path"], "objects")
    objects_dir_browse_result = utils.browse_default_ts_location(
        context.api_clients_config, objects_dir
    )
    if objects_dir_browse_result:
        contains_objects_dir = True
        cached_directories[objects_dir] = objects_dir_browse_result
    # get the paths (before sanitization) of each 'original' file
    original_file_paths = [
        utils.get_path_before_sanitization(fsentry, contains_objects_dir)
        for fsentry in mets.all_files()
        if fsentry.use == "original"
    ]
    assert original_file_paths, format_original_files_error(context.current_transfer)
    # verify each path has an entry in the transfer directory
    for file_path in original_file_paths:
        file_dir = os.path.join(
            context.current_transfer["transfer_path"], os.path.dirname(file_path)
        )
        file_name = os.path.basename(file_path)
        if file_dir not in cached_directories:
            file_dir_browse_result = utils.browse_default_ts_location(
                context.api_clients_config, file_dir
            )
            cached_directories[file_dir] = file_dir_browse_result
        assert file_name in cached_directories[file_dir]["entries"]


@then("the AIP contains a file called README.html")
def step_impl(context):
    readme_file = utils.get_aip_file_location(
        context.current_transfer["extracted_aip_dir"],
        os.path.join("data", "README.html"),
    )
    utils.is_valid_download(readme_file)


@then("the AIP contains a METS.xml file in the data directory")
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
    "the physical structMap of the AIP METS accurately reflects "
    "the physical layout of the AIP"
)
def step_impl(context):
    root_path = os.path.join(context.current_transfer["extracted_aip_dir"], "data")
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
            "mets:techMD/mets:mdWrap/mets:xmlData/premis3:object/"
            'premis3:objectIdentifier/premis3:objectIdentifierType[text()="UUID"]/'
            "../premis3:objectIdentifierValue",
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
        "mets:xmlData/premis3:event",
        namespaces=context.mets_nsmap,
    )
    error = "The {} file does not contain any PREMIS events".format(
        context.current_transfer["aip_mets_location"]
    )
    assert premis_events, error
    for event in premis_events:
        event_agents = event.findall(
            "premis3:linkingAgentIdentifier", namespaces=context.mets_nsmap
        )
        event_agent_types = set(
            [
                event_agent.findtext(
                    "premis3:linkingAgentIdentifierType", namespaces=context.mets_nsmap
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
    # map the event types as written in the feature file
    # to what AM outputs in the METS
    types = {
        "file format identification": "format identification",
        "ingestion": "ingestion",
        "message digest calculation": "message digest calculation",
        "reingestion": "reingestion",
        "virus scanning": "virus check",
    }
    mets_path = context.current_transfer["aip_mets_location"]
    if event_type == "reingestion":
        mets_path = context.current_transfer["reingest_aip_mets_location"]
    mets = metsrw.METSDocument.fromfile(mets_path)
    original_files = [
        fsentry for fsentry in mets.all_files() if fsentry.use == "original"
    ]
    assert original_files, format_original_files_error(context.current_transfer)
    for fsentry in original_files:
        events = utils.get_premis_events_by_type(fsentry, types[event_type])
        error = "Expected one {} event in the METS for file {}".format(
            event_type, fsentry.path
        )
        assert len(events) == 1, error


use_step_matcher("parse")


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
