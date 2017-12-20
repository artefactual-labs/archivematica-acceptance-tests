"""Archivematica User.

This module contains the ``ArchivematicaUser`` class, which represents a user
of Archivematica.
"""

import os
import shlex
import subprocess

from . import am_api_ability
from . import am_browser_ability
from . import am_cmd_line_ability
from . import am_mets_ability
from . import base
from . import constants as c
from . import utils


LOGGER = utils.LOGGER


class ArchivematicaUser(base.Base):
    """Represents an Archivematica user. An Archivematica user can have
    different abilities, or ways of interacting with Archivematica. Using
    composition, this Archivematica has the following types of abilities:

        - browser abilities (via Selenium) accessed through ``self.browser``.
        - API abilities (via Requests) accessed through ``self.api``.
        - SSH abilities (via ssh, scp) accessed through ``self.ssh``.
        - METS (XML) abilities, accessed through ``self.mets``.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.browser = am_browser_ability.ArchivematicaBrowserAbility(**kwargs)
        self.ssh = am_cmd_line_ability.ArchivematicaCommandLineAbility(
            **kwargs)
        self.api = am_api_ability.ArchivematicaAPIAbility(**kwargs)
        self.mets = am_mets_ability.ArchivematicaMETSAbility(**kwargs)

    @staticmethod
    def decompress_package(package_path):
        if os.path.isdir(package_path):
            return package_path
        fname, extension = os.path.splitext(package_path)
        if extension == '.gpg':
            fname, extension = os.path.splitext(fname)
        if extension != '.7z':
            LOGGER.info('decompress_package; extension %s of fname %s is NOT'
                        ' .7z', extension, fname)
            return False
        try:
            subprocess.check_output(['7z', '-h'])
        except FileNotFoundError:
            LOGGER.info('7z is not installed; aborting decompression attempt')
            return False
        try:
            subprocess.check_output(
                ['7z', 'x', package_path, '-o{}'.format(c.TMP_DIR_NAME)])
        except subprocess.CalledProcessError:
            LOGGER.info('7z extraction failed. File %s is not a .7z file or it'
                        ' is encrypted', package_path)
            return None
        return fname

    def decompress_aip(self, aip_path):
        aip_parent_dir_path = os.path.dirname(aip_path)
        try:
            devnull = getattr(subprocess, 'DEVNULL')
        except AttributeError:
            devnull = open(os.devnull, 'wb')
        cmd = shlex.split('7z l {}'.format(aip_path))
        output=subprocess.check_output(cmd).decode('utf8')
        aip_dir_name = output.splitlines()[-3].split()[-1]
        aip_dir_path = os.path.join(aip_parent_dir_path, aip_dir_name)
        p = subprocess.Popen(
            shlex.split('7z x {} -aoa'.format(aip_path)),
            cwd=self.tmp_path,
            stdout=devnull,
            stderr=subprocess.STDOUT)
        p.wait()
        assert p.returncode == 0
        assert os.path.isdir(aip_dir_path), (
            'Failed to create dir {} from compressed AIP at {}'.format(
                aip_dir_path, aip_path))
        return aip_dir_path
