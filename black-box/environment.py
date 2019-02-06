#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""environment.py

Configures the environment for running different scenarios. There are important
behave 'hooks' in here that can help establish stage at various stages in the
tests.
"""

from __future__ import unicode_literals
import os
import sys
import utils


# Archivematica sample-data paths.
demo_transfer_path = os.path.join(
    "archivematica", "archivematica-sampledata", "SampleTransfers",
    "DemoTransfer"
)

# Wait periods which we can get from amuser.constants.
WAIT_FACTOR = 4
MEDIUM_WAIT = 3 * WAIT_FACTOR

# Parameters to Access the AM/SS API.
SS_URL = "http://127.0.0.1:62081"
SS_USER = "test"
SS_API_KEY = "test"

#Archivematica.
AM_URL = "http://127.0.0.1:62080"
AM_USER = "test"
AM_API_KEY = "test"


class EnvironmentError(Exception):
    """Return this when there is a problem setting up the environment"""


def before_step(context, step):
    """Do nothing"""


def after_step(context, step):
    """Do nothing"""


def before_scenario(context, scenario):
    """Do nothing"""

    # Make sure that we have a storage service location to work with, this
    # first test is on a default install and uses the default home location.
    context.location_uuid = utils.return_default_ts_location(context)


def after_scenario(context, scenario):
    """Do nothing"""


def before_feature(context, feature):
    """Do nothing"""


def after_feature(context, feature):
    """Do nothing"""


def before_tag(context, tag):
    """Do nothing"""


def after_tag(context, tag):
    """Do nothing"""


def before_all(context):
    """Do nothing"""

    # Configure the storage service access parameters.
    context.ss_url = SS_URL
    context.ss_user = SS_USER
    context.ss_api_key = SS_API_KEY

    # Configure the Archivematica parameters.
    context.am_url = AM_URL
    context.am_user = AM_USER
    context.am_api_key = AM_API_KEY

    # One transfer path that we know exists in sample-data. We should be able
    # to figure out how to make it possible to use this with arbitrary data.
    context.demo_transfer_path = demo_transfer_path.encode()


def after_all(context):
    """Do nothing"""
