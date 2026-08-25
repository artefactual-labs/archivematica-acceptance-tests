"""Utilities for AM User."""

import logging
import time

import requests

from . import constants as c

logger = logging.getLogger("amuser.utils")

_MICROSERVICE_NAME_ALIASES = {
    "approvenormalization(review)": "approvenormalization",
    "approvenormalizationreview": "approvenormalization",
    "storeaip(review)": "storeaip",
    "storeaipreview": "storeaip",
}

_MICROSERVICE_NAME_VARIANTS = {
    "approvenormalization": (
        "Approve normalization",
        "Approve normalization (review)",
        "Approve normalization Review",
    ),
    "storeaip": ("Store AIP", "Store AIP (review)", "Store AIP Review"),
}


def squash(string_):
    """Simple function that makes it easy to compare two strings for
    equality even if they have incidental (for our purposes) formatting
    differences.
    """
    return string_.strip().lower().replace(" ", "")


def canonical_microservice_name(name):
    """Return a stable name across processing-monitor label variants."""
    squashed_name = squash(name)
    return _MICROSERVICE_NAME_ALIASES.get(squashed_name, squashed_name)


def microservice_names_match(first, second):
    """Compare microservice names across supported Archivematica versions."""
    return canonical_microservice_name(first) == canonical_microservice_name(second)


def microservice_name_variants(name):
    """Return processing-monitor labels equivalent to ``name``."""
    canonical_name = canonical_microservice_name(name)
    return _MICROSERVICE_NAME_VARIANTS.get(canonical_name, (name,))


def is_uuid(idfr):
    """Return true if ``idfr`` is a UUID."""
    return [8, 4, 4, 4, 12] == [
        len([x for x in y if x in "1234567890abcdef"]) for y in idfr.split("-")
    ]


def is_hdl(idfr, entity_type, accession_no=None):
    """Return ``True`` only if ``idfr`` is a handle, i.e. something like
    '12345/7432cdc5-a66a-4149-aa44-ebd802323196'.
    """
    try:
        _, pid = idfr.split("/")
    except ValueError:
        logger.info(
            "Unable to get exactly two values by splitting %s on a forward slash", idfr
        )
        return False
    if accession_no and entity_type == "aip":
        logger.info("PID %s should equal accession number %s", pid, accession_no)
        return pid == accession_no
    logger.info("PID %s should be a UUID", pid)
    return is_uuid(pid)


def normalize_ms_name(ms_name, vn):
    """Normalize the microservice name. This allows for different AM versions
    to use different names for the same microservice, without us having to
    change a whole bunch of feature files to accommodate such changes.
    """
    new_ms_name = ms_name
    if ms_name == "Approve normalization (review)" and vn != "1.6":
        new_ms_name = "Approve normalization Review"
    elif ms_name == "Store AIP (review)" and vn != "1.6":
        new_ms_name = "Store AIP Review"
    elif ms_name == "Store AIP Review" and vn == "1.6":
        new_ms_name = "Store AIP (review)"
    elif ms_name == "Approve normalization Review" and vn == "1.6":
        new_ms_name = "Approve normalization (review)"
    if ms_name != new_ms_name:
        logger.info('Treating microservice "%s" as "%s"', ms_name, new_ms_name)
    return new_ms_name


def parse_task_arguments_to_list(arguments):
    """Parse a string of Archivmatica task arguments to a list of arguments.
    E.g., parse something like::

        ('"a8e45bc1-eb35-4545-885c-dd552f1fde9a"'
         ' "/var/archivematica/sharedDirectory/watchedDirectories/
         'workFlowDecisions/selectFormatIDToolTransfer/'
         'arkivum1-5d15337f-c5e9-434f-a40f-14646ee2d2a2/'
         'objects/easy.txt"'
         ' "6d4cbcb8-d812-443c-8f02-2db113119518"'
         ' "--disable-reidentify")

    to::
        ['a8e45bc1-eb35-4545-885c-dd552f1fde9a',
         '/var/archivematica/sharedDirectory/watchedDirectories/'
         'workFlowDecisions/selectFormatIDToolTransfer/'
         'arkivum1-5d15337f-c5e9-434f-a40f-14646ee2d2a2/objects/easy.txt',
         '6d4cbcb8-d812-443c-8f02-2db113119518',
         '--disable-reidentify']

    WARNING: this function is flawed because not all arguments are enclosed in
    double quotes...
    """
    if arguments[0] == '"':
        arguments = arguments[1:]
    if arguments[-1] == '"':
        arguments = arguments[:-1]
    return arguments.split('" "')


def unixtimestamp():
    return int(time.time())


def all_urls_resolve(urls):
    """Return ``True`` only if all URLs in ``urls`` return good status codes
    when GET-requested.
    """
    for purl in urls:
        r = requests.get(purl)
        if r.status_code != 200:
            return False
    return True


def micro_service2group(micro_service):
    parts = micro_service.split("|")
    if len(parts) == 2:
        return tuple(parts)
    map_ = c.MICRO_SERVICES2GROUPS
    groups = None
    try:
        groups = map_[micro_service]
    except KeyError:
        for k, v in map_.items():
            if squash(k) == squash(micro_service):
                groups = v
                break
        if not groups:
            raise
    if len(groups) != 1:
        logger.warning(
            'WARNING: the micro-service "%s" belongs to multiple'
            ' micro-service groups; returning "%s"',
            micro_service,
            groups[0],
        )
    return micro_service, groups[0]
