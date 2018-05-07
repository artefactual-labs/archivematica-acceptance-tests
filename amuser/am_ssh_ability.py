"""Archivematica SSH Ability

This module contains the ``ArchivematicaSSHAbility`` class, which encodes the
ability of an Archivematica user to use SSH and scp to interact with
Archivematica.
"""

import logging
import os
import shlex
import string
import subprocess

import pexpect

from . import utils
from . import base


logger = logging.getLogger('ArchivematicaUser SSH')


class ArchivematicaSSHAbility(base.Base):
    """Archivematica SSH Ability: the ability of an Archivematica user to use
    SSH and scp to interact with Archivematica.
    """

    def scp_server_file_to_local(self, server_file_path):
        """Use scp to copy a file from the server to our local tmp directory."""
        if not self.ssh_accessible:
            logger.info('You do not have SSH access to the Archivematica'
                        ' server')
            return None
        filename = os.path.basename(server_file_path)
        local_path = os.path.join(self.tmp_path, filename)
        AM_IP = ''.join([x for x in self.am_url if x in string.digits + '.'])
        if self.server_user and self.ssh_identity_file:
            cmd = ('scp'
                   ' -o StrictHostKeyChecking=no'
                   ' -i {}'
                   ' {}@{}:{} {}'.format(
                       self.ssh_identity_file, self.server_user, AM_IP,
                       server_file_path, local_path))
            subprocess.check_output(shlex.split(cmd))
        elif self.server_user and self.server_password:
            cmd = ('scp'
                   ' -o UserKnownHostsFile=/dev/null'
                   ' -o StrictHostKeyChecking=no'
                   ' {}@{}:{} {}'.format(
                       self.server_user, AM_IP, server_file_path, local_path))
            child = pexpect.spawn(cmd)
            if self.ssh_requires_password:
                child.expect('assword:')
                child.sendline(self.server_password)
            child.expect(pexpect.EOF, timeout=20)
        else:
            logger.info('You must provide a server_user and a either a'
                        ' server_password or a ssh_identity_file')
            return None
        if os.path.isfile(local_path):
            return local_path
        logger.info('Failed to scp %s:%s to %s', AM_IP, server_file_path,
                    local_path)
        return False

    def scp_server_dir_to_local(self, server_dir_path):
        """Use scp to copy a directory from the server to our local tmp
        directory.
        """
        if not self.ssh_accessible:
            logger.info('You do not have SSH access to the Archivematica'
                        ' server')
            return None
        if server_dir_path[-1] == '/':
            server_dir_path = server_dir_path[:-1]
        dirname = os.path.basename(server_dir_path)
        local_path = os.path.join(self.tmp_path, dirname)
        AM_IP = ''.join([x for x in self.am_url if x in string.digits + '.'])
        if self.server_user and self.ssh_identity_file:
            cmd = ('scp'
                   ' -r'
                   ' -i {}'
                   ' -o StrictHostKeyChecking=no'
                   ' {}@{}:{} {}'.format(
                       self.ssh_identity_file, self.server_user, AM_IP,
                       server_dir_path, local_path))
            subprocess.check_output(shlex.split(cmd))
        elif self.server_user and self.server_password:
            cmd = ('scp'
                   ' -r'
                   ' -o UserKnownHostsFile=/dev/null'
                   ' -o StrictHostKeyChecking=no'
                   ' {}@{}:{} {}'.format(
                       self.server_user, AM_IP, server_dir_path, local_path))
            logger.info('Command for scp-ing a remote directory to local:\n%s',
                        cmd)
            child = pexpect.spawn(cmd)
            if self.ssh_requires_password:
                child.expect('assword:')
                child.sendline(self.server_password)
            child.expect(pexpect.EOF, timeout=20)
        else:
            logger.info('You must provide a server_user and a either a'
                        ' server_password or a ssh_identity_file')
            return None
        if os.path.isdir(local_path):
            return local_path
        logger.info('Failed to scp %s:%s to %s', AM_IP, server_dir_path,
                    local_path)
        return False

    def assert_elasticsearch_not_installed(self):
        """Assert that Elasticsearch is not installed by SSHing to the server
        and expecting to find no file at /etc/init.d/elasticsearch.
        """
        if not self.ssh_accessible:
            logger.info('You do not have SSH access to the Archivematica'
                        ' server')
            return None
        AM_IP = ''.join([x for x in self.am_url if x in string.digits + '.'])
        if self.server_user and self.ssh_identity_file:
            cmd = ('ssh'
                   ' -i {}'
                   ' -o StrictHostKeyChecking=no'
                   ' {}@{}'
                   ' ls /etc/init.d/elasticsearch'.format(
                       self.ssh_identity_file,
                       self.server_user, AM_IP))
            logger.info(
                'Command for checking if Elasticsearch is installed: %s', cmd)
            try:
                out = subprocess.check_output(
                    shlex.split(cmd), stderr=subprocess.STDOUT).decode('utf8')
            except subprocess.CalledProcessError as exc:
                out = exc.output.decode('utf8')
        elif self.server_user and self.server_password:
            cmd = ('ssh'
                   ' -o UserKnownHostsFile=/dev/null'
                   ' -o StrictHostKeyChecking=no'
                   ' {}@{}'
                   ' ls /etc/init.d/elasticsearch'.format(
                       self.server_user, AM_IP))
            logger.info(
                'Command for checking if Elasticsearch is installed: %s', cmd)
            child = pexpect.spawn(cmd)
            if self.ssh_requires_password:
                child.expect('assword:')
                child.sendline(self.server_password)
            child.expect(pexpect.EOF, timeout=20)
            out = child.before.decode('utf8')
        else:
            logger.info('You must provide a server_user and a either a'
                        ' server_password or a ssh_identity_file')
            return None
        needle = 'No such file or directory'
        assert needle in out, (
            'We expected "{}" to be in "{}".'.format(needle, out))
