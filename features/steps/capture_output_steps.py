"""Steps for the Capture Output Setting Feature."""
import logging

from behave import given
from behave import then
from behave import when


logger = logging.getLogger("amauat.steps.captureoutput")


# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------


@given(
    "an Archivematica instance that is deployed with output capturing"
    "{output_capture_state}"
)
def step_impl(context, output_capture_state):
    logger.info(
        "Assuming that this Archivematica instance has been"
        " deployed with output capturing %s",
        output_capture_state,
    )


# Whens
# ------------------------------------------------------------------------------


@when("preservation tasks occur")
def step_impl(context):
    """In order to implement the "occurrence of preservation tasks", we do the
    following:

    1. Start a transfer on TestTransfers/fixityCheckShouldFail/ which should
       fail early on in transfer at "Verify metadata directory checksums".
    2. Wait for "Verify metadata directory checksums" micro-service to complete
       and expect it to fail and fetch it's task data from the GUI.
    """
    context.execute_steps(
        "Given the default processing config is in its default state\n"
        'And the processing config decision "Assign UUIDs to directories" is'
        ' set to "No"\n'
        "When a transfer is initiated on directory"
        " ~/archivematica-sampledata/TestTransfers/fixityCheckShouldFail\n"
        'And the user waits for the "Verify metadata directory checksums"'
        " micro-service to complete during transfer\n"
        'Then the "Verify metadata directory checksums" micro-service output is'
        ' "Failed" during transfer\n'
    )


# Thens
# ------------------------------------------------------------------------------


@then("the {task_attribute} of the tasks is {outcome}")
def step_impl(context, task_attribute, outcome):
    """Should implement `Then the stderr/stdout of the tasks is (not)
    captured`. Tests whether the stderr or stdout of the job tasks gathered in
    a previous step are (or are not) present and non-empty.
    """
    task_attribute = task_attribute.strip().lower()
    task_attr_vals = list(
        filter(
            None,
            [
                t.get(task_attribute, "").strip()
                for t in context.scenario.job["tasks"].values()
            ],
        )
    )
    print(task_attr_vals)
    if outcome.lower().strip() == "not captured":
        assert not task_attr_vals
    else:
        assert task_attr_vals
        for task_attr_val in task_attr_vals:
            assert task_attr_val


# Helpers
# ------------------------------------------------------------------------------
