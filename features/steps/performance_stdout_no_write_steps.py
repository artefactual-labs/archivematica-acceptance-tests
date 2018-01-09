"""Steps for the Performance Testing When Output Streams Not Captured
Test/Feature.
"""

import json
import os
import time

from behave import when, then, given
from lxml import etree

from features.steps import utils

# ==============================================================================
# Step Definitions
# ==============================================================================

# Givens
# ------------------------------------------------------------------------------

@given('an Archivematica instance that {capture_output} client script output'
       ' streams to MCPServer')
def step_impl(context, capture_output):
    capture_output = {'passes': True}.get(capture_output, False)
    context.am_user.docker.recreate_archivematica(capture_output=capture_output)


# Whens
# ------------------------------------------------------------------------------

@when('the user alters the Archivematica instance to {capture_output} client'
      ' script output streams to MCPServer')
def step_impl(context, capture_output):
    del context.scenario.sip_uuid
    capture_output = {'passes': True}.get(capture_output, False)
    context.am_user.docker.recreate_archivematica(capture_output=capture_output)


@when('performance statistics are saved to {filename}')
def step_impl(context, filename):
    """Saves task statistics and the contents of the METS file of a
    transfer/AIP to a JSON file at ``filename`` suffixed with Unix timestamp in
    the permanent directory.

    Makes MySQL queries in a docker-compose-dependent way in order to do this.
    In future iterations, this should use AM's API, when that API is
    sufficiently developed.
    """
    sip_uuid = context.scenario.sip_uuid
    data = {'mets': etree.tostring(utils.get_mets_from_scenario(context),
                                   pretty_print=True).decode('utf8'),
            'tasks': context.am_user.docker.get_tasks_from_sip_uuid(
                sip_uuid)}
    filename = '{}-{}.json'.format(filename, int(time.time()))
    path = os.path.join(context.am_user.permanent_path, filename)
    with open(path, 'w') as fout:
        json.dump(data, fout, indent=4)
    context.scenario.performance_stats_path = path
    utils.logger.info('Set performance_stats_path to %s', path)


# Thens
# ------------------------------------------------------------------------------

@then('the size of the {without_outputs_fname} METS file is less than that of'
      ' the {with_outputs_fname} METS file')
def step_impl(context, without_outputs_fname, with_outputs_fname):
    without_outputs_stats = get_stats_file_json(
        without_outputs_fname, context.am_user.permanent_path)
    with_outputs_stats = get_stats_file_json(
        with_outputs_fname, context.am_user.permanent_path)
    without_outputs_mets = without_outputs_stats['mets']
    with_outputs_mets = with_outputs_stats['mets']
    without_outputs_mets_len = len(without_outputs_mets)
    with_outputs_mets_len = len(with_outputs_mets)
    utils.logger.info(
        'METS length for without output tasks: %d', without_outputs_mets_len)
    utils.logger.info(
        'METS length for with output tasks: %d', with_outputs_mets_len)
    assert without_outputs_mets_len < with_outputs_mets_len


@then('the runtime of client scripts in {without_outputs_fname} is less'
      ' than the runtime of client scripts in {with_outputs_fname}')
def step_impl(context, without_outputs_fname, with_outputs_fname):
    without_outputs_stats = get_stats_file_json(
        without_outputs_fname, context.am_user.permanent_path)
    with_outputs_stats = get_stats_file_json(
        with_outputs_fname, context.am_user.permanent_path)
    without_outputs_tasks = without_outputs_stats['tasks']
    with_outputs_tasks = with_outputs_stats['tasks']
    assert len(without_outputs_tasks) == len(with_outputs_tasks)
    without_outputs_tasks = add_duration_float(without_outputs_tasks)
    with_outputs_tasks = add_duration_float(with_outputs_tasks)
    wo_o_sum_tasks = sum(t['duration_float'] for t in without_outputs_tasks)
    w_o_sum_tasks = sum(t['duration_float'] for t in with_outputs_tasks)
    utils.logger.info('Total runtime for without output tasks: %f', wo_o_sum_tasks)
    utils.logger.info('Total runtime for with output tasks: %f', w_o_sum_tasks)
    assert wo_o_sum_tasks < w_o_sum_tasks


@then('performance statistics show output streams {verb} saved to the database')
def step_impl(context, verb):
    path = context.scenario.performance_stats_path
    with open(path) as fi:
        stats = json.load(fi)
    std_out_len_set = set([x['len_std_out'] for x in stats['tasks']])
    std_err_len_set = set([x['len_std_err'] for x in stats['tasks']])
    if verb == 'are':
        assert len(std_out_len_set) > 1
        assert len(std_err_len_set) > 1
    else:
        assert len(std_out_len_set) == 1, print(std_out_len_set)
        assert len(std_err_len_set) == 1, print(std_err_len_set)


@then('there is no stdout or stderr for the client scripts in {filename}')
def step_impl(context, filename):
    pass


@then('there is non-zero stdout and stderr for the client scripts in'
      ' {filename}')
def step_impl(context, filename):
    pass


# Helpers
# ------------------------------------------------------------------------------

def add_duration_float(tasks):
    for task in tasks:
        task['duration_float'] = utils.get_duration_as_float(task['duration'])
    return tasks


def get_newest_file_with_prefix(dirpath, filename_prefix):
    files = [f for f in os.listdir(dirpath) if f.startswith(filename_prefix)]
    return os.path.join(dirpath, sorted(files)[-1])


def get_stats_file_json(fname, permanent_path):
    fpath = get_newest_file_with_prefix(permanent_path, fname)
    utils.logger.info('file path for %s is %s', fname, fpath)
    with open(fpath) as fi:
        return json.load(fi)
