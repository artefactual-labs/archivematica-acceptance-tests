"""Steps for the MediaConch-related Features."""

import logging
import os

from behave import when, then, given
from lxml import etree

from features.steps import utils


logger = logging.getLogger("amauat.steps.mediaconch")


MC_EVENT_DETAIL_PREFIX = 'program="MediaConch"'
MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX = (
    "MediaConch implementation check result:"
)
MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX = "MediaConch policy check result"
POLICIES_DIR = "etc/mediaconch-policies"


# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------


@given("directory {transfer_path} contains files that are all {file_validity}" " .mkv")
def step_impl(context, transfer_path, file_validity):
    pass


@given(
    "directory {transfer_path} contains files that will all be normalized"
    " to {file_validity} .mkv"
)
def step_impl(context, transfer_path, file_validity):
    pass


@given(
    "directory {transfer_path} contains a processing config that does"
    " normalization for preservation, etc."
)
def step_impl(context, transfer_path):
    """Details: transfer must contain a processing config that creates a SIP,
    does normalization for preservation, approves normalization, and creates an
    AIP without storing it
    """


@given(
    "directory {transfer_path} contains a processing config that does"
    " normalization for access, etc."
)
def step_impl(context, transfer_path):
    """Details: transfer must contain a processing config that creates a SIP,
    does normalization for access, approves normalization, and creates an
    AIP without storing it
    """


@given("a base processing configuration for MediaConch tests")
def step_impl(context):
    """Create a processing configuration that is a base for all policy
    check-targetted workflows.
    """
    context.execute_steps(
        "Given that the user has ensured that the default processing config is"
        " in its default state\n"
        'And the processing config decision "Assign UUIDs to directories" is'
        ' set to "No"\n'
        'And the processing config decision "Perform policy checks on'
        ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
        ' derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Yes"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
        ' single SIP and continue processing"\n'
        'And the processing config decision "Approve normalization" is set to'
        ' "Yes"\n'
        'And the processing config decision "Select file format identification'
        ' command (Submission documentation & metadata)" is set to'
        ' "Yes"\n'
        'And the processing config decision "Bind PIDs" is set to "No"\n'
        'And the processing config decision "Store AIP location" is set to'
        ' "Store AIP in standard Archivematica Directory"\n'
        'And the processing config decision "Document empty directories" is set'
        ' to "No"\n'
        'And the processing config decision "Generate thumbnails" is set to'
        ' "No"\n'
        'And the processing config decision "Upload DIP" is set to'
        ' "Do not upload DIP"'
    )


@given("a processing configuration for policy checks on preservation" " derivatives")
def step_impl(context):
    context.execute_steps(
        "Given a base processing configuration for MediaConch tests\n"
        'And the processing config decision "Perform policy checks on'
        ' preservation derivatives" is set to "Yes"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"'
    )


@given(
    "a processing configuration for conformance checks on preservation" " derivatives"
)
def step_impl(context):
    context.execute_steps(
        "Given a base processing configuration for MediaConch tests\n"
        'And the processing config decision "Approve normalization" is set to'
        ' "None"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"'
    )


@given("a processing configuration for MediaConch challenging file testing")
def step_impl(context):
    context.execute_steps(
        "Given a base processing configuration for MediaConch tests\n"
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Identify using Siegfried"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"'
    )


@given(
    "transfer path {transfer_path} which contains files that, when"
    " normalized to MKV, are known to have broken MediaConch v. 16.12"
    " validation checks"
)
def step_impl(context, transfer_path):
    """We won't confirm it here, but if you attempt to run an implementation
    check on the .mkv file produced by normalizing the file(s) in this
    ``transfer_path`` using MediaConch v. 16.12, then MediaConch will hang. See
    https://github.com/artefactual/archivematica/issues/966.
    """


@given("a processing configuration for conformance checks on access" " derivatives")
def step_impl(context):
    context.execute_steps(
        "Given a base processing configuration for MediaConch tests\n"
        'And the processing config decision "Approve normalization" is set to'
        ' "None"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for access"'
    )


@given("a processing configuration for policy checks on access derivatives")
def step_impl(context):
    context.execute_steps(
        "Given a base processing configuration for MediaConch tests\n"
        'And the processing config decision "Perform policy checks on'
        ' access derivatives" is set to "Yes"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for access"\n'
        'And the processing config decision "Store AIP" is set to "Yes"'
    )


@given("a processing configuration for policy checks on originals")
def step_impl(context):
    context.execute_steps(
        "Given a base processing configuration for MediaConch tests\n"
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "Yes"\n'
        'And the processing config decision "Normalize" is set to "Do not'
        ' normalize"\n'
        'And the processing config decision "Store AIP" is set to "Yes"'
    )


@given("a processing configuration for conformance checks on originals")
def step_impl(context):
    context.execute_steps(
        "Given a base processing configuration for MediaConch tests\n"
        'And the processing config decision "Normalize" is set to "Do not'
        ' normalize"\n'
    )


@given(
    "MediaConch policy file {policy_file} is present in the local"
    " etc/mediaconch-policies/ directory"
)
def step_impl(context, policy_file):
    assert policy_file in os.listdir(POLICIES_DIR)


@given(
    "directory {transfer_path} contains files that, when normalized, will"
    " all {do_files_conform} to {policy_file}"
)
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given(
    "directory {transfer_path}/manualNormalization/preservation/ contains a"
    " file manually normalized for preservation that will"
    "{do_files_conform} to {policy_file}"
)
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given(
    "directory {transfer_path}/manualNormalization/access/ contains a"
    " file manually normalized for access that will {do_files_conform}"
    " to {policy_file}"
)
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given(
    "directory {transfer_path} contains files that all do {do_files_conform}"
    " to {policy_file}"
)
def step_impl(context, transfer_path, do_files_conform, policy_file):
    pass


@given(
    'an FPR rule with purpose "{purpose}", format "{format_}", and command'
    ' "{command}"'
)
def step_impl(context, purpose, format_, command):
    context.am_user.browser.ensure_fpr_rule(purpose, format_, command)


# Whens
# ------------------------------------------------------------------------------


@when("the user edits the FPR rule to transcode .mkv files to .mkv for access")
def step_impl(context):
    context.am_user.browser.change_normalization_rule_command(
        "Access Generic MKV", "Transcoding to mkv with ffmpeg"
    )


@when("the user edits the FPR rule to transcode .mov files to .mkv for access")
def step_impl(context):
    context.am_user.browser.change_normalization_rule_command(
        "Access Generic MOV", "Transcoding to mkv with ffmpeg"
    )


@when("the user uploads the policy file {policy_file}")
def step_impl(context, policy_file):
    policy_path = get_policy_path(policy_file)
    context.am_user.browser.upload_policy(policy_path)


@when("the user ensures there is an FPR command that uses policy file" " {policy_file}")
def step_impl(context, policy_file):
    policy_path = get_policy_path(policy_file)
    context.am_user.browser.ensure_fpr_policy_check_command(policy_file, policy_path)


# TODO: this step could be generalized to support any purpose/format/command
# triple.
@when(
    "the user ensures there is an FPR rule with purpose {purpose} that"
    " validates Generic MKV files against policy file {policy_file}"
)
def step_impl(context, purpose, policy_file):
    context.am_user.browser.ensure_fpr_rule(
        purpose,
        "Video: Matroska: Generic MKV (fmt/569)",
        context.am_user.browser.get_policy_command_description(policy_file),
    )


# Thens
# ------------------------------------------------------------------------------


@then("validation micro-service output is {microservice_output}")
def step_impl(context, microservice_output):
    context.scenario.job = context.am_user.browser.parse_job(
        "Validate formats", context.scenario.transfer_uuid
    )
    assert context.scenario.job.get("job_output") == microservice_output


@then(
    "the submissionDocumentation directory of the AIP {contains} a copy of"
    " the MediaConch policy file {policy_file}"
)
def step_impl(context, contains, policy_file):
    aip_path = context.scenario.aip_path
    original_policy_path = os.path.join(POLICIES_DIR, policy_file)
    aip_policy_path = os.path.join(
        aip_path, "data", "objects", "submissionDocumentation", "policies", policy_file
    )
    if contains in ("contains", "does contain"):
        assert os.path.isfile(original_policy_path)
        assert os.path.isfile(aip_policy_path), (
            "There is no MediaConch policy file in the AIP at"
            " {}!".format(aip_policy_path)
        )
        with open(original_policy_path) as filei:
            original_policy = filei.read().strip()
        with open(aip_policy_path) as filei:
            aip_policy = filei.read().strip()
        assert aip_policy == original_policy, (
            "The local policy file at {} is different from the one in the AIP"
            " at {}".format(original_policy_path, aip_policy_path)
        )
    else:
        assert not os.path.isfile(aip_policy_path), (
            "There is a MediaConch policy file in the AIP at {} but there"
            " shouldn't be!".format(aip_policy_path)
        )


@then(
    "the transfer logs directory of the AIP {contains} a copy of the"
    " MediaConch policy file {policy_file}"
)
def step_impl(context, contains, policy_file):
    aip_path = context.scenario.aip_path
    original_policy_path = os.path.join(POLICIES_DIR, policy_file)
    policy_file_no_ext, _ = os.path.splitext(policy_file)
    transfer_dirname = "{}-{}".format(
        context.scenario.transfer_name, context.scenario.transfer_uuid
    )
    aip_policy_path = os.path.join(
        aip_path,
        "data",
        "logs",
        "transfers",
        transfer_dirname,
        "logs",
        "policyChecks",
        policy_file_no_ext,
        policy_file,
    )
    if contains in ("contains", "does contain"):
        assert os.path.isfile(original_policy_path)
        assert os.path.isfile(aip_policy_path), (
            "There is no MediaConch policy file in the AIP at"
            " {}!".format(aip_policy_path)
        )
        with open(original_policy_path) as filei:
            original_policy = filei.read().strip()
        with open(aip_policy_path) as filei:
            aip_policy = filei.read().strip()
        assert aip_policy == original_policy, (
            "The local policy file at {} is different from the one in the AIP"
            " at {}".format(original_policy_path, aip_policy_path)
        )
    else:
        assert not os.path.isfile(aip_policy_path), (
            "There is a MediaConch policy file in the AIP at {} but there"
            " shouldn't be!".format(aip_policy_path)
        )


@then(
    "the transfer logs directory of the AIP contains a MediaConch policy"
    " check output file for each policy file tested against {policy_file}"
)
def step_impl(context, policy_file):
    policy_file_no_ext, _ = os.path.splitext(policy_file)
    aip_path = context.scenario.aip_path
    assert policy_file_no_ext, "policy_file_no_ext is falsey!"
    transfer_dirname = "{}-{}".format(
        context.scenario.transfer_name, context.scenario.transfer_uuid
    )
    aip_policy_outputs_path = os.path.join(
        aip_path,
        "data",
        "logs",
        "transfers",
        transfer_dirname,
        "logs",
        "policyChecks",
        policy_file_no_ext,
    )
    assert os.path.isdir(aip_policy_outputs_path), (
        "We expected {} to be a directory but it either does not exist or it is"
        " not a directory".format(aip_policy_outputs_path)
    )
    contents = os.listdir(aip_policy_outputs_path)
    assert contents
    file_paths = [
        x
        for x in [os.path.join(aip_policy_outputs_path, y) for y in contents]
        if os.path.isfile(x) and os.path.splitext(x)[1] == ".xml"
    ]
    assert file_paths, "There are no files in dir {}!".format(aip_policy_outputs_path)
    for fp in file_paths:
        with open(fp) as f:
            doc = etree.parse(f)
            root_tag = doc.getroot().tag
            expected_root_tag = "{https://mediaarea.net/mediaconch}MediaConch"
            assert root_tag == expected_root_tag, (
                "The root tag of file {} was expected to be {} but was actually"
                " {}".format(fp, expected_root_tag, root_tag)
            )


@then(
    "the logs directory of the AIP contains a MediaConch policy check output"
    " file for each policy file tested against {policy_file}"
)
def step_impl(context, policy_file):
    policy_file_no_ext, _ = os.path.splitext(policy_file)
    aip_path = context.scenario.aip_path
    assert policy_file_no_ext, "policy_file_no_ext is falsey!"
    aip_policy_outputs_path = os.path.join(
        aip_path, "data", "logs", "policyChecks", policy_file_no_ext
    )
    assert os.path.isdir(aip_policy_outputs_path)
    contents = os.listdir(aip_policy_outputs_path)
    assert contents
    file_paths = [
        x
        for x in [os.path.join(aip_policy_outputs_path, y) for y in contents]
        if os.path.isfile(x) and os.path.splitext(x)[1] == ".xml"
    ]
    assert file_paths, "There are no files in dir {}!".format(aip_policy_outputs_path)
    for fp in file_paths:
        with open(fp) as f:
            doc = etree.parse(f)
            assert doc.getroot().tag == "{https://mediaarea.net/mediaconch}MediaConch"


@then(
    "validate preservation derivatives micro-service output is" " {microservice_output}"
)
def step_impl(context, microservice_output):
    utils.ingest_ms_output_is(
        "Validate preservation derivatives", microservice_output, context
    )


@then("validate access derivatives micro-service output is" " {microservice_output}")
def step_impl(context, microservice_output):
    utils.ingest_ms_output_is(
        "Validate access derivatives", microservice_output, context
    )


@then(
    "all preservation conformance checks in the normalization report have"
    " value {validation_result}"
)
def step_impl(context, validation_result):
    utils.all_normalization_report_columns_are(
        "preservation_conformance_check", validation_result, context
    )


@then(
    "all access conformance checks in the normalization report have value"
    " {validation_result}"
)
def step_impl(context, validation_result):
    utils.all_normalization_report_columns_are(
        "access_conformance_check", validation_result, context
    )


@then(
    "all PREMIS implementation-check-type validation events have"
    " eventOutcome = {event_outcome}"
)
def step_impl(context, event_outcome):
    events = []
    for e in context.am_user.mets.get_premis_events(
        context.am_user.browser.get_mets(
            context.scenario.transfer_name,
            context.am_user.browser.get_sip_uuid(context.scenario.transfer_name),
        )
    ):
        if (
            e["event_type"] == "validation"
            and e["event_detail"].startswith(MC_EVENT_DETAIL_PREFIX)
            and e["event_outcome_detail_note"].startswith(
                MC_EVENT_OUTCOME_DETAIL_NOTE_IMPLEMENTATION_CHECK_PREFIX
            )
        ):
            events.append(e)
    assert events
    for e in events:
        assert e["event_outcome"] == event_outcome


@then(
    "policy checks for preservation derivatives micro-service output is"
    " {microservice_output}"
)
def step_impl(context, microservice_output):
    name = "Policy checks for preservation derivatives"
    utils.ingest_ms_output_is(name, microservice_output, context)


@then(
    "policy checks for access derivatives micro-service output is"
    " {microservice_output}"
)
def step_impl(context, microservice_output):
    name = "Policy checks for access derivatives"
    utils.ingest_ms_output_is(name, microservice_output, context)


@then("all policy check for access derivatives tasks indicate {event_outcome}")
def step_impl(context, event_outcome):
    policy_check_tasks = [
        t
        for t in context.scenario.job["tasks"].values()
        if t["stdout"].startswith("Running Check against policy ")
    ]
    assert policy_check_tasks
    if event_outcome == "pass":
        for task in policy_check_tasks:
            assert "All policy checks passed:" in task["stdout"]
            assert task["exit_code"] == "0"
    else:
        for task in policy_check_tasks:
            assert '"eventOutcomeInformation": "fail"' in task["stdout"]


@then("all policy check for originals tasks indicate {event_outcome}")
def step_impl(context, event_outcome):
    policy_check_tasks = [
        t
        for t in context.scenario.job["tasks"].values()
        if t["stdout"].startswith("Running Check against policy ")
    ]
    assert policy_check_tasks
    if event_outcome == "pass":
        for task in policy_check_tasks:
            assert "All policy checks passed:" in task["stdout"]
            assert task["exit_code"] == "0"
    else:
        for task in policy_check_tasks:
            assert '"eventOutcomeInformation": "fail"' in task["stdout"]


@then(
    "all PREMIS policy-check-type validation events have eventOutcome ="
    " {event_outcome}"
)
def step_impl(context, event_outcome):
    events = []
    for e in context.am_user.mets.get_premis_events(
        context.am_user.browser.get_mets_via_api(
            context.scenario.transfer_name,
            context.am_user.browser.get_sip_uuid(context.scenario.transfer_name),
        )
    ):
        if (
            e["event_type"] == "validation"
            and e["event_detail"].startswith(MC_EVENT_DETAIL_PREFIX)
            and e["event_outcome_detail_note"].startswith(
                MC_EVENT_OUTCOME_DETAIL_NOTE_POLICY_CHECK_PREFIX
            )
        ):
            events.append(e)
    assert events
    for e in events:
        assert e["event_outcome"] == event_outcome


@then(
    "all original files in the transfer are identified as PRONOM fmt/199"
    " (MPEG-4 Media File)"
)
def step_impl(context):
    for task in context.scenario.job["tasks"].values():
        assert "fmt/199" in task["stdout"]


# ==============================================================================
# Helper Functions
# ==============================================================================


def get_policy_path(policy_file):
    return os.path.realpath(os.path.join(POLICIES_DIR, policy_file))
