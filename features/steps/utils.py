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
from environment import AM_API_CONFIG_KEY
from environment import SS_API_CONFIG_KEY

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


def get_mets_from_scenario(context, api=False):
    """Retrieve the AIP METS file from the test scenario

    Given a parameter of True for the api parameter, then we will seek to
    retrieve the AIP METS from the AIP package itself. When that parameter is
    False, we will seek to download it via the web-driver from the Store AIP
    decision point on the ingest tab of Archivematica where the user has the
    opportunity to review the METS file from the browser window.
    """
    if api:
        return context.am_user.browser.get_mets_via_api(
            context.scenario.transfer_name,
            context.am_user.browser.get_sip_uuid(context.scenario.transfer_name),
        )
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


def configure_ss_client(api_client_config):
    am = AMClient()
    am.ss_url = api_client_config["url"]
    am.ss_user_name = api_client_config["username"]
    am.ss_api_key = api_client_config["api_key"]
    return am


def configure_am_client(api_client_config):
    am = AMClient()
    am.am_url = api_client_config["url"]
    am.am_user_name = api_client_config["username"]
    am.am_api_key = api_client_config["api_key"]
    return am


def is_invalid_api_response(response):
    return response is None or isinstance(response, int)


def call_api_endpoint(
    endpoint, endpoint_args=[], warning_message=None, error_message=None, max_attempts=3
):
    if warning_message is None:
        warning_message = "Got invalid response from {}. Retrying".format(endpoint)
    if error_message is None:
        error_message = (
            "Could not get a valid response from {}"
            " after {} attempts".format(endpoint, max_attempts)
        )
    response = None
    attempts = 0
    while is_invalid_api_response(response):
        response = endpoint(*endpoint_args)
        attempts += 1
        if is_invalid_api_response(response):
            if attempts == max_attempts:
                raise environment.EnvironmentError(error_message)
            logger.warning(warning_message)
            time.sleep(environment.OPTIMISTIC_WAIT * attempts)
    return response


def browse_default_ts_location(api_clients_config, browse_path):
    """
    Return transferable directories and entities from a path
    of the default transfer source of the storage service.
    """
    if os.path.splitext(browse_path)[1]:
        # browse_path points to a file (e.g. a zipped bag)
        # but the browse location endpoint of the SS expects a directory
        browse_path = os.path.dirname(browse_path)
    am = configure_ss_client(api_clients_config[SS_API_CONFIG_KEY])
    am.transfer_source = return_default_ts_location(api_clients_config)
    am.transfer_path = browse_path
    response = call_api_endpoint(
        endpoint=am.transferables,
        warning_message="Error browser default TS location",
        error_message="Error browser default TS location",
    )
    if response.get("directories") or response.get("entries"):
        return {
            "directories": response.get("directories"),
            "entries": response.get("entries"),
        }
    return {}


def return_default_ts_location(api_clients_config):
    """"
    Return the UUID of the default transfer source location.
    """
    am = configure_ss_client(api_clients_config[SS_API_CONFIG_KEY])
    response = call_api_endpoint(
        endpoint=am.list_storage_locations,
        warning_message="Cannot list storage locations",
        error_message="Cannot list storage locations",
    )
    for location_object in response.get("objects", []):
        if (
            location_object.get("description") == ""
            and location_object.get("enabled") is True
            and location_object.get("relative_path").endswith("home")
            and location_object.get("purpose") == "TS"
        ):
            return location_object.get("uuid")


def get_default_ss_pipeline(api_clients_config):
    am = configure_ss_client(api_clients_config[SS_API_CONFIG_KEY])
    response = call_api_endpoint(
        endpoint=am.get_pipelines,
        warning_message="Cannot get default SS pipeline",
        error_message="Cannot get default SS pipeline",
    )
    objects = response.get("objects", [])
    if objects:
        return objects[0].get("uuid")


def start_transfer(
    api_clients_config,
    transfer_path,
    transfer_name=None,
    processing_config="automated",
    transfer_type="standard",
):
    """Start a transfer using the create_package endpoint and return its uuid"""
    if transfer_name is None:
        transfer_name = "amauat-transfer_{}".format(int(time.time()))
    am = configure_am_client(api_clients_config[AM_API_CONFIG_KEY])
    am.transfer_source = return_default_ts_location(api_clients_config)
    am.transfer_directory = transfer_path
    am.transfer_name = transfer_name
    am.transfer_type = transfer_type
    am.processing_config = processing_config
    response = call_api_endpoint(
        endpoint=am.create_package,
        warning_message="Cannot start transfer",
        error_message="Cannot start transfer",
    )
    return {"transfer_name": transfer_name, "transfer_uuid": response.get("id")}


def check_unapproved_transfers_with_same_directory_name(
    api_clients_config, directory_name
):
    am = configure_am_client(api_clients_config[AM_API_CONFIG_KEY])
    response = call_api_endpoint(
        endpoint=am.unapproved_transfers,
        warning_message="Cannot get unapproved tansfers",
        error_message="Cannot get unapproved tansfers",
    )
    for transfer in response.get("results", []):
        if transfer.get("directory") == directory_name:
            return True


def approve_transfer(api_clients_config, transfer_uuid):
    response = check_unit_status(api_clients_config, transfer_uuid, "transfer")
    if response.get("status") == "USER_INPUT":
        am = configure_am_client(api_clients_config[AM_API_CONFIG_KEY])
        am.transfer_directory = response["directory"]
        response = call_api_endpoint(
            endpoint=am.approve_transfer, warning_message="", error_message=""
        )
        if not response.get("error"):
            return response["uuid"]
        raise environment.EnvironmentError(response["error"])


def start_reingest(
    api_clients_config,
    transfer_name,
    sip_uuid,
    reingest_type="FULL",
    processing_config="automated",
):
    # necessary in case a previous test failed leaving unapproved transfers
    if check_unapproved_transfers_with_same_directory_name(
        api_clients_config, transfer_name
    ):
        raise environment.EnvironmentError(
            "Cannot start reingest of AIP {} because there is a "
            "unapproved transfer with the same directory name in "
            "watchedDirectories/activeTransfers/standardTransfer".format(sip_uuid)
        )
    am = configure_ss_client(api_clients_config[SS_API_CONFIG_KEY])
    am.reingest_type = reingest_type
    am.processing_config = processing_config
    am.pipeline_uuid = get_default_ss_pipeline(api_clients_config)
    am.aip_uuid = sip_uuid
    response = call_api_endpoint(
        endpoint=am.reingest_aip,
        warning_message="Cannot reingest AIP",
        error_message="Cannot reingest AIP",
    )
    reingest_uuid = response.get("reingest_uuid")
    time.sleep(environment.MEDIUM_WAIT)
    return approve_transfer(api_clients_config, reingest_uuid)


def check_unit_status(api_clients_config, unit_uuid, unit="transfer"):
    """
    Get the status of a transfer or an ingest.
    """
    am = configure_am_client(api_clients_config[AM_API_CONFIG_KEY])
    am.transfer_uuid = unit_uuid
    am.sip_uuid = unit_uuid
    return call_api_endpoint(
        endpoint=getattr(am, "get_{}_status".format(unit)),
        warning_message="Cannot check unit status",
        error_message="Cannot check unit status",
    )


def download_aip(api_clients_config, sip_uuid):
    """
    Download an AIP from the storage service.
    """
    am = configure_ss_client(api_clients_config[SS_API_CONFIG_KEY])
    am.directory = tempfile.mkdtemp()
    return call_api_endpoint(
        endpoint=am.download_package,
        endpoint_args=[sip_uuid],
        warning_message="Error downloading AIP",
        error_message="Error donwloading AIP",
    )


def get_aip_file_location(extracted_aip_dir, relative_path):
    return os.path.join(extracted_aip_dir, relative_path)


def get_aip_mets_location(extracted_aip_dir, sip_uuid):
    path = os.path.join("data", "METS.{}.xml".format(sip_uuid))
    return get_aip_file_location(extracted_aip_dir, path)


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


def extract_aip(api_clients_config, sip_uuid):
    tmp = tempfile.mkdtemp()
    aip_ss_filename = download_aip(api_clients_config, sip_uuid)
    return _automation_tools_extract_aip(aip_ss_filename, sip_uuid, tmp)


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


def start_sample_transfer(
    api_clients_config,
    sample_transfer_path,
    transfer_type="standard",
    processing_config="automated",
):
    result = {}
    transfer_path = os.path.join(environment.sample_data_path, sample_transfer_path)
    if not browse_default_ts_location(api_clients_config, transfer_path):
        raise environment.EnvironmentError(
            "Location {} cannot be verified".format(transfer_path)
        )
    try:
        start_result = start_transfer(
            api_clients_config,
            transfer_path,
            transfer_type=transfer_type,
            processing_config=processing_config,
        )
        result["transfer_uuid"] = start_result["transfer_uuid"]
        result["transfer_name"] = start_result["transfer_name"]
        result["transfer_path"] = transfer_path
        return result
    except environment.EnvironmentError as err:
        assert False, "Error starting transfer: {}".format(err)


def wait_for_transfer(api_clients_config, transfer_uuid):
    status = None
    resp = None
    try:
        while status not in ("COMPLETE", "FAILED") or (
            status == "COMPLETE" and resp.get("sip_uuid") is None
        ):
            time.sleep(environment.MEDIUM_WAIT)
            resp = check_unit_status(api_clients_config, transfer_uuid, "transfer")
            if isinstance(resp, int) or resp is None:
                continue
            status = resp.get("status")
        return resp
    except environment.EnvironmentError as err:
        assert False, "Error checking transfer (uuid: {}) status: {}".format(
            transfer_uuid, err
        )


def wait_for_ingest(api_clients_config, sip_uuid):
    status = None
    resp = None
    try:
        while status not in ("COMPLETE", "FAILED"):
            time.sleep(environment.MEDIUM_WAIT)
            resp = check_unit_status(api_clients_config, sip_uuid, unit="ingest")
            if isinstance(resp, int) or resp is None:
                continue
            status = resp.get("status")
        return resp
    except environment.EnvironmentError as err:
        assert False, "Error checking ingest (uuid: {}) status: {}".format(
            sip_uuid, err
        )


def get_transfer_result(api_clients_config, transfer_uuid):
    """
    Wait for a started transfer to finish and return:
      - the SIP UUID
      - the local directory where the AIP has been extracted to
      - the METS path
    """
    transfer_response = wait_for_transfer(api_clients_config, transfer_uuid)
    if transfer_response["status"] == "FAILED":
        return {}
    sip_uuid = transfer_response["sip_uuid"]
    ingest_response = wait_for_ingest(api_clients_config, sip_uuid)
    if ingest_response["status"] == "FAILED":
        return {}
    extracted_aip_dir = extract_aip(api_clients_config, sip_uuid)
    aip_mets_location = get_aip_mets_location(extracted_aip_dir, sip_uuid)
    return {
        "sip_uuid": sip_uuid,
        "extracted_aip_dir": extracted_aip_dir,
        "aip_mets_location": aip_mets_location,
    }


def create_sample_transfer(
    api_clients_config, sample_transfer_path, transfer_type="standard"
):
    cached_transfer = environment.transfers_cache.setdefault(sample_transfer_path, {})
    if "aip_mets_location" in cached_transfer:
        return cached_transfer
    transfer = start_sample_transfer(
        api_clients_config, sample_transfer_path, transfer_type=transfer_type
    )
    transfer_result = get_transfer_result(api_clients_config, transfer["transfer_uuid"])
    if not transfer_result:
        return transfer
    transfer["sip_uuid"] = transfer_result["sip_uuid"]
    transfer["extracted_aip_dir"] = transfer_result["extracted_aip_dir"]
    transfer["aip_mets_location"] = transfer_result["aip_mets_location"]
    cached_transfer.update(transfer)
    return transfer


def create_reingest(api_clients_config, transfer):
    if "reingest_aip_mets_location" in transfer:
        return transfer
    result = {}
    try:
        result["reingest_transfer_uuid"] = start_reingest(
            api_clients_config, transfer["transfer_name"], transfer["sip_uuid"]
        )
    except environment.EnvironmentError as err:
        assert False, "Error starting reingest: {}".format(err)
    reingest_transfer_result = get_transfer_result(
        api_clients_config, result["reingest_transfer_uuid"]
    )
    if not reingest_transfer_result:
        return reingest_transfer_result
    result["reingest_sip_uuid"] = reingest_transfer_result["sip_uuid"]
    result["reingest_extracted_aip_dir"] = reingest_transfer_result["extracted_aip_dir"]
    result["reingest_aip_mets_location"] = reingest_transfer_result["aip_mets_location"]
    return result


def get_jobs(
    api_clients_config,
    unit_uuid,
    job_microservice=None,
    job_link_uuid=None,
    job_name=None,
):
    am = configure_am_client(api_clients_config[AM_API_CONFIG_KEY])
    am.unit_uuid = unit_uuid
    if job_microservice is not None:
        am.job_microservice = job_microservice
    if job_link_uuid is not None:
        am.job_link_uuid = job_link_uuid
    if job_name is not None:
        am.job_name = job_name
    return call_api_endpoint(
        endpoint=am.get_jobs,
        warning_message="Cannot check job status",
        error_message="Cannot check job status",
    )


def assert_jobs_completed_successfully(
    api_clients_config,
    unit_uuid,
    job_name=None,
    job_link_uuid=None,
    job_microservice=None,
    valid_exit_codes=(0,),
):
    jobs = get_jobs(
        api_clients_config,
        unit_uuid,
        job_name=job_name,
        job_link_uuid=job_link_uuid,
        job_microservice=job_microservice,
    )
    assert len(jobs), "No jobs found for unit {}".format(unit_uuid)
    for job in jobs:
        job_error = "Job '{} ({})' of unit '{}' does not have a COMPLETE status".format(
            job["name"], job["uuid"], unit_uuid
        )
        assert job["status"] == "COMPLETE", job_error
        for task in job["tasks"]:
            task_error = "Task '{}' of job '{} ({})' of unit '{}' does not have a valid exit_code ({})".format(
                task["uuid"],
                job["name"],
                job["uuid"],
                unit_uuid,
                ", ".join(map(str, valid_exit_codes)),
            )
            assert task["exit_code"] in valid_exit_codes, task_error


def assert_jobs_fail(
    api_clients_config,
    unit_uuid,
    job_name=None,
    job_link_uuid=None,
    job_microservice=None,
    valid_exit_codes=(0,),
):
    jobs = get_jobs(
        api_clients_config,
        unit_uuid,
        job_name=job_name,
        job_link_uuid=job_link_uuid,
        job_microservice=job_microservice,
    )
    assert len(jobs), "No jobs found for unit {}".format(unit_uuid)
    for job in jobs:
        job_error = "Job '{} ()' of unit '{}' does not have a FAILED status or one of its tasks has an invalid exit code ({})".format(
            job["name"], job["uuid"], unit_uuid, ", ".join(map(str, valid_exit_codes))
        )
        assert job["status"] == "FAILED" or job_tasks_failed(
            job, valid_exit_codes
        ), job_error


def job_tasks_failed(job, valid_exit_codes):
    return [task for task in job["tasks"] if task["exit_code"] not in valid_exit_codes]


def assert_microservice_executes(api_clients_config, unit_uuid, microservice_name):
    jobs = get_jobs(api_clients_config, unit_uuid, job_microservice=microservice_name)
    assert len(jobs), "No jobs found with microservice {} for unit {}".format(
        microservice_name, unit_uuid
    )
