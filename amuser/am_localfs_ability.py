"""Archivematica LocalFS Ability

This module contains the ``ArchivematicaLocalFSAbility`` class, which encodes
the ability to transfer files when they're locally available.
"""

import logging

from . import base


logger = logging.getLogger('amuser.localfs')


class ArchivematicaLocalFSAbility(base.Base):
    """Archivematica LocalFS Ability: the ability of an Archivematica user to
    access files in the application environment when they're local.
    """

    @staticmethod
    def read_server_file(server_file_path):
        """Return the local path to the file/dir requested.

        If needed in the future, it should be possible to have a map of
        transformations provided by the user running ``behave`` when the
        assets are available in different lcoations, e.g.:

           >>> for prefix, replacement in self.local_dirs_mapping:
           >>>    if server_file_path.startswith(prefix):
           >>>        return os.path.join(
           >>>            replacement, server_file_path[
           >>>               len(prefix):].lstrip("/"))
           >>> return server_file_path
        """
        return server_file_path
