"""Infinite AIPs Steps."""

import logging

from behave import when

from features.steps import utils


logger = logging.getLogger('amauat.steps.infiniteaips')


# Givens
# ------------------------------------------------------------------------------


# Whens
# ------------------------------------------------------------------------------

@when('a transfer is initiated on the runtime-supplied directory')
def step_impl(context):
    transfer_path = context.am_user.runtime_supplied_transfer_path
    utils.initiate_transfer(context, transfer_path)


@when('the user creates the same AIP all over again')
def step_impl(context):
    # This is necessary so that we don't incorrectly use the
    # ``context.scenario.sip_uuid`` value set on previous iterations.
    context.scenario.sip_uuid = None
    context.execute_steps(
        'When a transfer is initiated on the runtime-supplied directory\n'
        'And the user waits for the AIP to appear in archival storage\n'
        'And the user creates the same AIP all over again\n'  # <= recursive
    )


# Thens
# ------------------------------------------------------------------------------
