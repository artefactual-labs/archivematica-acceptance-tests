"""Steps for the UUIDs for the Direcotries Feature."""

import os
import pprint

from behave import then, given
from lxml import etree

from features.steps import utils

# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------

@given('remote directory {dir_path} contains a hierarchy of subfolders'
       ' containing digital objects')
def step_impl(context, dir_path):
    """Get a local copy of ``dir_path`` and assert that it contains at least
    one subfolder (subdirectory) and at least one file in a subfolder and then
    record the directory structure in ``context``.
    """
    if dir_path.startswith('~/'):
        dir_path = dir_path[2:]

    dir_is_zipped = bool(os.path.splitext(dir_path)[1])
    if dir_is_zipped:
        local_path = context.am_user.ssh.scp_server_file_to_local(
            dir_path)
    else:
        local_path = context.am_user.ssh.scp_server_dir_to_local(
            dir_path)
    if local_path is None:
        msg = (
            'Unable to copy item {} from the server to the local file'
            ' system. Server is not accessible via SSH.'.format(dir_path))
        utils.logger.warning(msg)
        raise Exception(msg)
    elif local_path is False:
        msg = (
            'Unable to copy item {} from the server to the local file'
            ' system. Attempt to scp the file failed.'.format(dir_path))
        utils.logger.warning(msg)
        raise Exception(msg)
    dir_local_path = local_path
    if dir_is_zipped:
        dir_local_path = context.utils.unzip(local_path)
    assert os.path.isdir(dir_local_path)
    non_root_paths = []
    non_root_file_paths = []

    # These are the names of the files that Archivematica will remove by
    # default. See MCPClient/lib/settings/common.py,
    # clientScripts/removeHiddenFilesAndDirectories.py, and
    # clientScripts/removeUnneededFiles.py.
    to_be_removed_files = [
        e.strip() for e in 'Thumbs.db, Icon, Icon\r, .DS_Store'.split(',')]

    for path, _, files in os.walk(dir_local_path):
        if path != dir_local_path:
            path = path.replace(dir_local_path, '', 1)
            non_root_paths.append(path)
            non_root_file_paths += [os.path.join(path, file_) for file_ in
                                    files if file_ not in to_be_removed_files]

    if dir_is_zipped:
        # If the "directory" from the server was a zip file, assume it is a
        # zipped bag and simulate "debagging" it, i.e., removing everything not
        # under data/ and removing the data/ prefix.
        non_root_paths = utils.debag(non_root_paths)
        non_root_file_paths = utils.debag(non_root_file_paths)

    assert len(non_root_paths) > 0
    assert len(non_root_file_paths) > 0
    context.scenario.remote_dir_subfolders = non_root_paths
    context.scenario.remote_dir_files = non_root_file_paths


@given('a processing configuration that assigns UUIDs to directories')
def step_impl(context):
    """Create a processing configuration that tells AM to assign UUIDs to
    directories.
    """
    context.execute_steps(
        'Given that the user has ensured that the default processing config is'
        ' in its default state\n'
        'And the processing config decision "Assign UUIDs to directories" is'
        ' set to "Yes"\n'
        'And the processing config decision "Select file format identification'
        ' command (Transfer)" is set to "Identify using Fido"\n'
        'And the processing config decision "Create SIP(s)" is set to "Create'
        ' single SIP and continue processing"\n'
        'And the processing config decision "Normalize" is set to "Normalize'
        ' for preservation"\n'
        'And the processing config decision "Approve normalization" is set to'
        ' "Yes"\n'
        'And the processing config decision "Bind PIDs" is set to "No"\n'
        'And the processing config decision "Select file format identification'
        ' command (Submission documentation & metadata)" is set to'
        ' "Identify using Fido"\n'
        'And the processing config decision "Perform policy checks on'
        ' preservation derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on access'
        ' derivatives" is set to "No"\n'
        'And the processing config decision "Perform policy checks on'
        ' originals" is set to "No"\n'
    )


@given('default processing configured to assign UUIDs to directories')
def step_impl(context):
    context.execute_steps(
        'Given the processing config decision "Assign UUIDs to directories" is'
        ' set to "Yes"\n')


# Thens
# ------------------------------------------------------------------------------

@then('the METS file includes the original directory structure')
def step_impl(context):
    """Asserts that the <mets:structMap> element of the AIP METS file correctly
    encodes the directory structure of the transfer that was recorded in an
    earlier step under the following attributes::

        context.scenario.remote_dir_subfolders
        context.scenario.remote_dir_files

    NOTE: empty directories in the transfer are not indicated in the resulting
    AIP METS.
    """
    context.scenario.mets = mets = utils.get_mets_from_scenario(context)
    ns = context.am_user.mets.mets_nsmap
    struct_map_el = mets.find('.//mets:structMap[@TYPE="physical"]', ns)
    subpaths = utils.get_subpaths_from_struct_map(struct_map_el, ns)
    subpaths = [p.replace('/objects', '', 1) for p in
                filter(None, utils.remove_common_prefix(subpaths))]
    for dirpath in context.scenario.remote_dir_subfolders:
        assert dirpath in subpaths, (
            'Expected directory path\n{}\nis not in METS structmap'
            ' paths\n{}'.format(dirpath, pprint.pformat(subpaths)))
    for filepath in context.scenario.remote_dir_files:
        if os.path.basename(filepath) == '.gitignore':
            continue
        assert filepath in subpaths, (
            'Expected file path\n{}\nis not in METS structmap'
            ' paths\n{}'.format(filepath, pprint.pformat(subpaths)))


@then('the UUIDs for the subfolders and digital objects are written to the METS'
      ' file')
def step_impl(context):
    mets = context.scenario.mets
    ns = context.am_user.mets.mets_nsmap
    struct_map_el = mets.find('.//mets:structMap[@TYPE="physical"]', ns)
    for dirpath in context.scenario.remote_dir_subfolders:
        dirname = os.path.basename(dirpath)
        mets_div_el = struct_map_el.find(
            './/mets:div[@LABEL="{}"]'.format(dirname), ns)
        assert mets_div_el is not None, (
            'Could not find a <mets:div> for directory at {}'.format(
                dirpath))
        dmdid = mets_div_el.get('DMDID')
        dmdSec_el = mets.find('.//mets:dmdSec[@ID="{}"]'.format(dmdid), ns)
        assert dmdSec_el is not None, (
            'Could not find a <mets:dmdSec> for directory at {}'.format(
                dirpath))
        try:
            id_type = dmdSec_el.find('.//premis3:objectIdentifierType', ns).text.strip()
            id_val = dmdSec_el.find('.//premis3:objectIdentifierValue', ns).text.strip()
        except AttributeError:
            utils.logger.info(ns)
            msg = etree.tostring(dmdSec_el, pretty_print=True)
            print(msg)
            utils.logger.info(msg)
            #raise AssertionError('Unable to find objectIdentifierType/Value')
            raise
        assert id_type == 'UUID'
        assert utils.is_uuid(id_val)
