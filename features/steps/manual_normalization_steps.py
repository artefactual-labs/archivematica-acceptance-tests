"""Steps for the Manual Normalization Feature."""

import logging

from behave import then, given


logger = logging.getLogger("amauat.steps.manualnormalization")


# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------


@given("a processing configuration for testing manual normalization")
def step_impl(context):
    """Create a processing configuration that moves a transfer through to
    "Store AIP" and runs normalization for preservation.
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
        ' command (Transfer)" is set to "Identify using Fido"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
        ' single SIP and continue processing"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"\n'
        'And the processing config decision "Approve normalization" is set to'
        ' "Yes"\n'
        'And the processing config decision "Select file format identification'
        ' command (Submission documentation & metadata)" is set to'
        ' "Identify using Fido"\n'
        'And the processing config decision "Bind PIDs" is set to "No"\n'
        'And the processing config decision "Store AIP location" is set to'
        ' "Store AIP in standard Archivematica Directory"\n'
        'And the processing config decision "Upload DIP" is set to'
        ' "Do not upload DIP"\n'
        'And the processing config decision "Document empty directories"'
        ' is set to "No"\n'
    )


@given(
    "transfer source {transfer_path} which contains a manually normalized"
    " file whose path is a prefix of another manually normalized file"
)
def step_impl(context, transfer_path):
    pass


# Whens
# ------------------------------------------------------------------------------


# Thens
# ------------------------------------------------------------------------------


@then("all preservation tasks recognize the manually normalized derivatives")
def step_impl(context):
    skipping_msg = (
        "is file group usage manualNormalization instead of original  - skipping"
    )
    already_nmlzd_msg = "was already manually normalized into"
    for task in context.scenario.job["tasks"].values():
        try:
            assert skipping_msg in task["stdout"]
        except AssertionError:
            assert already_nmlzd_msg in task["stdout"], "{} is not in {}\n\n{}".format(
                already_nmlzd_msg, task["stdout"], task
            )


@then("each manually normalized file is matched to an original")
def step_impl(context):
    for task in context.scenario.job["tasks"].values():
        assert "Matched original file" in task["stdout"]
        assert "to  preservation file" in task["stdout"]


# ==============================================================================
# Helper Functions
# ==============================================================================
