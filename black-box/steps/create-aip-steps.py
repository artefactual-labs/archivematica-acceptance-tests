#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module Docstring

We should do as much as we can to document what this module is doing. So let's
do that here!
"""

from __future__ import print_function, unicode_literals
import os
import sys
import time

from behave import given, when, then

import environment
import utils


@given(
    u'the transfer ‘DemoTransfer’ is started with the automatedProcessingMCP '
    'processing configuration.')
def step_impl(context):
    """Step 1"""
    if not utils.browse_default_ts_location(context):
        raise environment.EnvironmentError("Location cannot be verified")
    try:
        context.transfer_uuid = utils.start_transfer(context)
    except environment.EnvironmentError as err:
        assert False, "Error starting transfer: {}".format(err)


@when(u'the Transfer is COMPLETE')
def step_impl(context):
    """Step 2"""
    context.sip_uuid = None
    status = None
    resp = None
    try:
        while status != "COMPLETE" or status == "FAILED":
            time.sleep(environment.MEDIUM_WAIT)
            resp = utils.check_unit_status(context)
            if isinstance(resp, int) or resp is None:
                continue
            status = resp.get("status")
        if status == "COMPLETE":
            context.sip_uuid = resp.get("sip_uuid")
        else:
            assert False
    except environment.EnvironmentError as err:
        assert False, "Error checking transfer status: {}".format(err)


@when(u'the Ingest is COMPLETE')
def step_impl(context):
    """Step 3"""
    status = None
    resp = None
    try:
        while status != "COMPLETE" or status == "FAILED":
            time.sleep(environment.MEDIUM_WAIT)
            resp = utils.check_unit_status(context, unit="ingest")
            if isinstance(resp, int) or resp is None:
                continue
            status = resp.get("status")
        if status == "COMPLETE":
            return
        else:
            assert False
    except environment.EnvironmentError as err:
        assert False, "Error checking ingest status: {}".format(err)


@then(u'an AIP can be downloaded')
def step_impl(context):
    """Step 4"""
    context.aip_location = utils.download_aip(context)
    #
    # Or we can download an individual METS file too... up to you!
    #
    print("\n", "AIP output to:", context.aip_location, "\n")


@then(u'the AIP METS can be accessed and parsed by mets-reader-writer')
def step_impl(context):
    """Step 5"""
    if os.path.exists(context.aip_location):
        """Validate its contents."""
    raise NotImplementedError(
        u'STEP: Then the AIP METS can be accessed and parsed by '
        'mets-reader-writer')
