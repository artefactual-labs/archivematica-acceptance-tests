"""Archivematica User.

This module contains the ``ArchivematicaUser`` class, which represents a user
of Archivematica.
"""

import logging
import os
import shlex
import subprocess

from . import am_api_ability
from . import am_browser_ability
from . import am_docker_ability
from . import am_localfs_ability
from . import am_mets_ability
from . import am_ssh_ability
from . import base
from . import constants as c

logger = logging.getLogger("amuser")


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
        self.ssh = am_ssh_ability.ArchivematicaSSHAbility(**kwargs)
        self.docker = am_docker_ability.ArchivematicaDockerAbility(**kwargs)
        self.localfs = am_localfs_ability.ArchivematicaLocalFSAbility(**kwargs)
        self.api = am_api_ability.ArchivematicaAPIAbility(**kwargs)
        self.mets = am_mets_ability.ArchivematicaMETSAbility(**kwargs)

    @staticmethod
    def decompress_package(package_path):
        if os.path.isdir(package_path):
            return package_path
        fname, extension = os.path.splitext(package_path)
        if extension == ".gpg":
            fname, extension = os.path.splitext(fname)
        if extension != ".7z":
            logger.info(
                "decompress_package; extension %s of fname %s is NOT .7z",
                extension,
                fname,
            )
            return False
        try:
            subprocess.check_output(["7z", "-h"])
        except FileNotFoundError:
            logger.info("7z is not installed; aborting decompression attempt")
            return False
        try:
            subprocess.check_output(["7z", "x", package_path, f"-o{c.TMP_DIR_NAME}"])
        except subprocess.CalledProcessError:
            logger.info(
                "7z extraction failed. File %s is not a .7z file or it is encrypted",
                package_path,
            )
            return None
        return fname

    def decompress_aip(self, aip_path, cwd=None):
        cwd = cwd or self.tmp_path
        aip_parent_dir_path = os.path.dirname(aip_path)
        try:
            devnull = subprocess.DEVNULL
        except AttributeError:
            devnull = open(os.devnull, "wb")
        aip_dir_name = get_aip_dir_name_from_archive(aip_path)
        aip_dir_path = os.path.join(aip_parent_dir_path, aip_dir_name)
        cmd = shlex.split(f"7z x {aip_path} -aoa")
        logger.info("Decompress AIP command: %s", cmd)
        logger.info("Decompress AIP cwd: %s", cwd)
        p = subprocess.Popen(cmd, cwd=cwd, stdout=devnull, stderr=subprocess.STDOUT)
        p.wait()
        assert p.returncode == 0
        assert os.path.isdir(
            aip_dir_path
        ), f"Failed to create dir {aip_dir_path} from compressed AIP at {aip_path}"
        return aip_dir_path


def get_aip_dir_name_from_archive(aip_path):
    cmd = shlex.split(f"7z l {aip_path}")
    output = subprocess.check_output(cmd).decode("utf8")
    in_table = False
    paths = []
    for line in output.splitlines():
        if line.startswith("--------"):
            in_table = not in_table
            continue
        if in_table:
            paths.append(line.split()[-1])
    paths.sort(key=len)
    return paths[0]
