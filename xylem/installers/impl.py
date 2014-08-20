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

from xylem.os_support import OSSupport
from xylem.log_utils import info_v
from xylem.log_utils import error
from xylem.config import get_config
from xylem.plugin_utils import PluginBase
from xylem.plugin_utils import load_plugins
from xylem.exception import XylemError
from xylem.text_utils import type_name

# TODO: fix docstrings


INSTALLER_GROUP = "xylem.installers"


def load_installer_plugins(disabled=[]):
    """Return list of installer plugin objects unique by name.

    See :func:`load_plugins`
    """
    return load_plugins("installer", Installer, INSTALLER_GROUP, disabled)


class InstallerError(XylemError):

    """Base class for all installer related exceptions."""


class InvalidRuleError(InstallerError):

    """Invalid rule input to installer plugin."""


class InstallerPrerequisiteError(InstallerError):

    """Exception for unfulfilled installer prerequisites."""


class Installer(PluginBase):

    """Installer class that custom installer plugins derive from.

    The :class:`Installer` API is designed around ordered lists of
    opaque ``resolution`` parameters with argument name ``resolutions``.
    These parameters can be any type of object, but they must be
    printable to the user.  A ``resolution`` typically corresponds to a
    single package, possibly with additional options or meta data for
    how they can/should be installed.

    One xylem key may resolve to multiple resolutions.
    """

    @abc.abstractproperty
    def name():
        """Name of the installer this class implements.

        This is the name that is referenced in the rules files, user
        configuration or OS plugins. There may only be one installer for
        any given name at runtime, i.e. plugins defining installers
        with existing names might be ignored.

        :rtype: `str`
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def options(self):
        """Get installer options as `xylem.config_utils.ConfigDict`."""
        raise NotImplementedError()

    @options.setter
    def options(self, value):
        """Set installer options as `dict`."""
        raise NotImplementedError()

    @abc.abstractmethod
    def use_as_additional_installer(self, os_tuple):
        """Determines if this should be used as an additional installer.

        Given an OS name/version tuple, the installer can declare that
        it should be used on that OS as an additional installer.
        Additional installers are secondary to the ordered list of core
        installers defined by OS plugins.

        :rtype: `bool`
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_depends(self, installer_rule):
        """Get list list of dependencies on other xylem keys.

        :param dict installer_rule: installer rule from the rules
            dictionary for this installer
        :return: List of dependencies on other xylem keys. Only
            necessary if the package manager doesn't handle
            dependencies.
        :rtype: `list` of `str`
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve(self, installer_rule):
        """Return list of resolutions from installer dict entry.

        :param dict installer_rule: installer rule from the rules
            dictionary for this installer
        :returns: ``resolutions`` -- list of resolution items
        :raises InvalidRuleError: if installer_rule cannot does not have
            a valid structure according to this installer
        """
        raise NotImplementedError()

    # TODO: Think about correct abstraction for `is_installed` and
    # `filter_ininstalled`. We need a way to pass info down, e.g. about
    # why packages are considered 'uninstalled' (package not found,
    # homebrew not linked or wrong options)

    @abc.abstractmethod
    def is_installed(self, resolutions):
        """Check if ``resolutions`` are installed.

        :param resolutions: list of resolution items or single item
        :returns bool: ``True`` if all items are installed
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def filter_uninstalled(self, resolutions):
        """Return list of only uninstalled items given list of resolutions.

        :param resolutions: list of resolution items
        :returns: list of resolutions which are not currently installed,
            in the same order as in the input list
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_install_commands(self,
                             resolutions,
                             interactive=True,
                             reinstall=False):
        """Get command line invocations to install list of resolutions.

        :param resolutions: list of resolution items
        :param interactive: if `False`, disable interactive prompts,
            e.g. pass through ``-y`` or equivalent to package manager
        :param reinstall: if ``True``, issue commands to reinstall or
            uninstall/install the given resolution items
        :return: list of commands, each command being a list of strings
        :rtype: ``[[str]]``
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def check_general_prerequisites(self,
                                    os_tuple,
                                    fix_unsatisfied=False,
                                    interactive=True):
        """Check general prerequisites for using this installer.

        These are independent from any concrete list of resolutions to
        be installed. For example, an error might be raised if the
        package manager is installed, and a warning if it has not been
        recently updated.

        The installer may try to fix unsatisfied prerequisites, raise
        errors as `InstallerPrerequisiteError` exceptions, or print
        warnings to console.

        :param fix_unsatisfied: if ``True``, attempt to fix unsatisfied
            prerequisites instead of just informing the user; if
            ``False``, do not attempt; if string ``"simulate"`` is
            passed, behaves like ``True``, but does not actually execute
            the fixes
        :type fix_unsatisfied: `bool` or string ``"simulate"``
        :param bool interactive: if ``True``, any attempts to fix
            unsatisfied prerequisites will require confirmation of the
            user
        :param bool warning_as_error: if ``True``, all warnings are
            converted to errors
        :raises InstallerPrerequisiteError: if the check was not
            successful
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def check_install_prerequisites(self,
                                    resolutions,
                                    os_tuple,
                                    fix_unsatisfied=False,
                                    interactive=True):
        """Check prerequisites for installing a list of resolutions.

        For example, this might include checking if the according apt
        repositories are activated.

        On top if raising errors as `InstallerPrerequisiteError`
        exceptions, this may also print warnings.

        :param resolutions: list of resolution items
        :param bool fix_unsatisfied: if ``True``, attempt to fix
            unsatisfied prerequisites instead of just informing the user
        :param bool interactive: if ``True``, any attempts to fix
            unsatisfied prerequisites will require confirmation of the
            user
        :param bool warning_as_error: if ``True``, all warnings are
            converted to errors
        :raises InstallerPrerequisiteError: if the check was not
            successful
        """
        raise NotImplementedError()


class InstallerContext(object):

    """Manages the context of OS and installers for xylem.

    It combines OS plugins, installer plugins and user settings to
    manage the current OS and installers to be used.

    :ivar dict config: config dictionary used; e.g. for os override, os
        options, installer options
    :ivar OSSupport os_support: os support object managing current
        (or override) os; is set by :meth:`setup_os`
    :ivar installer_plugins: list of all known installer objects,
        independent of the current OS
    :type installer_plugins: `list` of `Installer`
    :ivar core_installers: list of the core installer objects for
        the current os; is set by :meth:`setup_installers`
    :type core_installers: `list` of `Installer`
    :ivar additional_installers: list of the additional installer
        objects for the current os; is set by :meth:`setup_installers`
    :type additional_installers: `list` of `Installer`
    """

    def __init__(self, config=None, os_support=None, setup_installers=True):

        if config is None:
            config = get_config()
        self.config = config
        if os_support is None:
            self.setup_os()
        else:
            self.os_support = os_support
        self.installer_plugins = load_installer_plugins(
            self.config.disabled_plugins.installer)
        if setup_installers:
            self.setup_installers()
        else:
            self.core_installers = []
            self.additional_installers = []

    def setup_os(self):
        """Create `OSSupport` and detect or override OS depending on config.

        :raises xylem.os_support.UnsupportedOsError: if OS override was
            invalid and detection failed
        :raises xylem.os_support.UnsupportedOSVersionError: if override
            version is not valid for override OS
        """
        self.os_support = OSSupport(self.config.disabled_plugins.os)
        if self.config.os_override is None:
            self.os_support.detect_os()
            info_v("detected OS [%s]" % self.get_os_string())
        else:
            info_v("overriding OS to [%s:%s]" % self.config.os_override)
            self.os_support.override_os(self.config.os_override)
            if self.config.os_override[1] is None:
                info_v("detected OS version [%s]" % self.get_os_string())
        self.get_os().options = self.config.os_options

    def get_os(self):
        """Get the current OS plugin object.

        :rtype xylem.os_support.OS: the current OS object
        :raises xylem.os_support.UnsupportedOsError: if OS was not
            detected correctly
        """
        return self.os_support.current_os

    def get_os_tuple(self):
        """Get the current OS (name,version) tuple.

        :return: (os_name, os_version)
        :rtype: ``(str,str)``
        :raises xylem.os_support.UnsupportedOsError: if OS was not
            detected correctly
        """
        return self.get_os().get_tuple()

    def get_os_string(self):
        """Get the cuurent OS name and version as ``'name:version'`` string.

        :rtype: `str`
        :raises xylem.os_support.UnsupportedOsError: if OS was not
            detected correctly
        """
        return "%s:%s" % self.get_os_tuple()

    def get_default_installer_name(self):
        """Get name of default installer for current OS.

        :rtype: `str`
        """
        return self.os_support.current_os.default_installer

    @property
    def installers(self):
        """Get list of core and additional installers.

        :meth:`setup_installers` needs to be called beforehand.

        :rtype: `list` of `Installer`
        """
        return self.core_installers + self.additional_installers

    @property
    def installer_names(self):
        """Get list of names for core and additional installers.

        :meth:`setup_installers` needs to be called beforehand.

        :rtype: `list` of `str`
        """
        return [i.name for i in self.installers]

    @property
    def core_installer_names(self):
        """Get list of names for core installers.

        :meth:`setup_installers` needs to be called beforehand.

        :rtype: `list` of `str`
        """
        return [i.name for i in self.core_installers]

    @property
    def additional_installer_names(self):
        """Get list of names for additional installers.

        :meth:`setup_installers` needs to be called beforehand.

        :rtype: `list` of `str`
        """
        return [i.name for i in self.additional_installers]

    @property
    def installer_plugin_names(self):
        """Get list of names for all known installers.

        :rtype: `list` of `str`
        """
        return [i.name for i in self.installer_plugins]

    def lookup_installer(self, name):
        """Get installer object by name.

        :param str name: name of the installer
        :return: if found, installer object, else ``None``
        :rtype: `Installer` or ``None``
        """
        for inst in self.installer_plugins:
            if inst.name == name:
                return inst
        return None

    def setup_installers(self):
        """For current os, setup configured installers.

        Installers are set based on the current os, user config and
        installer plugins.
        """
        os = self.get_os()
        os_tuple = os.get_tuple()
        _, os_version = os_tuple

        self.core_installers = []
        self.additional_installers = []

        #  1. Go through all installers and set options from config
        for inst in self.installer_plugins:
            inst.options = self.config.installer_options.get(inst.name, {})

        #  2. setup core installers from config or OS plugin
        if self.config.core_installers is not None:
            core_installer_names = self.config.core_installers
            info_v("setting up core installers from config: '{}'".
                   format(", ".join(core_installer_names)))
        else:
            core_installer_names = os.get_core_installers(os_version,
                                                          os.options)
            info_v("setting up core installers from os plugin: '{}'".
                   format(", ".join(core_installer_names)))

        for name in core_installer_names:
            inst = self.lookup_installer(name)
            if inst is None:
                error("ignoring core installer '{}'; according plugin was not "
                      "found".format(name))
            else:
                self.core_installers.append(inst)

        #  3. Go through all installers and check if they should be used
        #     as additional installers for the current OS.
        if self.config.use_additional_installers:
            for inst in self.installer_plugins:
                if inst not in self.core_installers and \
                        inst.use_as_additional_installer(os_tuple):
                    self.additional_installers.append(inst)
        info_v("Using additional installers: '{}'".format(
               ", ".join([i.name for i in self.additional_installers])))


def ensure_installer_context(installer_context, config):
    """Helper for processing ``installer_context`` arguments in public API.

    Return installer context. If ``installer_context`` is none, create
    new one using ``config``.

    :param installer_context: `InstallerContext` or `None`
    :param ConfigDict config: config dict to create installer context with
    :rtype: `InstallerContext`
    :raises ValueError: if ``config`` is invalid type
    """
    if installer_context is None:
        return InstallerContext(config=config)
    if isinstance(installer_context, InstallerContext):
        return installer_context
    raise ValueError("invalid installer context of type '{}'".
                     format(type_name(config)))
