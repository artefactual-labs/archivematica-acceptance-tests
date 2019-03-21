#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Steps for the black_box features.

These steps use the AM APIs to initiate transfers and validate the
contents of their AIPs without relying on user interface interactions.
"""

from __future__ import print_function, unicode_literals
import os
import time

from behave import given, when, then
from lxml import etree
import metsrw

import environment
from features.steps import utils


@given(
    'the transfer "DemoTransferCSV" is started with the '
    "automatedProcessingMCP processing configuration."
)
def step_impl(context):
    """Step 1"""
    if not utils.browse_default_ts_location(context):
        raise environment.EnvironmentError("Location cannot be verified")
    try:
        context.transfer_uuid = utils.start_transfer(context)
    except environment.EnvironmentError as err:
        assert False, "Error starting transfer: {}".format(err)


@given("an AIP has been created and stored")
def step_impl(context):
    context.execute_steps(
        'Given the transfer "DemoTransferCSV" is started with the'
        " automatedProcessingMCP processing configuration.\n"
        "When the Transfer is COMPLETE\n"
        "And the Ingest is COMPLETE\n"
    )


@given("an AIP has been reingested")
def step_impl(context):
    context.execute_steps(
        'Given the transfer "DemoTransferCSV" is started with the'
        " automatedProcessingMCP processing configuration.\n"
        "When the Transfer is COMPLETE\n"
        "And the Ingest is COMPLETE\n"
        "Then an AIP can be downloaded\n"
    )
    # Save the METS of the initial transfer
    context.initial_aip_mets_location = context.aip_mets_location
    try:
        context.transfer_uuid = utils.start_reingest(context)
    except environment.EnvironmentError as err:
        assert False, "Error starting reingest: {}".format(err)
    context.execute_steps("When the Transfer is COMPLETE\nAnd the Ingest is COMPLETE\n")


@when("the Transfer is COMPLETE")
def step_impl(context):
    """Step 2"""
    context.sip_uuid = None
    status = None
    resp = None
    try:
        while status not in ("COMPLETE", "FAILED"):
            time.sleep(environment.MEDIUM_WAIT)
            resp = utils.check_unit_status(context)
            if isinstance(resp, int) or resp is None:
                continue
            status = resp.get("status")
        if status == "COMPLETE":
            context.sip_uuid = resp.get("sip_uuid")
        else:
            assert False, "Error in transfer"
    except environment.EnvironmentError as err:
        assert False, "Error checking transfer (uuid: {}) status: {}".format(
            context.transfer_uuid, err
        )


@when("the Ingest is COMPLETE")
def step_impl(context):
    """Step 3"""
    status = None
    resp = None
    try:
        while status not in ("COMPLETE", "FAILED"):
            time.sleep(environment.MEDIUM_WAIT)
            resp = utils.check_unit_status(context, unit="ingest")
            if isinstance(resp, int) or resp is None:
                continue
            status = resp.get("status")
        if status == "COMPLETE":
            return
        else:
            assert False, "Error in ingest"
    except environment.EnvironmentError as err:
        assert False, "Error checking ingest (uuid: {}) status: {}".format(
            context.sip_uuid, err
        )


@when("the AIP is downloaded")
def step_impl(context):
    context.execute_steps("Then an AIP can be downloaded")


@when("the reingest processing is complete")
def step_impl(context):
    context.execute_steps("Then an AIP can be downloaded\n")


@then("an AIP can be downloaded")
def step_impl(context):
    """Step 4"""
    # Download of individual files is package-type agnostic.
    context.aip_mets_location = utils.download_mets(context)
    print("\n", "AIP output to:", context.aip_mets_location, "\n")


@then("the AIP METS can be accessed and parsed by mets-reader-writer")
def step_impl(context):
    """Step 5"""
    mets = metsrw.METSDocument.fromfile(context.aip_mets_location)
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
    mets = metsrw.METSDocument.fromfile(context.aip_mets_location)
    # cache each query to the SS browse endpoint by directory name
    cached_directories = {}
    # look for an 'objects' directory in the transfer directory
    contains_objects_dir = False
    objects_dir = os.path.join(context.demo_transfer_path, "objects")
    objects_dir_browse_result = utils.browse_default_ts_location(context, objects_dir)
    if objects_dir_browse_result:
        contains_objects_dir = True
        cached_directories[objects_dir] = objects_dir_browse_result
    # get the paths (before sanitization) of each 'original' file
    original_file_paths = [
        utils.get_path_before_sanitization(fsentry, contains_objects_dir)
        for fsentry in mets.all_files()
        if fsentry.use == "original"
    ]
    # verify each path has an entry in the transfer directory
    for file_path in original_file_paths:
        file_dir = os.path.join(context.demo_transfer_path, os.path.dirname(file_path))
        file_name = os.path.basename(file_path)
        if file_dir not in cached_directories:
            file_dir_browse_result = utils.browse_default_ts_location(context, file_dir)
            cached_directories[file_dir] = file_dir_browse_result
        assert file_name in cached_directories[file_dir]["entries"]


@then("the AIP contains a file called README.html")
def step_impl(context):
    readme_file = "{}-{}/data/README.html".format(
        context.transfer_name, context.sip_uuid
    )
    extracted_file = utils.download_file(context, readme_file)
    utils.is_valid_download(extracted_file)


@then("the AIP contains a METS.xml file in the data directory")
def step_impl(context):
    extracted_file = utils.download_mets(context)
    utils.is_valid_download(extracted_file)


@then("the AIP conforms to expected content and structure")
def step_impl(context):
    context.aip_location = utils.download_aip(context)
    extracted_aip_dir = utils.extract_aip(context)
    expected_directories = ["objects", "logs", "objects/submissionDocumentation"]
    for directory in expected_directories:
        path = "data/{}".format(directory)
        assert os.path.isdir(os.path.join(extracted_aip_dir, path))


@then(
    "the fileSec of the AIP METS will record every file in the objects "
    "and metadata directories of the AIP"
)
def step_impl(context):
    context.aip_location = utils.download_aip(context)
    extracted_aip_dir = utils.extract_aip(context)
    tree = etree.parse(context.aip_mets_location)
    filesec_files = utils.get_filesec_files(tree, nsmap=context.mets_nsmap)
    for filesec_file in filesec_files:
        flocat = filesec_file.find("mets:FLocat", namespaces=context.mets_nsmap)
        href = flocat.attrib["{http://www.w3.org/1999/xlink}href"]
        path = "data/{}".format(href)
        assert os.path.exists(os.path.join(extracted_aip_dir, path))


@then(
    "the physical structMap of the AIP METS accurately reflects "
    "the physical layout of the AIP"
)
def step_impl(context):
    context.aip_location = utils.download_aip(context)
    extracted_aip_dir = utils.extract_aip(context)
    root_path = "{}/data".format(extracted_aip_dir)
    tree = etree.parse(context.aip_mets_location)
    structmap = tree.find(
        'mets:structMap[@TYPE="physical"]', namespaces=context.mets_nsmap
    )
    transfer_dir = structmap.find(
        'mets:div[@LABEL="{}-{}"][@TYPE="Directory"]'.format(
            context.transfer_name, context.sip_uuid
        ),
        namespaces=context.mets_nsmap,
    )
    for item in transfer_dir:
        utils.assert_structmap_item_path_exists(item, root_path)


@then("every object in the AIP has been assigned a UUID in the AIP METS")
def step_impl(context):
    tree = etree.parse(context.aip_mets_location)
    filesec_files = utils.get_filesec_files(tree, nsmap=context.mets_nsmap)
    for filesec_file in filesec_files:
        # remove the 'file-' prefix from the UUID of the file
        file_uuid = filesec_file.attrib["ID"].split("file-")[-1]
        amdsec_id = filesec_file.attrib["ADMID"]
        amdsec = tree.find(
            'mets:amdSec[@ID="{}"]'.format(amdsec_id), namespaces=context.mets_nsmap
        )
        object_uuid = amdsec.findtext(
            "mets:techMD/mets:mdWrap/mets:xmlData/premis:object/"
            "premis:objectIdentifier/premis:objectIdentifierValue",
            namespaces=context.mets_nsmap,
        )
        assert object_uuid == file_uuid


@then("every object in the objects and metadata directories has an amdSec")
def step_impl(context):
    tree = etree.parse(context.aip_mets_location)
    filesec_files = utils.get_filesec_files(tree, nsmap=context.mets_nsmap)
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
    tree = etree.parse(context.aip_mets_location)
    premis_events = tree.findall(
        'mets:amdSec/mets:techMD/mets:mdWrap[@MDTYPE="PREMIS:EVENT"]/'
        "mets:xmlData/premis:event",
        namespaces=context.mets_nsmap,
    )
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


@then("there is a PREMIS reingestion event for each original object in the AIP METS")
def step_impl(context):
    event_type = "reingestion"
    types = {"reingestion": "reingestion"}
    mets = metsrw.METSDocument.fromfile(context.aip_mets_location)
    original_files = [
        fsentry for fsentry in mets.all_files() if fsentry.use == "original"
    ]
    for fsentry in original_files:
        events = utils.get_premis_events_by_type(fsentry, types[event_type])
        error = "Expected one {} event in the METS for file {}".format(
            event_type, fsentry.path
        )
        assert len(events) == 1, error


@then("there is a current and a superseded techMD for each original object")
def step_impl(context):
    mets = metsrw.METSDocument.fromfile(context.aip_mets_location)
    original_files = [
        fsentry for fsentry in mets.all_files() if fsentry.use == "original"
    ]
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
    reingest_mets = metsrw.METSDocument.fromfile(context.aip_mets_location)
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
    initial_mets = metsrw.METSDocument.fromfile(context.initial_aip_mets_location)
    original_files = [
        fsentry for fsentry in initial_mets.all_files() if fsentry.use == "original"
    ]
    for fsentry in original_files:
        if utils.get_premis_events_by_type(fsentry, "normalization"):
            error = "Expected normalized file {} to be deleted after reingest".format(
                fsentry.path
            )
            assert fsentry.file_uuid in deleted_file_uuids, error
