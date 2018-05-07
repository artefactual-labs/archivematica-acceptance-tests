"""Steps for the Indexless ("No Elasticsearch") Feature."""

import logging
import os
import re

from behave import when, then, given
from lxml import etree

from features.steps import utils


logger = logging.getLogger('amauat.steps.indexless')


# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------

@given('Archivematica deployment method {method} which provides an option to'
       ' exclude Elasticsearch')
def step_impl(context, method):
    """This is an empty given. It should remain empty."""
    logger.info('We are assuming that Archivematica deployment method'
                      ' "%s" allows for "headless", i.e., Elasticsearch-less'
                      ' deployments', method)


@given('an Archivematica instance with Indexing disabled')
def step_impl(context):
    """This is an empty given. It should remain empty."""
    logger.info('We are assuming that the Archivematica instance we are'
                      ' targetting has been deployed headlessly.')


@given('local indexed AIP at {indexed_AIP} created from {transfer_path} with'
       ' Indexing enabled')
def step_impl(context, indexed_AIP, transfer_path):
    """The path ``indexed_AIP`` should point to a .7z file which, when is the
    result of creating an AIP from the transfer source at ``transfer_path`` (by
    using the processing config specified by
    ``'Given a default processing config that creates and stores an AIP'``.
    """
    assert os.path.exists(indexed_AIP)
    assert os.path.isfile(indexed_AIP)


# Whens
# ------------------------------------------------------------------------------

@when('Archivematica is deployed without Elasticsearch using method {method}')
def step_impl(context, method):
    """This is an empty when, but it could be populated.

    Populating it would entail writing a function that deploys an AM instance
    using deployment method ``method``, which will initially be
    'docker-compose'. Here is a rough draft of a recipe for deploying
    Index-less AM using docker, docker-compose, and the am.git repo.

    1. Save `method` (e.g., 'docker') in `context.scenario.deployment_method` for
       later use.
    2. Execute these commands::

        $ git clone https://github.com/artefactual-labs/am.git
        $ cd am
        $ git submodule update --init --recursive
        $ cd src/archivematica
        $ git checkout -b dev/1.8.x origin/dev/1.8.x
        $ cd ../archivematica-storage-service
        $ git checkout qa/0.x
        $ cd ../../compose/
        $ make create-volumes
        $ docker-compose -f docker-compose-no-indexing.yml up -d --build
        $ make bootstrap
        $ make restart-am-services

    A manual installation from packages probably cannot be performed via behave
    because it requires responding to prompts during the apt install process,
    e.g., to add the MySQL root and archivematica user passwords.
    """
    context.scenario.idxls_dply_method = method
    if method == 'manual':
        logger.info(
            'Manual headless Archivematica installation cannot be performed by'
            ' these acceptance tests.')
    else:
        logger.info(
            'These acceptance tests could be modified to deploy headless'
            ' Archivematica using Vagrant/Ansible or Docker Compose.')


@when('processing config decision "{pc_decision}" is inspected')
def step_impl(context, pc_decision):
    """Create SIP(s)"""
    options = context.am_user.browser.get_processing_config_decision_options(
        decision_label=pc_decision)
    context.scenario.decision_options = options


@when('the user queries the API until the AIP has been stored')
def step_impl(context):
    """Query the SS API for context.scenario.sip_uuid."""
    context.am_user.api.poll_until_aip_stored(
        context.scenario.sip_uuid, context.am_user.browser.ss_api_key)


@when('the user decompresses the local AIP at {indexed_aip_path}')
def step_impl(context, indexed_aip_path):
    indexed_aip_path = os.path.join(context.am_user.here, indexed_aip_path)
    cwd = os.path.dirname(indexed_aip_path)
    context.scenario.indexed_aip_path = context.am_user.decompress_aip(
        indexed_aip_path, cwd=cwd)


@when('the user navigates to the Archivematica instance')
def step_impl(context):
    context.am_user.browser.navigate(context.am_user.get_transfer_url())


@when('the user navigates to the {tab_name}')
def step_impl(context, tab_name):
    tab_name = tab_name.replace(' tab', '').strip().lower()
    url_getter = {
        'backlog': context.am_user.browser.get_transfer_backlog_url,
        'appraisal': context.am_user.browser.get_appraisal_url,
        'archival storage': context.am_user.browser.get_archival_storage_url,
        'ingest': context.am_user.browser.get_ingest_url
    }[tab_name]
    context.am_user.browser.navigate(url_getter())


# Thens
# ------------------------------------------------------------------------------

@then('the installation has Indexing disabled')
def step_impl(context):
    """Steps to perform assertion:
    1. Navigate to http://127.0.0.1:62080/administration/general/
    2. Expect to find a `p.es-indexing-configuration` element
    3. Expect that element to contain exactly this text: "Elasticsearch
       indexing has been disabled in this Archivematica installation"
    """
    es_indexing_config_text = context.am_user.browser.get_es_indexing_config_text()
    assert es_indexing_config_text is not None
    assert es_indexing_config_text.strip() == (
        'Elasticsearch indexing has been disabled in this Archivematica'
        ' installation')


@then('Elasticsearch is not installed')
def step_impl(context):
    """Steps to perform assertion:
    1. With a docker-compose deployment method:
       Run ``docker-compose ps`` and expect NOT to find any "elastic" container
       process in the output.
    2. With a Vagrant/Ansible deployment method:
       Run ``ssh ls /etc/init.d/elasticsearch`` and expect NOT to find such a
       file.
    3. TODO: with a manual deployment method: ...
    """
    method = context.scenario.idxls_dply_method
    if context.scenario.idxls_dply_method == 'docker-compose':
        ps_names_states = context.am_user.docker.get_process_names_states()
        es_ps = None
        for name_state in ps_names_states:
            if 'elasticsearch' in name_state['name']:
                es_ps = name_state
                break
        try:
            assert es_ps is None
        except AssertionError:
            logger.warning(
                'An Elasticsearch container is running when we expect it not to'
                ' be. Its state is %s', es_ps['state'])
            raise
    elif context.scenario.idxls_dply_method in ('ansible', 'manual'):
        context.am_user.ssh.assert_elasticsearch_not_installed()
    else:
        logger.warning(
            'The "Then Elasticsearch is not running" step is not implemented'
            ' for deployment method "%s".', method)


@then('there is no "Send to backlog" option')
def step_impl(context):
    """How to implement: assert that none of the options in the context match
    "Send to backlog".
    """
    assert isinstance(context.scenario.decision_options, list)
    assert 'Send to backlog' not in context.scenario.decision_options


@then('the "Index AIP" micro-service output indicates that no indexing has'
      ' occurred')
def step_impl(context):
    unit_type = utils.get_normalized_unit_type('ingest')
    uuid_val = utils.get_uuid_val(context, unit_type)
    job = context.am_user.browser.parse_job(
        'Index AIP', uuid_val, unit_type=unit_type)
    for task_data in job['tasks'].values():
        assert ('Skipping indexing: indexing is currently disabled.' in
                task_data['stderr'])


@then('the AIP is identical in all relevant repects to local indexed AIP at'
      ' etc/aips/pictures.7z')
def step_impl(context):
    indexless_aip_path = context.scenario.aip_path
    indexed_aip_path = context.scenario.indexed_aip_path
    assert os.path.isdir(indexless_aip_path)
    assert os.path.isdir(indexed_aip_path)
    indexless_dirname = _remove_uuid_suffix(
        os.path.basename(indexless_aip_path.rstrip('/')))
    indexed_dirname = _remove_uuid_suffix(
        os.path.basename(indexed_aip_path.rstrip('/')))
    indexless_rel_paths = _get_rel_paths(indexless_aip_path)
    indexed_rel_paths = _get_rel_paths(indexed_aip_path)
    assert len(indexless_rel_paths) == len(indexed_rel_paths)
    # Assert that each path in the indexless AIP has a counterpart path in the
    # indexed AIP. A counterpart path may be exactly identical or it may be
    # identical except that it contains a different UUID or the name of the AIP
    # followed by a hyphen and a UUID.
    for rel_path in indexless_rel_paths:
        counterpart = _get_path_counterpart(
            rel_path, indexed_rel_paths, indexless_dirname, indexed_dirname)
        assert counterpart, (
            logger.warning(
                'Relative path %s in the indexless AIP has no counterpart in'
                ' the indexed one', rel_path))
        logger.info(
            'Relative path %s in the indexless AIP matches %s in'
            ' the indexed one', rel_path, counterpart)
    indexless_uuid = os.path.basename(
        indexless_aip_path.rstrip('/')).split('-', 1)[1]
    indexed_uuid = os.path.basename(
        indexed_aip_path.rstrip('/')).split('-', 1)[1]
    indexless_mets_path = os.path.join(
        indexless_aip_path, 'data', 'METS.{}.xml'.format(indexless_uuid))
    indexed_mets_path = os.path.join(
        indexed_aip_path, 'data', 'METS.{}.xml'.format(indexed_uuid))
    assert os.path.isfile(indexless_mets_path), '{} is not a file'.format(
        indexless_mets_path)
    assert os.path.isfile(indexed_mets_path), '{} is not a file'.format(
        indexless_mets_path)
    with open(indexless_mets_path) as filei:
        indexless_mets = etree.parse(filei)
    with open(indexed_mets_path) as filei:
        indexed_mets = etree.parse(filei)
    _assert_mets_files_equivalent(indexless_mets, indexed_mets,
                                  context.am_user.mets)


@then('the {tab_name} is not displayed in the navigation bar')
def step_impl(context, tab_name):
    displayed_tabs = [t.lower() for t in
                      context.am_user.browser.get_displayed_tabs()]
    tab_name = tab_name.replace(' tab', '').strip().lower()
    assert displayed_tabs
    assert 'transfer' in displayed_tabs, '"transfer" is not in {}'.format(
        str(displayed_tabs))  # sanity check
    assert tab_name not in displayed_tabs


@then('a warning is displayed indicating that the {tab_name} is not'
      ' operational')
def step_impl(context, tab_name):
    tab_name = tab_name.replace(' tab', '').strip().lower()
    msg1 = 'Elasticsearch Indexing Disabled'
    msg2 = 'The {} tab is non-functional'.format(tab_name)
    page_text = context.am_user.browser.driver.find_element_by_tag_name(
        'body').text
    assert msg1 in page_text
    assert msg2 in page_text


@then('the SIP Arrange pane is not displayed')
def step_impl(context):
    context.am_user.browser.assert_sip_arrange_pane_not_displayed()


@then('the "Create SIP(s)" decision point does not have a "Send to backlog" option')
def step_impl(context):
    context.am_user.browser.assert_no_option(
        'Send to backlog', 'Create SIP(s)', context.scenario.transfer_uuid)


# ==============================================================================
# Helper Functions
# ==============================================================================

def _assert_mets_files_equivalent(indexless_mets, indexed_mets, mets_ability):
    """Here we extract all the PREMIS events from each METS file and assert
    that both mets files have the same number of each type of PREMIS event.
    More thorough "sameness" tests could be performed but this is sufficient
    for now.
    """
    indexless_pevents = mets_ability.get_premis_events(indexless_mets)
    indexed_pevents = mets_ability.get_premis_events(indexed_mets)
    for event_type in (
            'creation', 'message digest calculation', 'validation',
            'fixity check', 'ingestion', 'virus check', 'name cleanup',
            'format identification', 'normalization'):
        indexless_event_count = len(
            [e for e in indexless_pevents if e['event_type'] == event_type])
        indexed_event_count = len(
            [e for e in indexed_pevents if e['event_type'] == event_type])
        assert indexless_event_count == indexed_event_count, (
            'The indexless METS file has {} PREMIS events while the indexed'
            ' METS file has {}'.format(
                indexless_event_count, indexed_event_count))


def _get_rel_paths(path):
    """Return a list of all relative paths within the directory at ``path``."""
    rel_paths = []
    for root, _, files in os.walk(path):
        rel_path = root.replace(path, '', 1).lstrip('/')
        if rel_path:
            rel_paths.append(rel_path)
        for file_ in files:
            rel_path = os.path.join(root, file_).replace(
                path, '', 1).lstrip('/')
            if rel_path:
                rel_paths.append(rel_path)
    return rel_paths


uuid_pattern = re.compile(
    '[a-f0-9]{8}-'
    '[a-f0-9]{4}-'
    '[a-f0-9]{4}-'
    '[a-f0-9]{4}-'
    '[a-f0-9]{12}')


def _flatten_uuids(path):
    """Replace all UUID strings in ``path`` with the string ``'UUID'``."""
    return re.sub(uuid_pattern, 'UUID', path)


def _remove_uuid_suffix(string):
    """Remove all ``-<UUID>`` type strings from ``string``."""
    return re.sub(re.compile('-' + uuid_pattern.pattern), '', string)


def _flatten_name_uuids(path, name):
    """Replace all ``<name>-<UUID>`` type strings in ``path`` with the string
    ``'NAME-UUID'``.
    """
    pattern = re.compile(name + '-' + uuid_pattern.pattern)
    return re.sub(pattern, 'NAME-UUID', path)


def _get_path_counterpart(needle, haystack, needle_name, haystack_name):
    """Return the counterpart to ``needle`` in ``haystack`` where a
    counterpart is an exact match or an exact match except all UUIDs in the
    path are replaced by ``'UUID'`` or an exact match except all NAME-UUID type
    strings are replaced by ``'NAME-UUID'``. If there is no counterpart, return
    ``None``.
    """
    if needle in haystack:
        return needle
    flattened_rel_paths = {_flatten_uuids(o): o for o in haystack}
    try:
        return flattened_rel_paths[_flatten_uuids(needle)]
    except KeyError:
        flattened_rel_paths = {
            _flatten_name_uuids(o, haystack_name): o for o in haystack}
        return flattened_rel_paths.get(_flatten_name_uuids(needle, needle_name))
