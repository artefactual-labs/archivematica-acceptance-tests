"""Base class for ArchivematicaUser and other related classes."""
# pylint: disable=too-many-instance-attributes

import os
import re
import shutil

try:
    from urllib import parse
except ImportError:  # above is available in py3+, below is py2.7
    import urlparse as parse

from . import constants as c
from . import urls
from . import utils


class ArchivematicaUserError(Exception):
    pass


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Base:
    """Base class for Archivematica user- and ability-type classes. Should only
    hold common functionality for configuring state.
    """

    expected_args = (
        ("am_username", c.DEFAULT_AM_USERNAME),
        ("am_password", c.DEFAULT_AM_PASSWORD),
        ("am_url", c.DEFAULT_AM_URL),
        ("am_version", c.DEFAULT_AM_VERSION),
        ("am_api_key", c.DEFAULT_AM_API_KEY),
        ("ss_username", c.DEFAULT_SS_USERNAME),
        ("ss_password", c.DEFAULT_SS_PASSWORD),
        ("ss_url", c.DEFAULT_SS_URL),
        ("ss_api_key", c.DEFAULT_SS_API_KEY),
        ("driver_name", c.DEFAULT_DRIVER_NAME),
        ("ssh_accessible", None),
        ("ssh_requires_password", None),
        ("server_user", None),
        ("server_password", None),
        ("nihilistic_wait", c.NIHILISTIC_WAIT),
        ("apathetic_wait", c.APATHETIC_WAIT),
        ("pessimistic_wait", c.PESSIMISTIC_WAIT),
        ("medium_wait", c.MEDIUM_WAIT),
        ("optimistic_wait", c.OPTIMISTIC_WAIT),
        ("quick_wait", c.QUICK_WAIT),
        ("micro_wait", c.MICRO_WAIT),
        (
            "max_click_transfer_directory_attempts",
            c.MAX_CLICK_TRANSFER_DIRECTORY_ATTEMPTS,
        ),
        ("max_click_aip_directory_attempts", c.MAX_CLICK_AIP_DIRECTORY_ATTEMPTS),
        (
            "max_navigate_aip_archival_storage_attempts",
            c.MAX_NAVIGATE_AIP_ARCHIVAL_STORAGE_ATTEMPTS,
        ),
        ("max_download_aip_attempts", c.MAX_DOWNLOAD_AIP_ATTEMPTS),
        ("max_check_aip_stored_attempts", c.MAX_CHECK_AIP_STORED_ATTEMPTS),
        ("max_check_mets_loaded_attempts", c.MAX_CHECK_METS_LOADED_ATTEMPTS),
        (
            "max_search_aip_archival_storage_attempts",
            c.MAX_SEARCH_AIP_ARCHIVAL_STORAGE_ATTEMPTS,
        ),
        ("max_search_dip_backlog_attempts", c.MAX_SEARCH_DIP_BACKLOG_ATTEMPTS),
        (
            "max_check_transfer_appeared_attempts",
            c.MAX_CHECK_TRANSFER_APPEARED_ATTEMPTS,
        ),
        ("max_check_for_ms_group_attempts", c.MAX_CHECK_FOR_MS_GROUP_ATTEMPTS),
    )

    url_stdports_re = re.compile(r":(?:80|443)/?$")

    def set_url_getters(self):
        """Create functions as attributes on this instance which return needed
        URLs, given the function names and format templates defined in the urls
        module. E.g., this creates pseudo-methods like
        ``self.get_ss_login_url()``.
        """
        for base_url, url_spec in (
            (self.am_url, urls.AM_URLS),
            (self.ss_url, urls.SS_URLS),
        ):
            for getter_name, template in url_spec:

                def getter(*args, t=template, b=base_url):
                    # Remove standard port suffix from netloc.
                    b = re.sub(self.url_stdports_re, "/", b)
                    return t.format(*(b,) + args)

                setattr(self, getter_name, getter)

    kwarg2attr_filter = {"ss_api_key": "_ss_api_key"}

    def __init__(self, **kwargs):
        self.here = ROOT
        self._ss_api_key = None  # Make pylint happy.
        for kwarg, default in self.expected_args:
            setattr(
                self,
                self.kwarg2attr_filter.get(kwarg, kwarg),
                kwargs.get(kwarg, default),
            )
        self.vn = self.am_version
        expected_kwargs = [x[0] for x in self.expected_args]
        for k, v in kwargs.items():
            if k not in expected_kwargs:
                setattr(self, k, v)
        self.set_url_getters()
        self.metadata_attrs = c.METADATA_ATTRS
        self.dummy_val = c.DUMMY_VAL
        self.cwd = None
        self._tmp_path = None
        self._permanent_path = None

    @staticmethod
    def unique_name(name):
        return "{}_{}".format(name, utils.unixtimestamp())

    @property
    def permanent_path(self):
        if not self._permanent_path:
            self._permanent_path = os.path.join(ROOT, c.PERM_DIR_NAME)
            if not os.path.isdir(self._permanent_path):
                os.makedirs(self._permanent_path)
        return self._permanent_path

    @property
    def tmp_path(self):
        if not self._tmp_path:
            self._tmp_path = os.path.join(ROOT, c.TMP_DIR_NAME)
            if not os.path.isdir(self._tmp_path):
                os.makedirs(self._tmp_path)
        return self._tmp_path

    def clear_tmp_dir(self):
        for thing in os.listdir(self.tmp_path):
            thing_path = os.path.join(self.tmp_path, thing)
            if os.path.isfile(thing_path):
                os.unlink(thing_path)
            elif os.path.isdir(thing_path):
                shutil.rmtree(thing_path)

    @property
    def am_hostname(self):
        return parse.urlparse(self.am_url).hostname
