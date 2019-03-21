"""Utilities for Steps files."""

import datetime
import logging
import os
import re
import subprocess
import tempfile
import time
import zipfile

from amclient.amclient import AMClient
import environment

logger = logging.getLogger("amauat.steps.utils")


class ArchivematicaStepsError(Exception):
    pass


def wait_for_micro_service_to_complete(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_user.browser.await_job_completion(
        microservice_name, uuid_val, unit_type=unit_type
    )


def wait_for_decision_point_to_appear(context, microservice_name, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    job_uuid, _ = context.am_user.browser.await_decision_point(
        microservice_name, uuid_val, unit_type=unit_type
    )
    context.scenario.awaiting_job_uuid = job_uuid


def make_choice(context, choice, decision_point, unit_type):
    unit_type = get_normalized_unit_type(unit_type)
    uuid_val = get_uuid_val(context, unit_type)
    context.am_user.browser.make_choice(
        choice, decision_point, uuid_val, unit_type=unit_type
    )


def get_normalized_unit_type(unit_type):
    return {"transfer": "transfer"}.get(unit_type, "sip")


def get_uuid_val(context, unit_type):
    """Return the UUID value corresponding to the ``unit_type`` ('transfer' or
    'sip') of the unit being tested in this scenario.
    """
    if unit_type == "transfer":
        uuid_val = context.scenario.transfer_uuid
    else:
        uuid_val = getattr(context.scenario, "sip_uuid", None)
        if not uuid_val:
            # If we are getting a SIP UUID from a transfer name, it is possible
            # that the transfer name is a .zip file name, in which case we must
            # remove the '.zip'. This is possible because zipped bag type
            # transfers are named after the transfer source file yet when they
            # become SIPs the extension is removed.
            context.scenario.transfer_name = context.scenario.transfer_name.rstrip(
                ".zip"
            )
            uuid_val = context.scenario.sip_uuid = context.am_user.browser.get_sip_uuid(
                context.scenario.transfer_name
            )
    return uuid_val


def aip_descr_to_attr(aip_description):
    return aip_description.lower().strip().replace(" ", "_") + "_uuid"


def aip_descr_to_ptr_attr(aip_description):
    return aip_description.lower().strip().replace(" ", "_") + "_ptr"


def get_event_attr(event_type):
    return "{}_event_uuid".format(event_type)


def get_mets_from_scenario(context):
    return context.am_user.browser.get_mets(
        context.scenario.transfer_name,
        context.am_user.browser.get_sip_uuid(context.scenario.transfer_name),
    )


def assert_premis_event(event_type, event, context):
    """Make PREMIS-event-type-specific assertions about ``event``."""
    if event_type == "unpacking":
        premis_evt_detail_el = event.find(
            "premis:eventDetail", context.am_user.mets.mets_nsmap
        )
        assert premis_evt_detail_el.text.strip().startswith("Unpacked from: ")
    elif event_type == "message digest calculation":
        event_detail = event.find(
            "premis:eventDetail", context.am_user.mets.mets_nsmap
        ).text
        event_odn = event.find(
            "premis:eventOutcomeInformation/"
            "premis:eventOutcomeDetail/"
            "premis:eventOutcomeDetailNote",
            context.am_user.mets.mets_nsmap,
        ).text
        assert 'program="python"' in event_detail
        assert 'module="hashlib.sha256()"' in event_detail
        assert re.search("^[a-f0-9]+$", event_odn)
    elif event_type == "virus check":
        event_detail = event.find(
            "premis:eventDetail", context.am_user.mets.mets_nsmap
        ).text
        event_outcome = event.find(
            "premis:eventOutcomeInformation/premis:eventOutcome",
            context.am_user.mets.mets_nsmap,
        ).text
        assert 'program="ClamAV' in event_detail
        assert event_outcome == "Pass"


def assert_premis_properties(event, context, properties):
    """Make assertions about the ``event`` element using the user-supplied
    ``properties`` dict, which maps descendants of ``event`` to dicts that map
    relations on those descendants to values.
    """
    for xpath, predicates in properties.items():
        xpath = "/".join(["premis:" + part for part in xpath.split("/")])
        desc_el = event.find(xpath, context.am_user.mets.mets_nsmap)
        for relation, value in predicates:
            if relation == "equals":
                assert desc_el.text.strip() == value, "{} does not equal {}".format(
                    desc_el.text.strip(), value
                )
            elif relation == "contains":
                assert (
                    value in desc_el.text.strip()
                ), "{} does not substring-contain {}".format(
                    desc_el.text.strip(), value
                )
            elif relation == "regex":
                assert re.search(
                    value, desc_el.text.strip()
                ), "{} does not contain regex {}".format(desc_el.text.strip(), value)


def initiate_transfer(context, transfer_path, accession_no=None, transfer_type=None):
    if transfer_path.startswith("~"):
        context.scenario.transfer_path = os.path.join(context.HOME, transfer_path[2:])
    else:
        context.scenario.transfer_path = os.path.join(
            context.TRANSFER_SOURCE_PATH, transfer_path
        )
    context.scenario.transfer_name = context.am_user.browser.unique_name(
        transfer_path2name(transfer_path)
    )
    context.scenario.transfer_uuid, context.scenario.transfer_name = context.am_user.browser.start_transfer(
        context.scenario.transfer_path,
        context.scenario.transfer_name,
        accession_no=accession_no,
        transfer_type=transfer_type,
    )


def ingest_ms_output_is(name, output, context):
    """Wait for the Ingest micro-service with name ``name`` to appear and
    assert that its output is ``output``.
    """
    context.scenario.sip_uuid = context.am_user.browser.get_sip_uuid(
        context.scenario.transfer_name
    )
    context.scenario.job = context.am_user.browser.parse_job(
        name, context.scenario.sip_uuid, "sip"
    )
    assert context.scenario.job.get("job_output") == output


def debag(paths):
    """Given an array of paths like::

        >>> ['/BagTransfer/bag-info.txt',
        ...  '/BagTransfer/bagit.txt',
        ...  '/BagTransfer/manifest-sha512.txt',
        ...  '/BagTransfer/data/bagTest/LICENSE',
        ...  '/BagTransfer/data/bagTest/README',
        ...  '/BagTransfer/data/bagTest/TRADEMARK']

    return an array like::

        >>> ['/bagTest/LICENSE', '/bagTest/README', '/bagTest/TRADEMARK']

    """
    new_paths = []
    for path in paths:
        parts = path.split(os.path.sep)
        if len(parts) > 3 and parts[2] == "data":
            new_paths.append(os.path.sep.join([""] + parts[3:]))
    return new_paths


def is_uuid(val):
    return ("".join(x for x in val if x in "-abcdef0123456789") == val) and (
        [len(x) for x in val.split("-")] == [8, 4, 4, 4, 12]
    )


def remove_common_prefix(seq):
    """Recursively remove a common prefix from all strings in a sequence of
    strings.
    """
    try:
        prefixes = set([x[0] for x in seq])
    except IndexError:
        return seq
    if len(prefixes) == 1:
        return remove_common_prefix([x[1:] for x in seq])
    return seq


def get_subpaths_from_struct_map(elem, ns, base_path="", paths=None):
    if not paths:
        paths = set()
    for div_el in elem.findall("mets:div", ns):
        path = os.path.join(base_path, div_el.get("LABEL"))
        paths.add(path)
        for subpath in get_subpaths_from_struct_map(
            div_el, ns, base_path=path, paths=paths
        ):
            paths.add(subpath)
    return list(paths)


def all_normalization_report_columns_are(column, expected_value, context):
    """Wait for the normalization report to be generated then assert that all
    values in ``column`` have value ``expected_value``.
    """
    normalization_report = context.am_user.browser.parse_normalization_report(
        context.scenario.sip_uuid
    )
    for file_dict in normalization_report:
        if file_dict["file_format"] != "None":
            assert file_dict[column] == expected_value


def transfer_path2name(transfer_path):
    """Return a transfer name, given a transfer path."""
    return os.path.split(transfer_path.replace("-", "_"))[1]


def parse_k_v_attributes(attributes):
    """Parse a string of key-value attributes formatted like "key 1: value 1;
    key 2: value 2;".
    """
    return {
        pair.split(":")[0].strip(): pair.split(":")[1].strip()
        for pair in attributes.split(";")
        if pair.strip()
    }


def get_duration_as_float(duration_string):
    dt = datetime.datetime.strptime(duration_string, "%H:%M:%S.%f")
    delta = datetime.timedelta(
        hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond
    )
    return delta.total_seconds()


def unzip(zip_path):
    directory_to_extract_to = os.path.dirname(zip_path)
    zip_ref = zipfile.ZipFile(zip_path, "r")
    try:
        zip_ref.extractall(directory_to_extract_to)
    except BaseException:
        pass
    finally:
        zip_ref.close()
    if os.path.isdir(directory_to_extract_to):
        return directory_to_extract_to
    return None


def configure_ss_client(context):
    am = AMClient()
    am.ss_url = context.am_user.ss_url.rstrip("/")
    am.ss_user_name = context.am_user.ss_username
    am.ss_api_key = context.am_user.browser.ss_api_key
    return am


def configure_am_client(context):
    am = AMClient()
    am.am_url = context.am_user.am_url.rstrip("/")
    am.am_user_name = context.am_user.am_username
    am.am_api_key = context.am_user.am_api_key
    return am


def browse_default_ts_location(context, browse_path=None):
    """
    Return transferable directories and entities from a path
    of the default transfer source of the storage service.
    """
    am = configure_ss_client(context)
    am.transfer_source = return_default_ts_location(context)
    if browse_path is None:
        browse_path = context.demo_transfer_path
    am.transfer_path = browse_path
    try:
        resp = am.transferables()
        if resp.get("directories") or resp.get("entries"):
            return {
                "directories": resp.get("directories"),
                "entries": resp.get("entries"),
            }
        return {}
    except (KeyError, TypeError):
        raise environment.EnvironmentError("Error making API call")


def return_default_ts_location(context):
    """"
    Return the UUID of the default transfer source location.
    """
    am = configure_ss_client(context)
    try:
        resp = am.list_storage_locations()["objects"]
        for location_object in resp:
            if (
                location_object.get("description") == ""
                and location_object.get("enabled") is True
                and location_object.get("relative_path").endswith("home")
                and location_object.get("purpose") == "TS"
            ):
                return location_object.get("uuid")
    except (KeyError, TypeError) as err:
        raise environment.EnvironmentError("Error making API call: {}".format(err))


def get_default_ss_pipeline(context):
    am = configure_ss_client(context)
    try:
        return am.get_pipelines()["objects"][0].get("uuid")
    except (KeyError, IndexError) as err:
        raise environment.EnvironmentError("Error making API call: {}".format(err))


def start_transfer(
    context, transfer_name="amauat-transfer", processing_config="automated"
):
    """Start a transfer using the create_package endpoint and return its uuid"""
    am = configure_am_client(context)
    am.transfer_source = return_default_ts_location(context)
    am.transfer_directory = context.demo_transfer_path
    am.transfer_name = transfer_name
    am.processing_config = processing_config
    try:
        context.transfer_name = transfer_name
        return am.create_package().get("id")
    except (KeyError, TypeError) as err:
        raise environment.EnvironmentError("Error making API call: {}".format(err))


def check_unapproved_transfers_with_same_directory_name(context):
    am = configure_am_client(context)
    for transfer in am.unapproved_transfers()["results"]:
        if transfer["directory"] == context.transfer_name:
            return True


def approve_transfer(context, transfer_uuid):
    context.transfer_uuid = transfer_uuid
    response = check_unit_status(context, "transfer")
    if response.get("status") == "USER_INPUT":
        am = configure_am_client(context)
        am.transfer_directory = response["directory"]
        message = am.approve_transfer()
        if not message.get("error"):
            return message["uuid"]
        raise environment.EnvironmentError(message["error"])


def start_reingest(context, reingest_type="FULL", processing_config="automated"):
    # necessary in case a previous test failed leaving unapproved transfers
    if check_unapproved_transfers_with_same_directory_name(context):
        raise environment.EnvironmentError(
            "Cannot start reingest of AIP {} because there is a "
            "unapproved transfer with the same directory name in "
            "watchedDirectories/activeTransfers/standardTransfer".format(
                context.sip_uuid
            )
        )
    am = configure_ss_client(context)
    am.reingest_type = reingest_type
    am.processing_config = processing_config
    am.pipeline_uuid = get_default_ss_pipeline(context)
    am.aip_uuid = context.sip_uuid
    try:
        reingest_uuid = am.reingest_aip().get("reingest_uuid")
        time.sleep(environment.MEDIUM_WAIT)
        return approve_transfer(context, reingest_uuid)
    except (KeyError, TypeError, AttributeError) as err:
        raise environment.EnvironmentError("Error making API call: {}".format(err))


def check_unit_status(context, unit="transfer"):
    """
    Get the status of a transfer or an ingest.
    """
    am = configure_am_client(context)
    am.transfer_uuid = context.transfer_uuid
    am.sip_uuid = context.sip_uuid
    if unit == "transfer":
        resp = am.get_transfer_status()
        if isinstance(resp, dict):
            return resp
        raise environment.EnvironmentError("Error making API call: {}".format(resp))
    resp = am.get_ingest_status()
    if isinstance(resp, dict):
        return resp
    raise environment.EnvironmentError("Error making API call: {}".format(resp))


def download_aip(context):
    """
    Download an AIP from the storage service.
    """
    tmp = tempfile.gettempdir()
    # Can be a 7z or a Tar file, we need to differentiate eventually.
    aip_location = os.path.join(tmp, "amauat-aip-file")
    am = configure_ss_client(context)
    am.directory = aip_location
    aip = am.download_package(context.sip_uuid)
    if isinstance(aip, int):
        raise environment.EnvironmentError("Error making API call")
    return aip


def download_file(context, relative_path):
    """
    Download a file relative to an AIP's path.
    """
    tmp = tempfile.gettempdir()
    fname = os.path.basename(relative_path)
    tmp_file_location = os.path.join(tmp, fname)
    am = configure_ss_client(context)
    am.package_uuid = context.sip_uuid
    am.relative_path = relative_path
    am.saveas_filename = fname
    am.directory = tmp
    am.extract_file()
    return tmp_file_location


def download_mets(context):
    """
    Download the METS.xml file of an AIP.
    """
    mets_file = "{}-{}/data/METS.{}.xml".format(
        context.transfer_name, context.sip_uuid, context.sip_uuid
    )
    return download_file(context, mets_file)


def _automation_tools_extract_aip(aip_file, aip_uuid, tmp_dir):
    """
    Extracts an AIP to a folder.
    :param str aip_file: absolute path to an AIP
    :param str aip_uuid: UUID from the AIP
    :param str tmp_dir: absolute path to a directory to place the extracted AIP
    :returns: absolute path to the extracted AIP folder
    """
    command = ["7z", "x", "-bd", "-y", "-o{0}".format(tmp_dir), aip_file]
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error("Could not extract AIP, error: %s", e.output)
        return

    # Remove extracted file to avoid multiple entries with the same UUID
    try:
        os.remove(aip_file)
    except OSError:
        pass

    # Find extracted entry. Assuming it contains the AIP UUID
    extracted_entry = None
    for entry in os.listdir(tmp_dir):
        if aip_uuid in entry:
            extracted_entry = os.path.join(tmp_dir, entry)

    if not extracted_entry:
        logger.error("Can not find extracted AIP by UUID")
        return

    # Return folder path if it's a directory
    if os.path.isdir(extracted_entry):
        return extracted_entry

    # Re-try extraction if it's not a directory
    return _automation_tools_extract_aip(extracted_entry, aip_uuid, tmp_dir)


# TODO: Make a decision about keeping this. Probably not if not used.
def extract_aip(context):
    tmp = tempfile.mkdtemp()
    return _automation_tools_extract_aip(context.aip_location, context.sip_uuid, tmp)


def get_premis_events_by_type(entry, event_type):
    return [ev for ev in entry.get_premis_events() if ev.type == event_type]


def get_path_before_sanitization(entry, transfer_contains_objects_dir=False):
    clean_name_premis_events = get_premis_events_by_type(entry, "name cleanup")
    if not clean_name_premis_events:
        result = entry.path
    else:
        event = clean_name_premis_events[0]
        note = event.event_outcome_detail_note
        # this parsing is based on
        # metsrw.plugins.premisrw.premis.PREMISEvent.parsed_event_detail
        parsed_note = dict(
            [
                tuple([x.strip(' "') for x in kv.strip().split("=", 1)])
                for kv in note.split(";")
            ]
        )
        # remove the '%transferDirectory%' part from the path
        result = parsed_note["Original name"][19:]
    if not transfer_contains_objects_dir:
        # remove the 'objects/' part from the path
        return result[8:]
    else:
        return result


def assert_structmap_item_path_exists(item, root_path, parent_path=""):
    label = item.attrib.get("LABEL")
    if label:
        # the relative path of the item is represented by its LABEL attribute
        path = os.path.join(root_path, parent_path, label)
        if item.attrib["TYPE"] == "Item":
            assert os.path.isfile(path)
        elif item.attrib["TYPE"] == "Directory":
            assert os.path.isdir(path)
        else:
            msg = "Cannot handle structMap items with attribute " 'TYPE "{}"'.format(
                item.attrib["TYPE"]
            )
            raise ValueError(msg)
        for child in item:
            assert_structmap_item_path_exists(child, root_path, path)


def is_valid_download(path):
    errors = {
        "path": "Path returned is None",
        "validate": "Cannot validate {} as file".format(path),
        "size": "File {} has not downloaded correctly".format(path),
    }
    assert path, errors["path"]
    assert os.path.isfile(path), errors["validate"]
    assert os.stat(path).st_size >= 1, errors["size"]


def get_filesec_files(tree, use=None, nsmap={}):
    use_query = ""
    # an empty use parameter will retrieve all the files in the fileSec
    if use:
        use_query = '="{}"'.format(use)
    return tree.findall(
        "mets:fileSec/mets:fileGrp[@USE{}]/mets:file".format(use_query),
        namespaces=nsmap,
    )
