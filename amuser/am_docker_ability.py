"""Archivematica Docker Ability

This module contains the ``ArchivematicaDockerAbility`` class, which encodes the
ability of an Archivematica user to use Docker to interact configure and deploy
Archivematica.
"""

import logging
import os
import shlex
import subprocess

from . import base


logger = logging.getLogger("amuser.docker")


class ArchivematicaDockerAbility(base.Base):
    """Archivematica Docker Ability: the ability of an Archivematica user to use
    Docker configure and deploy Archivematica.
    """

    @property
    def docker_compose_file_path(self):
        return os.path.join(self.docker_compose_path, "docker-compose.yml")

    def recreate_archivematica(self, capture_output=False):
        """Recreate the docker-compose deploy of Archivematica by calling
        docker-compose's ``up`` subcommand.
        """
        dc_recreate_cmd = "docker-compose -f {} up -d".format(
            self.docker_compose_file_path
        )
        capture_output = {True: "true"}.get(capture_output, "false")
        env = dict(os.environ, AM_CAPTURE_CLIENT_SCRIPT_OUTPUT=capture_output)
        subprocess.check_output(shlex.split(dc_recreate_cmd), env=env)

    def get_tasks_from_sip_uuid(
        self, sip_uuid, mysql_user="root", mysql_password="12345"
    ):
        """Use ``docker-compose exec mysql`` to get all tasks used to create a
        given SIP as a list of dicts.
        """
        tasks = []
        sql_query = (
            "SELECT t.fileUUID as file_uuid,"
            " f.fileSize as file_size,"
            " LENGTH(t.stdOut) as len_std_out,"
            " LENGTH(t.stdError) as len_std_err,"
            " t.exec,"
            " t.exitCode,"
            " t.endTime,"
            " t.startTime,"
            " TIMEDIFF(t.endTime,t.startTime) as duration"
            " FROM Tasks t"
            " INNER JOIN Files f ON f.fileUUID=t.fileUUID"
            " WHERE f.sipUUID='{}'"
            " ORDER by endTime-startTime, exec;".format(sip_uuid)
        )
        cmd_str = 'docker-compose exec mysql mysql -u {} -p{} MCP -e "{}"'.format(
            mysql_user, mysql_password, sql_query
        )
        res = subprocess.check_output(
            shlex.split(cmd_str), cwd=self.docker_compose_path
        ).decode("utf8")
        lines = [l for l in res.splitlines() if l.startswith("|")]
        keys = [k.strip() for k in lines[0].strip(" |").split("|")]
        for line in lines[1:]:
            vals = [v.strip() for v in line.strip(" |").split("|")]
            tasks.append(dict(zip(keys, vals)))
        return tasks

    def get_processes(self):
        return (
            subprocess.check_output(
                ["docker-compose", "-f", self.docker_compose_file_path, "ps"]
            )
            .decode("utf8")
            .splitlines()
        )

    def get_process_names_states(self):
        NAME = slice(0, 42)
        STATE = slice(75, 86)
        names_and_states = []
        for line in self.get_processes():
            name = line[NAME].strip().lower()
            state = line[STATE].strip().lower()
            names_and_states.append({"name": name, "state": state})
        return names_and_states

    def _get_container_id(self, docker_container_name):
        try:
            docker_compose_path = self.docker_compose_path
        except AttributeError:
            logger.error("No docker compose path provided.")
            raise
        return (
            subprocess.check_output(
                shlex.split("docker-compose ps -q {}".format(docker_container_name)),
                cwd=docker_compose_path,
            )
            .decode("utf8")
            .strip()
        )

    def cp_server_file_to_local(self, server_file_path):
        """Use ``docker cp`` to copy a file from the docker container to our
        local tmp directory.
        """
        docker_container_name = "archivematica-storage-service"
        docker_container_id = self._get_container_id(docker_container_name)
        filename = os.path.basename(server_file_path)
        local_path = os.path.join(self.tmp_path, filename)
        subprocess.check_output(
            shlex.split(
                "docker cp {}:{} {}".format(
                    docker_container_id, server_file_path, local_path
                )
            ),
            cwd=self.docker_compose_path,
        ).decode("utf8").strip()
        if os.path.isfile(local_path):
            return local_path
        logger.info("Failed to `docker cp` %s to %s", server_file_path, local_path)
        return False

    def cp_server_dir_to_local(self, server_dir_path):
        """Use ``docker cp`` to copy a directory from the docker container to
        our local tmp directory.
        """
        docker_container_name = "archivematica-storage-service"
        docker_container_id = self._get_container_id(docker_container_name)
        server_dir_path = server_dir_path.rstrip("/")
        dirname = os.path.basename(server_dir_path)
        local_path = os.path.join(self.tmp_path, dirname)
        subprocess.check_output(
            shlex.split(
                "docker cp {}:{} {}".format(
                    docker_container_id, server_dir_path, local_path
                )
            ),
            cwd=self.docker_compose_path,
        ).decode("utf8").strip()
        if os.path.isdir(local_path):
            return local_path
        logger.info("Failed to `docker cp` %s to %s", server_dir_path, local_path)
        return False
