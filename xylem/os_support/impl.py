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

from __future__ import unicode_literals

import abc

from xylem.log_utils import warning
from xylem.exception import XylemError
from xylem.exception import type_error_msg
from xylem.plugin_utils import PluginBase
from xylem.plugin_utils import load_plugins


OS_GROUP = 'xylem.os'


def load_os_plugins(disabled=[]):
    """Return list of os plugin objects unique by name.

    See :func:`load_plugins`
    """
    return load_plugins("os", OS, OS_GROUP, disabled)


class UnsupportedOSError(XylemError):

    """Operating system unsupported.

    Detected operating system is not supported or could not be
    identified.
    """


class UnsupportedOSVersionError(XylemError):

    """Version of OS is unsupported.

    Overriding a specific version is not supported. Version-order can
    not be computed for specific version.
    """


class OS(PluginBase):

    """Abstract OS plugin base class.

    The is :meth:`is_os` method detects if the current OS matches the
    platform described by the plugin. When :meth:`is_os` returns
    ``True``, the plugin is able to detect the OS version. Name and
    version of the OS are also known as the OS tuple ``(name,
    version)``.

    To support derivative OSs (like XUbuntu or Mint as Ubuntu
    derivatives), the plugins may furthermore define a list of
    decreasingly specific names, and return a list of OS decreasingly
    specific OS tuples (names and versions, or None for version if the
    derivative OS version cannot be mapped to version of the parent OS).

    OS plugins define an ordered list of core installers (highest
    priority first). These are the installers used primarily to resolve
    keys on this platform. If for a specific key there is no rule for
    any of the core installers, additional installers as defined by
    installer plugins may be considered. OS plugins can furthermore name
    a default installer, which is helpful for brevity in rules files,
    but has no meaning for the priority of installers during rules
    resolution.
    """

    @abc.abstractproperty
    def name(self):
        """Get the most specific name of the described operating system.

        The most specific name is "the" name of this OS.

        :rtype: str
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def all_names(self):
        """Return list of decreasingly specific OS names.

        The first element is equal to :ivar:`name`.

        :rtype: `list` of `str`
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_version(self):
        """Get version of this operating system.

        Runs version detection. Only works if run on the correct OS.

        :raises UnsupportedOSError: if the current OS does not match
            this plugin and thus the version cannot be detected
        :rtype: `str`
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_tuple(self):
        """Get (name,version) tuple.

        Runs version detection. Only works if run on the correct OS.

        :raises UnsupportedOSError: if version detection fails (see
            :meth:`get_version`)
        :rtype: ``(str,str)``
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_tuples(self, version):
        """Get a list of decreasingly specific tuples, given a current version.

        The first elements of the tuples correspond to the output of
        :ivar:`all_names`; versions of any 'parent' OS may also be
        ``None``, indicating that no matching version can be determined
        give the current derivative OS version. The first element of the
        list is equal to  :meth:`get_tuple`.

        This does not run version detection, i.e. it works with an
        override OS version running on a different OS.

        :param str version: version of the derivative (most specific) OS.
        :raises UnsupportedOSError: if version is not known
        :rtype: `list` of ``(str,str)``; version part might be None
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_core_installers(self, version, options):
        """List of core installers given os version and options.

        :rtype: `list` of `str`
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def default_installer(self):
        """Name of default installer if any.

        :rtype: `str` or None
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def known_versions(self):
        """Ordered list of known versions; newest versions last.

        :rtype: `list` of `str`
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def version_less_fn(self):
        """Function implementing an order on version strings (less).

        This is used for example for ``any_version>=foo`` in rules
        files.

        The returned order function raises `UnsupportedOSVersionError`
        when one of the passed versions is not
        :meth:`is_version_acceptable`.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def is_os(self):
        """Return true if the current OS matches the one this object describes.

        :rtype: `bool`
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def set_options(self, options):
        """Set OS options such as active *features*.

        :param dict options: OS options dictionary
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_options(self):
        """Get OS options susch as active *features*.

        :return dict: OS options dictionary
        """
        raise NotImplementedError()


class OSBase(OS):

    """Some sensible default implementations of parts of the `OS` interface.

    This class may be used by OS plugins as a base class instead of
    `OS`.
    """

    @property
    def name(self):
        return self.all_names[0]

    def get_tuple(self):
        return (self.name, self.get_version())

    @property
    def default_installer(self):
        return None

    @property
    def version_less_fn(self):
        return version_order_from_list(self.known_versions)

    def set_options(self, options):
        self._options = options

    def get_options(self):
        return self._options

    # TODO: do handling of `features` here; maybe introduce a
    # ConfigDescription that handles verifying the structure of options
    # (and subclasses can extend the description)
    # TODO: make this more like with Installer (options property)

class OSOverride(OS):

    """Special OS class that acts as a proxy to another OS with fixed version.

    OSOverride takes another OS object and delegates all queries to
    that, except for detection and version, which are fixed by the
    OSOverride.
    """

    def __init__(self, os, version):
        """Setup the `OSOverride` with given os object and version string.

        :param OS os: object of class derived from `OS` that this object
            imitates
        :param str version: version of the imitated OS; if None is
            passed, the version is detected
        :type version: `str` or ``None``
        :raises UnsupportedOSError: if ``os`` is not valid
        :raises UnsupportedOSVersionError: if ``version`` is not a known
            version for ``os``; for ``version is None`` if the version
            cannot be detected
        """
        if not isinstance(os, OS):
            raise UnsupportedOSError(
                type_error_msg("OS", os, what_for="os override"))
        self.os = os
        if version is None:
            self.version = os.get_version()
        else:
            if version not in os.known_versions:
                raise UnsupportedOSVersionError(
                    "Cannot override OS '{}' with unknown version '{}'.".
                    format(os.name, version))
            self.version = version

    @property
    def name(self):
        """Defer to delegate."""
        return self.os.name

    @property
    def all_names(self):
        """Defer to delegate."""
        return self.os.all_names

    def get_version(self):
        """Return the saved version from setup."""
        return self.version

    def get_tuple(self):
        """Return delegate's name and saved version from setup."""
        return (self.name, self.get_version())

    def get_all_tuples(self, version):
        """Defer to delegate."""
        return self.os.get_all_tuples(version)

    def get_core_installers(self, version, options):
        """Defer to delegate."""
        return self.os.get_core_installers(version, options)

    @property
    def default_installer(self):
        """Defer to delegate."""
        return self.os.default_installer

    @property
    def known_versions(self):
        """Defer to delegate."""
        return self.os.known_versions

    @property
    def version_less_fn(self):
        """Defer to delegate."""
        return self.os.version_less_fn

    def is_os(self):
        """Detection for OSOverride is always `True`."""
        return True

    def set_options(self, options):
        """Defer to delegate."""
        return self.os.set_options(options)

    def get_options(self):
        """Defer to delegate."""
        return self.os.get_options()


class OSSupport(object):

    """OSSupport manages the OS plugins and options such as OS override.

    Can detect the current OS from the installed OS plugins or use the
    override option. Moreover manages options such as disabling specific
    plugins.

    In order to set up, either call :meth:`detect_os` or
    :meth:`override_os` and subsequently access it with
    :func:`get_current_os`
    """

    # TODO: Configure to disable specific plugins

    def __init__(self):
        self._os = None
        self._os_plugin_list = get_os_plugin_list()

    def get_current_os(self):
        """Return OS object of current OS.

        Detect current OS if not yet detected or overridden.

        :rtype: `OS`
        :raises UnsupportedOSError: If OS is not set and cannot be
            detected.
        """
        if not self._os:
            self.detect_os()
        return self._os

    def get_os_plugins(self):
        """Return list of is plugin objects."""
        return self._os_plugin_list

    def get_os_plugin_names(self):
        """Return list of known/configured os names."""
        return [x.name for x in self.get_os_plugins()]

    def get_os_plugin(self, name):
        """Return os plugin object for given os name or `None` if not known."""
        for os in self.get_os_plugins():
            if name == os.name:
                return os
        return None

    def get_default_installer_names(self):
        """Return mapping of os name to default installer for all os."""
        return {os.name: os.default_installer
                for os in self.get_os_plugins()}

    def override_os(self, os_tuple):
        """Override current OS to (name,version) tuple.

        A plugin with ``name`` must be installed and ``version`` must be
        valid for that OS.

        :raises UnsupportedOSError: if specified OS name is not known
        :raises UnsupportedOSVersionError: if version is not valid for
            that OS
        """
        if os_tuple:
            name, version = os_tuple
            os = self.get_os_plugin(name)
            if not os:
                raise UnsupportedOSError(
                    "Did not find OS plugin {0} to be used as override.".
                    format(name))
            else:
                self._os = OSOverride(os, version)

    def detect_os(self):
        """Detects and sets the current OS.

        The most specific OS plugin that returns ``True`` for
        :meth:`OS.is_os` is the detected one.

        If multiple os plugins would accept the current OS and they is
        not single most specific OS, a warning is printed to the user.

        :raises UnsupportedOSError: If no OS plugin accepts the current OS
        """
        result = None
        for os in self.get_os_plugins():
            if os.is_os():
                if not result:
                    result = os
                else:
                    if os.name in result.all_names:
                        # ignore this 'parent' os
                        pass
                    elif result.name in os.all_names:
                        # found a more specific derivative os; use that instead
                        result = os
                    else:
                        warning("OS '{}' detected, but '{}' already detected".
                                format(os.name, result.name))
        if not result:
            raise UnsupportedOSError(
                "None of the OS plugins {} detected the current OS.".
                format(self.get_os_plugin_names()))
        self._os = result
