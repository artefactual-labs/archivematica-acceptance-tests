#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from behave import given, when, then

automation_tools = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "automation-tools",
)

sys.path.append(automation_tools)

from transfers import amclient


@given(
    u'the transfer ‘DemoTransfer’ is started with the automatedProcessingMCP '
    'processing configuration.')
def step_impl(context):
    raise NotImplementedError(
        u'STEP: Given the transfer ‘DemoTransfer’ is started with the '
        'automatedProcessingMCP processing configuration.')


@when(u'the Transfer is COMPLETE')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the Transfer is COMPLETE')


@when(u'the Ingest is COMPLETE')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the Ingest is COMPLETE')


@then(u'an AIP can be downloaded')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then an AIP can be downloaded')


@then(u'the AIP METS can be accessed and parsed by mets-reader-writer')
def step_impl(context):
    raise NotImplementedError(
        u'STEP: Then the AIP METS can be accessed and parsed by '
        'mets-reader-writer')
