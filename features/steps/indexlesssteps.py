"""Steps for the Indexless ("No Elasticsearch") Feature."""

import os

from behave import when, then, given

# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------

@given('Archivematica deployment method {method} which provides an option to'
       ' exclude Elasticsearch')
def step_impl(context, method):
    """This is an empty given. It should remain empty."""
    pass


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
    """
    context.scenario.idxls_dply_method = method


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
    es_indexing_config_text = context.am_sel_cli.get_es_indexing_config_text()
    assert es_indexing_config_text is not None
    assert es_indexing_config_text.strip() == (
        'Elasticsearch indexing has been disabled in this Archivematica'
        ' installation')


@then('Elasticsearch is not running')
def step_impl(context):
    """Steps to perform assertion:
    1. Run `docker-compose ps` and expect NOT to find "elastic" in the output.
    2. Run `docker-compose exec archivematica-mcp-client curl
       http://elasticsearch:9200/` and expect to see `'Could not resolve host:
       elasticsearch'` in the response.
    """
    if context.scenario.idxls_dply_method == 'docker-compose':
        docker_compose_path = os.path.join(
            context.am_sel_cli.docker_compose_path, 'docker-compose.yml')
        import subprocess
        NAME = slice(0, 42)
        STATE = slice(75, 86)
        stdout = subprocess.check_output([
            'sudo',
            'docker-compose',
            '-f',
            docker_compose_path ,
            'ps']).decode('utf8').splitlines()
        es_ps = None
        for line in stdout:
            name = line[NAME].strip().lower()
            state = line[STATE].strip().lower()
            if 'elasticsearch' in name:
                es_ps = {'name': name, 'state': state}
        try:
            assert es_ps is None
        except AssertionError:
            assert es_ps['state'] != 'up'


@then('Elasticsearch is not installed')
def step_impl(context):
    """Steps to perform assertion:
    1. Run `docker-compose images` and expect NOT to find "elastic" in the output.
    Note: this will fail because the current automated way of deploying AM with
    docker-compose without ES is to simply stop the ES process after
    orchestrating the build. Therefore, an ES container will have been built,
    it will simply not be running.
    """
    pass
