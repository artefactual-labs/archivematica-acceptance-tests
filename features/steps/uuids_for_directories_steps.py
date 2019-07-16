"""Steps for the UUIDs for the Direcotries Feature."""

import logging
import os
import pprint

from behave import then, given
from lxml import etree

from features.steps import utils


logger = logging.getLogger("amauat.steps.uuidsdirectories")


# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------


@given(
    "remote directory {dir_path} contains a hierarchy of subfolders"
    " containing digital objects"
)
def step_impl(context, dir_path):
    """Get a local copy of ``dir_path`` and assert that it contains at least
    one subfolder (subdirectory) and at least one file in a subfolder and then
    record the directory structure in ``context``.
    """
    if dir_path.startswith("~/"):
        dir_path = "/home/{}/{}".format(context.HOME, dir_path[2:])

    dir_is_zipped = bool(os.path.splitext(dir_path)[1])
    if dir_is_zipped:
        if getattr(context.am_user.docker, "docker_compose_path", None):
            local_path = context.am_user.docker.cp_server_file_to_local(dir_path)
        elif context.am_user.ssh_accessible:
            local_path = context.am_user.ssh.scp_server_file_to_local(dir_path)
        else:
            local_path = context.am_user.localfs.read_server_file(dir_path)
    else:
        if getattr(context.am_user.docker, "docker_compose_path", None):
            local_path = context.am_user.docker.cp_server_dir_to_local(dir_path)
        elif context.am_user.ssh_accessible:
            local_path = context.am_user.ssh.scp_server_dir_to_local(dir_path)
        else:
            local_path = context.am_user.localfs.read_server_file(dir_path)
    if local_path is None:
        msg = (
            "Unable to copy item {} from the server to the local file"
            " system.".format(dir_path)
        )
        logger.warning(msg)
        raise Exception(msg)
    elif local_path is False:
        msg = (
            "Unable to copy item {} from the server to the local file"
            " system. Attempt to copy the file/dir failed.".format(dir_path)
        )
        logger.warning(msg)
        raise Exception(msg)
    dir_local_path = local_path
    if dir_is_zipped:
        dir_local_path = utils.unzip(local_path)
    assert os.path.isdir(dir_local_path), "%s is not a directory" % dir_local_path
    non_root_paths = []
    non_root_file_paths = []
    empty_dirs = []

    # These are the names of the files that Archivematica will remove by
    # default. See MCPClient/lib/settings/common.py,
    # clientScripts/removeHiddenFilesAndDirectories.py, and
    # clientScripts/removeUnneededFiles.py.
    to_be_removed_files = [
        e.strip() for e in "Thumbs.db, Icon, Icon\r, .DS_Store".split(",")
    ]

    for path, dirs, files in os.walk(dir_local_path):
        if path != dir_local_path:
            path = path.replace(dir_local_path, "", 1)
            non_root_paths.append(path)
            files = [
                os.path.join(path, file_)
                for file_ in files
                if file_ not in to_be_removed_files
            ]
            non_root_file_paths += files
            if (not dirs) and (not files):
                empty_dirs.append(path)

    if dir_is_zipped:
        # If the "directory" from the server was a zip file, assume it is a
        # zipped bag and simulate "debagging" it, i.e., removing everything not
        # under data/ and removing the data/ prefix.
        non_root_paths = utils.debag(non_root_paths)
        non_root_file_paths = utils.debag(non_root_file_paths)

    assert non_root_paths
    assert non_root_file_paths
    context.scenario.remote_dir_subfolders = non_root_paths
    context.scenario.remote_dir_files = non_root_file_paths
    context.scenario.remote_dir_empty_subfolders = empty_dirs


@given("a processing configuration that assigns UUIDs to directories")
def step_impl(context):
    """Create a processing configuration that tells AM to assign UUIDs to
    directories.
    """
    context.execute_steps(
        "Given that the user has ensured that the default processing config is"
        " in its default state\n"
        'And the processing config decision "Assign UUIDs to directories" is'
        ' set to "Yes"\n'
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Yes"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
        ' single SIP and continue processing"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"\n'
        'And the processing config decision "Approve normalization" is set to'
        ' "Yes"\n'
        'And the processing config decision "Bind PIDs" is set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Submission documentation & metadata)" is set to'
        ' "Yes"\n'
        'And the processing config decision "Perform policy checks on'
        ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
        ' derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "No"\n'
        'And the processing config decision "Document empty directories"'
        ' is set to "Yes"\n'
        'And the processing config decision "Store AIP" is set to "Yes"\n'
        'And the processing config decision "Store AIP location" is set to "Default location"\n'
    )


@given("default processing configured to assign UUIDs to directories")
def step_impl(context):
    context.execute_steps(
        'Given the processing config decision "Assign UUIDs to directories" is'
        ' set to "Yes"\n'
    )


@given("default processing configured to assign UUIDs to all directories")
def step_impl(context):
    context.execute_steps(
        'Given the processing config decision "Assign UUIDs to directories" is'
        ' set to "Yes"\n'
        'And the processing config decision "Document empty directories" is'
        ' set to "Yes"\n'
    )


# Thens
# ------------------------------------------------------------------------------


@then("the METS file includes the original directory structure")
def step_impl(context):
    """Asserts that the <mets:structMap> element of the AIP METS file correctly
    encodes the directory structure of the transfer that was recorded in an
    earlier step under the following attributes::

        context.scenario.remote_dir_subfolders
        context.scenario.remote_dir_files
        context.scenario.remote_dir_empty_subfolders

    NOTE: empty directories in the transfer are not indicated in the resulting
    AIP METS.
    """
    context.scenario.mets = mets = utils.get_mets_from_scenario(context, api=True)
    ns = context.am_user.mets.mets_nsmap
    for type_, xpath in (
        ("physical", './/mets:structMap[@TYPE="physical"]'),
        ("logical", './/mets:structMap[@LABEL="Normative Directory Structure"]'),
    ):
        struct_map_el = mets.find(xpath, ns)
        assert (
            struct_map_el is not None
        ), "We expected to find a {}-type structMap but did not".format(type_)
        subpaths = utils.get_subpaths_from_struct_map(struct_map_el, ns)
        subpaths = [
            p.replace("/objects", "", 1)
            for p in filter(None, utils.remove_common_prefix(subpaths))
        ]
        for dirpath in context.scenario.remote_dir_subfolders:
            if (type_ == "physical") and (
                dirpath in context.scenario.remote_dir_empty_subfolders
            ):
                continue
            assert dirpath in subpaths, (
                "Expected directory path\n{}\nis not in METS structmap"
                " paths\n{}".format(dirpath, pprint.pformat(subpaths))
            )
        if type == "physical":
            for filepath in context.scenario.remote_dir_files:
                if os.path.basename(filepath) == ".gitignore":
                    continue
                assert filepath in subpaths, (
                    "Expected file path\n{}\nis not in METS structmap"
                    " paths\n{}".format(filepath, pprint.pformat(subpaths))
                )


@then(
    "the UUIDs for the subfolders and digital objects are written to the METS" " file"
)
def step_impl(context):
    """Make the following assertions:
    - All directories are listed in the logical (Normative Directory Structure)
      structMap.
    - All directories except for the empty one(s) are listed in the physical
      structMap.
    - All non-empty directories in the physical structMap link to a dmdSec that
      documents the directory's UUID identifier.
    - All empty directories in the logical structMap link to a dmdSec that
      documents the directory's UUID identifier.
    """
    mets = context.scenario.mets
    ns = context.am_user.mets.mets_nsmap
    for type_, xpath in (
        ("physical", './/mets:structMap[@TYPE="physical"]'),
        ("logical", './/mets:structMap[@LABEL="Normative Directory Structure"]'),
    ):
        struct_map_el = mets.find(xpath, ns)
        assert struct_map_el is not None
        for dirpath in context.scenario.remote_dir_subfolders:
            if (
                type_ == "physical"
                and dirpath in context.scenario.remote_dir_empty_subfolders
            ):
                continue
            dirname = os.path.basename(dirpath)
            mets_div_el = struct_map_el.find(
                './/mets:div[@LABEL="{}"]'.format(dirname), ns
            )
            assert (
                mets_div_el is not None
            ), "Could not find a <mets:div> for directory at {}".format(dirpath)
            if (
                type_ == "logical"
                and dirpath not in context.scenario.remote_dir_empty_subfolders
            ):
                continue
            dmdid = mets_div_el.get("DMDID")
            dmdSec_el = mets.find('.//mets:dmdSec[@ID="{}"]'.format(dmdid), ns)
            assert (
                dmdSec_el is not None
            ), "Could not find a <mets:dmdSec> for directory at {}".format(dirpath)
            try:
                id_type = dmdSec_el.find(
                    ".//premis3:objectIdentifierType", ns
                ).text.strip()
                id_val = dmdSec_el.find(
                    ".//premis3:objectIdentifierValue", ns
                ).text.strip()
            except AttributeError:
                logger.info(ns)
                msg = etree.tostring(dmdSec_el, pretty_print=True)
                print(msg)
                logger.info(msg)
                raise
            assert id_type == "UUID"
            assert utils.is_uuid(id_val)
            logger.info(
                'Found UUID for directory "%s" in %s-type structmap', dirpath, type_
            )
