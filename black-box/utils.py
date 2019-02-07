#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import os
import sys
import tempfile

import environment

automation_tools = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "automation-tools",
)

sys.path.append(automation_tools)

from transfers.amclient import AMClient


def configure_ss_client(context):
    """Do nothing"""
    am = AMClient()
    am.ss_url = context.ss_url
    am.ss_user_name = context.ss_user
    am.ss_api_key = context.ss_api_key
    return am


def configure_am_client(context):
    """Do nothing"""
    am = AMClient()
    am.am_url = context.am_url
    am.am_user_name = context.am_user
    am.am_api_key = context.am_api_key
    return am


def return_default_ts_location(context):
    """Do nothing"""
    am = configure_ss_client(context)
    try:
        resp = am.list_locations()['objects']
        for location_object in resp:
            if location_object.get("description") == "" \
                and location_object.get("enabled") is True \
                and location_object.get("relative_path").endswith("home") \
                    and location_object.get("purpose") == "TS":
                return location_object.get("uuid")
    except (KeyError, TypeError):
        raise environment.EnvironmentError("Error making API call")


def browse_default_ts_location(context):
    """Do nothing"""
    am = configure_ss_client(context)
    am.transfer_source = context.location_uuid
    am.transfer_path = context.demo_transfer_path
    try:
        resp = am.transferables()
        if resp.get("directories") and resp.get("entries"):
            return True
        return False
    except (KeyError, TypeError):
        raise environment.EnvironmentError("Error making API call")


def start_transfer(
    context, transfer_name="amauat-transfer", processing_config="automated"):
    """Do nothing"""
    am = configure_am_client(context)
    am.transfer_source = context.location_uuid
    am.transfer_path = context.demo_transfer_path
    try:
        context.transfer_name = transfer_name
        return am.create_package(
            name=transfer_name,
            processing_config=processing_config).get("id")
    except (KeyError, TypeError) as err:
        raise environment.EnvironmentError(
            "Error making API call: {}".format(err))


def check_unit_status(context, unit="transfer"):
    """Do nothing"""
    am = configure_am_client(context)
    am.transfer_uuid = context.transfer_uuid
    am.sip_uuid = context.sip_uuid
    if unit == "transfer":
        resp = am.get_transfer_status()
        if isinstance(resp, dict):
            return resp
    resp = am.get_ingest_status()
    if isinstance(resp, dict):
        return resp
    raise environment.EnvironmentError("Error making API call: {}".format(err))


def download_aip(context):
    """Do nothing"""
    tmp = tempfile.gettempdir()
    # Can be a 7z or a Tar file, we need to differentiate eventually.
    aip_location = os.path.join(tmp, "amauat-aip-file")
    am = configure_ss_client(context)
    aip = am.download_package(context.sip_uuid, path=aip_location)
    if isinstance(aip, int):
        raise environment.EnvironmentError("Error making API call")
    return aip


def download_file(context, relative_path):
    """Do nothing"""
    tmp = tempfile.gettempdir()
    tmp_file_location = os.path.join(tmp, os.path.split(relative_path)[-1:][0])
    am = configure_ss_client(context)
    file = am.extract_file(
        context.sip_uuid, relative_path)
    with open(tmp_file_location, 'w') as write_file:
        write_file.write(file)
    return tmp_file_location


def download_mets(context):
    """Do nothing"""
    mets_file = "{}-{}/data/METS.{}.xml"\
        .format(context.transfer_name, context.sip_uuid, context.sip_uuid)
    return download_file(context, mets_file)
