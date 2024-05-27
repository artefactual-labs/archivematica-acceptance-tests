"""Steps for the CCA DIP Feature."""

import csv
import logging
import os
import subprocess
import time
import zipfile

from behave import given
from behave import then
from behave import when

logger = logging.getLogger("amauat.steps.ccadip")


# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------


@given(
    "Tim has configured the automation-tools DIP creation bash script with"
    " all the required parameters"
)
def step_impl(context):
    # Check if the DIP creation script exists and is executable
    context.script = os.path.join(context.AUTOMATION_TOOLS_PATH, "create_dip_script.sh")
    assert os.path.isfile(context.script)
    assert os.access(context.script, os.X_OK)

    # Get AIP UUID, transer name and output dir from user data
    userdata = context.config.userdata
    context.aip_uuid = userdata.get("aip_uuid")
    context.transfer_name = userdata.get("transfer_name")
    context.output_dir = userdata.get("output_dir")
    assert context.aip_uuid
    assert context.transfer_name
    assert context.output_dir


@given("he has created that AIP using the current version of Archivematica (1.6.x)")
def step_impl(context):
    # Not the best way to check the AIP existence
    # as the request won't fail if AM is in debug mode.
    # Should we check directly in the SS API?
    context.am_user.browser.navigate_to_aip_in_archival_storage(context.aip_uuid)


# Whens
# ------------------------------------------------------------------------------


@when("he executes the DIP creation script")
def step_impl(context):
    output = subprocess.check_output([context.script], stderr=subprocess.STDOUT)
    logger.info("Create DIP script output:\n%s", output.decode())


# Thens
# ------------------------------------------------------------------------------


@then(
    "the script retrieves the AIP and creates a new DIP named with the"
    " original Transfer name appended with the AIP UUID and “_DIP”"
)
def step_impl(context):
    dip_name = f"{context.transfer_name}_{context.aip_uuid}_DIP"
    context.dip_path = os.path.join(context.output_dir, dip_name)
    assert os.path.exists(context.dip_path)


@then("the DIP METS XML file that describes the contents of the DIP")
def step_impl(context):
    mets_filename = f"METS.{context.aip_uuid}.xml"
    context.mets_path = os.path.join(context.dip_path, mets_filename)
    assert os.path.exists(context.mets_path)


@then(
    "the DIP objects directory contains one zip container with all objects"
    " from the original transfer"
)
def step_impl(context):
    objects_path = os.path.join(context.dip_path, "objects")
    context.zip_path = os.path.join(objects_path, f"{context.transfer_name}.zip")
    assert os.path.exists(context.zip_path)


@then(
    "each DIP object file has its original filename and last modified date"
    " from the original transfer"
)
def step_impl(context):
    # Get objects files info from CSV file
    userdata = context.config.userdata
    files_csv_path = userdata.get("files_csv")
    files = []
    with open(files_csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            filename = row["filename"]
            if filename.startswith("./"):
                filename = filename[2:]
            files.append({"filename": filename, "lastmodified": row["lastmodified"]})
    assert files
    # Check file info in ZIP files
    with zipfile.ZipFile(context.zip_path, "r") as zip_file:
        for file_info in zip_file.infolist():
            # Strip transfer name and '/', the main folder will end empty
            filename = file_info.filename[len(context.transfer_name) + 1 :]
            # Ignore main folder, METS, submissionDocumentation and directories
            if (
                not filename
                or filename == f"METS.{context.aip_uuid}.xml"
                or filename.startswith("submissionDocumentation")
                or filename.endswith("/")
            ):
                continue
            lastmodified = int(time.mktime(file_info.date_time + (0, 0, -1)))
            # Find file by filename in file info from CSV
            csv_info = next((x for x in files if x["filename"] == filename), None)
            assert csv_info
            # Check lastmodified date, if present in CSV
            csv_lastmodified = csv_info["lastmodified"]
            if not csv_info["lastmodified"]:
                continue
            csv_lastmodified = int(csv_info["lastmodified"])
            # Somehow, between getting the last modified date from the METS file,
            # setting it in the DIP files with os.utime(), zipping the files and
            # getting it in here with infolist(), a mismatch of a second is found
            # in some of the files. No milliseconds are involved in the process so
            # this should not be a rounding issue.
            assert csv_lastmodified - 1 <= lastmodified <= csv_lastmodified + 1


@then(
    "the DIP zip file includes a copy of the submissionDocumentation from the original Transfer"
)
def step_impl(context):
    sub_folder = f"{context.transfer_name}/submissionDocumentation/"
    with zipfile.ZipFile(context.zip_path, "r") as zip_file:
        assert sub_folder in zip_file.namelist()


@then("a copy of the AIP METS file generated during ingest")
def step_impl(context):
    mets_filename = f"{context.transfer_name}/METS.{context.aip_uuid}.xml"
    with zipfile.ZipFile(context.zip_path, "r") as zip_file:
        assert mets_filename in zip_file.namelist()


@then(
    "the DIP is stored locally in the output directory specified in the script parameters"
)
def step_impl(context):
    # Already checked in previous steps
    pass
