"""Archivematica Command Line Ability

This module contains the ``ArchivematicaCommandLineAbility`` class, which
encodes the ability of an Archivematica user to use a the command line and
Python modules like os, etc. to interact with
Archivematica.
"""

import os
import string

import pexpect

from . import utils
from . import base


LOGGER = utils.LOGGER


class ArchivematicaCommandLineAbility(base.Base):
    """Archivematica Command Line Ability: the ability of an Archivematica user
    to use SSH, scp, and Python os, etc. to interact with
    Archivematica.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def scp_server_file_to_local(self, server_file_path):
        """Use scp to copy a file from the server to our local tmp directory."""
        if self.server_user and self.server_password and self.ssh_accessible:
            filename = os.path.basename(server_file_path)
            local_path = os.path.join(self.tmp_path, filename)
            AM_IP = ''.join([x for x in self.am_url if x in string.digits + '.'])
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
            if os.path.isfile(local_path):
                return local_path
            LOGGER.info('Failed to scp %s:%s to %s', AM_IP, server_file_path,
                        local_path)
            return False
        else:
            LOGGER.info('You do not have SSH access to the Archivematica'
                        ' server')
            return None

    def scp_server_dir_to_local(self, server_dir_path):
        """Use scp to copy a directory from the server to our local tmp
        directory.
        """
        if self.server_user and self.server_password and self.ssh_accessible:
            if server_dir_path[-1] == '/':
                server_dir_path = server_dir_path[:-1]
            dirname = os.path.basename(server_dir_path)
            local_path = os.path.join(self.tmp_path, dirname)
            AM_IP = ''.join([x for x in self.am_url if x in string.digits + '.'])
            cmd = ('scp'
                   ' -r'
                   ' -o UserKnownHostsFile=/dev/null'
                   ' -o StrictHostKeyChecking=no'
                   ' {}@{}:{} {}'.format(
                       self.server_user, AM_IP, server_dir_path, local_path))
            LOGGER.info('Command for scp-ing a remote directory to local:\n%s',
                        cmd)
            child = pexpect.spawn(cmd)
            if self.ssh_requires_password:
                child.expect('assword:')
                child.sendline(self.server_password)
            child.expect(pexpect.EOF, timeout=20)
            if os.path.isdir(local_path):
                return local_path
            LOGGER.info('Failed to scp %s:%s to %s', AM_IP, server_dir_path,
                        local_path)
            return False
        else:
            LOGGER.info('You do not have SSH access to the Archivematica'
                        ' server')
            return None
