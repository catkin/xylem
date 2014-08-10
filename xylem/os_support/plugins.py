# Copyright 2014 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing builtin OS plugins."""

from __future__ import unicode_literals

from six.moves import zip

from xylem.os_support import OSBase
from xylem.os_support import UnsupportedOSVersionError

from .os_detect import OsNotDetected
from .os_detect import OsDetect
from .os_detect import OS_DEBIAN
from .os_detect import OS_OSX
from .os_detect import OS_UBUNTU

# TODO: refactor the relevant detection code from `os_detect` to be
# directly contained in the os plugins


class _OSDetecorBase(OSBase):

    """OS plugin base class for builtin plugins.

    This is an internal base class used for the plugins shipped with
    xylem, which use the :mod:`os_detect` module. In general, external
    plugins would want to derive from :class:`OS` or :class:`OSBase`
    directly.

    Derived classes should fill in the following member variables:

    :ivar list(str) names: list of names
    :ivar detect: Detector object supporting ``is_os()``,
        ``get_version()`` and ``get_codename()``
    :ivar bool use_codename: boolean to decide if numbered version or
        codename should be used
    :ivar dict installer_priorities: dict of installer_name => priority
    :ivar str default_installer_name: name of the desired default
        installer
    """

    def __init__(self):
        self._names = []
        self._version_mappings = []
        self._known_versions = []
        self._detector = None
        self._use_codename = False
        self._core_installers = []
        self._default_installer = None

    @property
    def all_names(self):
        return self._names

    def get_version(self):
        if self._detector:
            try:
                if self._use_codename:
                    return self._detector.get_codename()
                else:
                    return self._detector.get_version()
            except OsNotDetected:
                raise UnsupportedOSVersionError(
                    "version detection for '{}' cannot be run on this OS".
                    format(self.name))
        else:
            raise UnsupportedOSVersionError("os plugin '{}' has no detector".
                                            format(self.name))

    def get_all_tuples(self, version):
        tuples = []
        for name, mapping in zip(self.all_names, self._version_mappings):
            tuples.append((name, version))
            if mapping is None or version is None:
                version = None
            else:
                version = mapping.get(version, None)
        return tuples

    def get_core_installers(self, version, options):
        return self._core_installers

    @property
    def default_installer(self):
        return self._default_installer

    @property
    def known_versions(self):
        return self._versions

    def is_os(self):
        if self._detector:
            return self._detector.is_os()
        else:
            return False


class Debian(_OSDetecorBase):

    def __init__(self):
        super(Debian, self).__init__()
        self._names = [OS_DEBIAN]
        self._version_mappings = [None]
        self._versions = ["etch",
                          "lenny",
                          "squeeze",
                          "wheezy",
                          "jessie"]
        self._detector = OsDetect().get_detector(OS_DEBIAN)
        self._use_codename = True
        self._core_installers = ["apt"]
        self._default_installer = "apt"


debian_definition = dict(
    plugin_name='debian',
    description="""OS plugin for Debian.""",
    os=Debian
)


class Ubuntu(Debian):

    def __init__(self):
        super(Ubuntu, self).__init__()
        self._names.insert(0, OS_UBUNTU)
        self._version_mappings.insert(0, None)
        self._versions = ["lucid",
                          "maverick",
                          "natty",
                          "oneiric",
                          "precise",
                          "quantal",
                          "raring",
                          "saucy",
                          "trusty",
                          "utopic"]
        self.detect = OsDetect().get_detector(OS_UBUNTU)


ubuntu_definition = dict(
    plugin_name='ubuntu',
    description="""OS plugin for Ubuntu.""",
    os=Ubuntu
)


class OSX(_OSDetecorBase):

    def __init__(self):
        super(OSX, self).__init__()
        self._names = [OS_OSX]
        self._version_mappings = [None]
        self._versions = ["tiger",
                          "leopard",
                          "snow",
                          "lion",
                          "mountain lion",
                          "mavericks",
                          "yosemite"]
        self._detector = OsDetect().get_detector(OS_OSX)
        self._use_codename = True
        self._core_installers = ["homebrew", "pip", "gem"]
        self._default_installer = "homebrew"


osx_definition = dict(
    plugin_name='osx',
    description="""OS plugin for OS X.""",
    os=OSX
)
