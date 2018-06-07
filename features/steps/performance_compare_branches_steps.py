import logging
import json
import os
import re
import subprocess
import time

from behave import when, then, given
from features.steps import utils

logger = logging.getLogger('amauat.steps.performancenocapture')


def switch_to_version(context, version):
    context.scenario.transfer_uuid = None
    context.scenario.transfer_name = None
    context.scenario.sip_uuid = None

    docker_compose_path = getattr(context.am_user.docker, 'docker_compose_path', None)
    version = getattr(context.am_user.docker, version, None)

    if docker_compose_path is None:
        raise Exception("docker_compose_path parameter must be provided")

    if version is None:
        raise Exception(version + " parameter must be provided")

    package_versions = [re.split(" *: *", package) for package in re.split(" *, *", version)]

    for (package, version) in package_versions:
        package_dir = os.path.join(docker_compose_path, "..", "src", package)

        logger.info("Hard resetting '%s' to version %s" % (package_dir, version))

        subprocess.run(["git", "reset", "--hard", version],
                       cwd=package_dir)

    context.am_user.docker.stop_archivematica()
    context.am_user.docker.recreate_archivematica()

@given(u'an Archivematica instance running version_a')
def step_impl(context):
    switch_to_version(context, 'version_a')

@when(u'the user alters the Archivematica instance to run version_b')
def step_impl(context):
    switch_to_version(context, 'version_b')

def add_duration_float(tasks):
    for task in tasks:
        task['duration_float'] = utils.get_duration_as_float(task['duration'])
    return tasks

@when('the difference in runtime between {version_a_fname} and {version_b_fname} is printed')
def step_impl(context, version_a_fname, version_b_fname):
    version_a_stats = utils.get_stats_file_json(version_a_fname, context.am_user.permanent_path)
    version_b_stats = utils.get_stats_file_json(version_b_fname, context.am_user.permanent_path)

    logger.info('Total runtime for version_a tasks: %f; Total runtime for version_b tasks: %f',
                tasks_duration_seconds(version_a_stats['tasks']),
                tasks_duration_seconds(version_b_stats['tasks']))

# Helpers
# ------------------------------------------------------------------------------

def tasks_duration_seconds(tasks):
    timefmt = '%Y-%m-%d %H:%M:%S.%f'
    earliest = min([time.strptime(task['startTime'], timefmt) for task in tasks])
    latest = max([time.strptime(task['endTime'], timefmt) for task in tasks])

    return time.mktime(latest) - time.mktime(earliest)
