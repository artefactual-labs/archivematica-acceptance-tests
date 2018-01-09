"""Archivematica Docker Ability

This module contains the ``ArchivematicaDockerAbility`` class, which encodes the
ability of an Archivematica user to use Docker to interact configure and deploy
Archivematica.
"""

import os
import shlex
import subprocess

from . import utils
from . import base


LOGGER = utils.LOGGER


class ArchivematicaDockerAbility(base.Base):
    """Archivematica Docker Ability: the ability of an Archivematica user to use
    Docker configure and deploy Archivematica.
    """

    @property
    def docker_compose_file_path(self):
        return os.path.join(self.docker_compose_path, 'docker-compose.yml')

    def recreate_archivematica(self, capture_output=False):
        """Recreate the docker-compose deploy of Archivematica by calling
        docker-compose's ``up`` subcommand.
        """
        dc_recreate_cmd = 'docker-compose -f {} up -d'.format(
            self.docker_compose_file_path)
        capture_output = {True: 'true'}.get(capture_output, 'false')
        env = dict(os.environ,
                   AM_CAPTURE_CLIENT_SCRIPT_OUTPUT=capture_output)
        subprocess.check_output(shlex.split(dc_recreate_cmd), env=env)

    def get_tasks_from_sip_uuid(self, sip_uuid, mysql_user='root',
                                mysql_password='12345'):
        """Use ``docker-compose exec mysql`` to get all tasks used to create a
        given SIP as a list of dicts.
        """
        tasks = []
        sql_query = (
            'SELECT t.fileUUID as file_uuid,'
            ' f.fileSize as file_size,'
            ' LENGTH(t.stdOut) as len_std_out,'
            ' LENGTH(t.stdError) as len_std_err,'
            ' t.exec,'
            ' t.endTime,'
            ' t.startTime,'
            ' TIMEDIFF(t.endTime,t.startTime) as duration'
            ' FROM Tasks t'
            ' INNER JOIN Files f ON f.fileUUID=t.fileUUID'
            ' WHERE f.sipUUID=\'{}\''
            ' ORDER by endTime-startTime, exec;'.format(sip_uuid))
        cmd_str = (
            'docker-compose exec mysql mysql -u {} -p{} MCP -e "{}"'.format(
                mysql_user, mysql_password, sql_query))
        res = subprocess.check_output(
            shlex.split(cmd_str),
            cwd=self.docker_compose_path).decode('utf8')
        lines = [l for l in res.splitlines() if l.startswith('|')]
        keys = [k.strip() for k in lines[0].strip(' |').split('|')]
        for line in lines[1:]:
            vals = [v.strip() for v in line.strip(' |').split('|')]
            tasks.append(dict(zip(keys, vals)))
        return tasks
