import logging
import os

import amuser
from amuser.constants import (
    NIHILISTIC_WAIT,
    APATHETIC_WAIT,
    PESSIMISTIC_WAIT,
    MEDIUM_WAIT,
    OPTIMISTIC_WAIT,
    QUICK_WAIT,
    MICRO_WAIT,
    METS_NSMAP,
)
import utils


class EnvironmentError(Exception):
    """Return this when there is a problem setting up the environment"""


ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Archivematica sample-data paths.
sample_data_path = os.path.join("archivematica", "archivematica-sampledata")

# Change these to match your test environment
# These may also be overridden as Behave userdata options
# (https://pythonhosted.org/behave/new_and_noteworthy_v1.2.5.html#index-7),
# i.e., ``behave -D am_username=demo -D am_password=secret``
AM_USERNAME = "test"
AM_PASSWORD = "testtest"
AM_URL = "http://192.168.168.192/"
AM_VERSION = "1.6"
AM_API_KEY = None
AM_API_CONFIG_KEY = "archivematica"
SS_USERNAME = "test"
SS_PASSWORD = "test"
SS_URL = "http://192.168.168.192:8000/"
SS_API_KEY = None
SS_API_CONFIG_KEY = "storage_service"
# Path relative to /home where transfer sources live.
TRANSFER_SOURCE_PATH = "vagrant/archivematica-sampledata/TestTransfers/acceptance-tests"
HOME = ""
DRIVER_NAME = "Chrome"
AUTOMATION_TOOLS_PATH = "/etc/archivematica/automation-tools"
# Set these constants if the AM client should be able to gain SSH access to the
# server where AM is being served. This is needed in order to scp server files
# to local, which some tests need. If SSH access is not possible, set
# ``SSH_ACCESSIBLE`` to ``False``.
SSH_ACCESSIBLE = True
SSH_REQUIRES_PASSWORD = True
SSH_IDENTITY_FILE = None
SERVER_USER = "vagrant"
SERVER_PASSWORD = "vagrant"

# Use-case-specific maximum attempt counters
MAX_CLICK_TRANSFER_DIRECTORY_ATTEMPTS = 5
MAX_CLICK_AIP_DIRECTORY_ATTEMPTS = 5
MAX_NAVIGATE_AIP_ARCHIVAL_STORAGE_ATTEMPTS = 10
MAX_DOWNLOAD_AIP_ATTEMPTS = 20
MAX_CHECK_AIP_STORED_ATTEMPTS = 60
MAX_CHECK_METS_LOADED_ATTEMPTS = 60
MAX_SEARCH_AIP_ARCHIVAL_STORAGE_ATTEMPTS = 120
MAX_SEARCH_DIP_BACKLOG_ATTEMPTS = 120
MAX_CHECK_TRANSFER_APPEARED_ATTEMPTS = 1000
MAX_CHECK_FOR_MS_GROUP_ATTEMPTS = 7200


def get_am_user(userdata):
    """Instantiate an ArchivematicaUser."""
    userdata.update(
        {
            "am_username": userdata.get("am_username", AM_USERNAME),
            "am_password": userdata.get("am_password", AM_PASSWORD),
            "am_url": userdata.get("am_url", AM_URL),
            "alt_am_url": userdata.get("alt_am_url", AM_URL),
            "am_version": userdata.get("am_version", AM_VERSION),
            "am_api_key": userdata.get("am_api_key", AM_API_KEY),
            "ss_username": userdata.get("ss_username", SS_USERNAME),
            "ss_password": userdata.get("ss_password", SS_PASSWORD),
            "ss_url": userdata.get("ss_url", SS_URL),
            "ss_api_key": userdata.get("ss_api_key", SS_API_KEY),
            "driver_name": userdata.get("driver_name", DRIVER_NAME),
            "ssh_accessible": _bool(userdata.get("ssh_accessible", SSH_ACCESSIBLE)),
            "ssh_requires_password": _bool(
                userdata.get("ssh_requires_password", SSH_REQUIRES_PASSWORD)
            ),
            "server_user": userdata.get("server_user", SERVER_USER),
            "server_password": userdata.get("server_password", SERVER_PASSWORD),
            "ssh_identity_file": userdata.get("ssh_identity_file", SSH_IDENTITY_FILE),
            "runtime_supplied_transfer_path": userdata.get(
                "runtime_supplied_transfer_path"
            ),
            # User-customizable wait values:
            "nihilistic_wait": userdata.get("nihilistic_wait", NIHILISTIC_WAIT),
            "apathetic_wait": userdata.get("apathetic_wait", APATHETIC_WAIT),
            "pessimistic_wait": userdata.get("pessimistic_wait", PESSIMISTIC_WAIT),
            "medium_wait": userdata.get("medium_wait", MEDIUM_WAIT),
            "optimistic_wait": userdata.get("optimistic_wait", OPTIMISTIC_WAIT),
            "quick_wait": userdata.get("quick_wait", QUICK_WAIT),
            "micro_wait": userdata.get("micro_wait", MICRO_WAIT),
            # User-customizable max attempt values:
            "max_click_transfer_directory_attempts": userdata.get(
                "max_click_transfer_directory_attempts",
                MAX_CLICK_TRANSFER_DIRECTORY_ATTEMPTS,
            ),
            "max_click_aip_directory_attempts": userdata.get(
                "max_click_aip_directory_attempts", MAX_CLICK_AIP_DIRECTORY_ATTEMPTS
            ),
            "max_navigate_aip_archival_storage_attempts": userdata.get(
                "max_navigate_aip_archival_storage_attempts",
                MAX_NAVIGATE_AIP_ARCHIVAL_STORAGE_ATTEMPTS,
            ),
            "max_download_aip_attempts": userdata.get(
                "max_download_aip_attempts", MAX_DOWNLOAD_AIP_ATTEMPTS
            ),
            "max_check_aip_stored_attempts": userdata.get(
                "max_check_aip_stored_attempts", MAX_CHECK_AIP_STORED_ATTEMPTS
            ),
            "max_check_mets_loaded_attempts": userdata.get(
                "max_check_mets_loaded_attempts", MAX_CHECK_METS_LOADED_ATTEMPTS
            ),
            "max_search_aip_archival_storage_attempts": userdata.get(
                "max_search_aip_archival_storage_attempts",
                MAX_SEARCH_AIP_ARCHIVAL_STORAGE_ATTEMPTS,
            ),
            "max_search_dip_backlog_attempts": userdata.get(
                "max_search_dip_backlog_attempts", MAX_SEARCH_DIP_BACKLOG_ATTEMPTS
            ),
            "max_check_transfer_appeared_attempts": userdata.get(
                "max_check_transfer_appeared_attempts",
                MAX_CHECK_TRANSFER_APPEARED_ATTEMPTS,
            ),
            "max_check_for_ms_group_attempts": userdata.get(
                "max_check_for_ms_group_attempts", MAX_CHECK_FOR_MS_GROUP_ATTEMPTS
            ),
        }
    )
    return amuser.ArchivematicaUser(**userdata)


def before_all(context):
    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    context.config.setup_logging(format=logging_format)
    logger = logging.getLogger()
    log_filename = "AMAUAT.log"
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(root_path, log_filename)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(logging_format)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def before_scenario(context, scenario):
    """Instantiate an ``ArchivematicaUser`` instance. The ``ArchivematicaUser``
    instance creates many drivers/browsers. If we don't destroy then in between
    scenarios, we end up with too many and it causes the tests to fail. That is
    why we are using ``before_scenario`` here and not ``before_all``.
    """
    userdata = context.config.userdata
    context.utils = utils
    if "driver_name" in userdata:
        context.am_user = get_am_user(userdata)
        context.am_user.browser.set_up()
    context.TRANSFER_SOURCE_PATH = userdata.get(
        "transfer_source_path", TRANSFER_SOURCE_PATH
    )
    context.HOME = userdata.get("home", HOME)
    context.AUTOMATION_TOOLS_PATH = userdata.get(
        "automation_tools_path", AUTOMATION_TOOLS_PATH
    )
    context.mets_nsmap = METS_NSMAP
    context.api_clients_config = {
        SS_API_CONFIG_KEY: {
            "url": userdata.get("ss_url", SS_URL).rstrip("/"),
            "username": userdata.get("ss_username", SS_USERNAME),
            "api_key": userdata.get("ss_api_key", SS_API_KEY),
        },
        AM_API_CONFIG_KEY: {
            "url": userdata.get("am_url", AM_URL).rstrip("/"),
            "username": userdata.get("am_username", AM_USERNAME),
            "api_key": userdata.get("am_api_key", AM_API_KEY),
        },
    }


def after_scenario(context, scenario):
    """Close all browser windows/Selenium drivers."""
    # In the following scenario, we've created a weird FPR rule. Here we put
    # things back as they were: make access .mov files normalize to .mp4
    if scenario.name == (
        "Isla wants to confirm that normalization to .mkv for access is successful"
    ):
        context.am_user.browser.change_normalization_rule_command(
            "Access Generic MOV", "Transcoding to mp4 with ffmpeg"
        )
    if scenario.name == (
        "Joel creates an AIP on an Archivematica instance that saves"
        " stdout/err and on one that does not. He expects that the"
        " processing time of the AIP on the first instance will be less"
        " than that of the AIP on the second one."
    ):
        context.am_user.docker.recreate_archivematica(capture_output=True)
    if getattr(context, "am_user", None) is not None:
        context.am_user.browser.tear_down()


def _bool(value):
    """Parse boolean values encoded as strings."""
    if isinstance(value, bool):
        return value
    return value.lower() in ("yes", "true", "1")
