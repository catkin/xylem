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

import pkg_resources

from six.moves import map

from ..os_support import OSSupport
from ..exception import InvalidPluginError
from ..log_utils import info, warning, is_verbose
from ..text_utils import text_type
from ..config import get_config


INSTALLER_GROUP = "xylem.installers"


# TODO: split out verify installer plugin function


# TODO: fix docstrings


def load_installer_plugin(entry_point):
    """Load Installer plugin from entry point.

    :param entry_point: entry point object from `pkg_resources`
    """
    obj = entry_point.load()
    if not (isinstance(obj, dict) and
            isinstance(obj.get('plugin_name'), text_type) and
            isinstance(obj.get('description'), text_type) and
            issubclass(obj.get('installer'), Installer)):   # TODO: this or
                                                            # duck type
        raise InvalidPluginError(
            "Entry point '{0}' does not describe valid Installer "
            "plugin.  Installer plugins need to be dictionaries with "
            "`plugin_name`, `description` and `installer` keys.  "
            "`installer` needs to refer to a class derived from "
            "`installers.Installer`".format(entry_point.name))
    return obj


def get_installer_plugin_list():
    """Return list of Installer plugin objects unique by name.

    Load the Installer plugin descriptions from entry points,
    instantiating objects and ignoring duplicates (by
    Installer.get_name(), not entry point name).

    :return: list of the loaded plugin objects
    :raises InvalidPluginError: if one of the loaded plugins is invalid
    """
    plugin_list = []
    name_set = set()
    for entry_point in pkg_resources.iter_entry_points(group=INSTALLER_GROUP):
        description = load_installer_plugin(entry_point)
        installer_class = description["installer"]
        name = installer_class.get_name()
        if name in name_set:
            warning("Ignoring duplicate installer plugin '{0}' from entry "
                    "point '{1}' with name '{2}'".format(
                        description['plugin_name'], entry_point.name, name))
        else:
            name_set.add(name)
            plugin_list.append(installer_class())
    return plugin_list


# TODO: can we allow OSX to change the default resolutions based on
# whether homebrew is installed or not? Now the resolution does depend
# on the system state...

class InstallerContext(object):

    """:class:`InstallerContext` manages the context of execution for xylem.

    It combines OS plugins, installer plugins and user settings to
    manage the current OS, installers to be used including their
    priorities.
    """

    def __init__(self, config=None, setup_installers=True):

        if config is None:
            config = get_config()

        self.os_support = OSSupport()
        if config.os_override:
            self.set_os_override(config.os_override)
        else:
            self.os_support.detect_os()
            if is_verbose():
                info("detected OS [%s]" % self.get_os_string())

        self.installer_plugins = get_installer_plugin_list()

        self.installers = []
        self.installer_priorities = {}

        if setup_installers:
            self.setup_installers()

    def set_os_override(self, os_tuple):
        """Override the OS detector with *os_name* and *os_version*.

        See :meth:`InstallerContext.detect_os`.

        :param (str,str) os_name: OS (name,version) tuple to use
        :raises UnsupportedOsError: if os override was invalid
        """
        if is_verbose():
            info("overriding OS to [%s:%s]" % os_tuple)
        self.os_support.override_os(os_tuple)
        if is_verbose() and os_tuple[1] is None:
            info("detected OS version [%s]" % self.get_os_string())

    def get_os_tuple(self):
        """Get the OS (name,version) tuple.

        Return the OS name/version tuple to use for resolution and
        installation.  This will be the detected OS name/version unless
        :meth:`InstallerContext.set_os_override()` has been called.

        :return: (os_name, os_version)
        :rtype: (str,str)
        :raises UnsupportedOsError: if OS was not detected correctly
        """
        return self.os_support.get_current_os().get_tuple()

    def get_os_string(self):
        """Get the OS name and version as 'name:version' string.

        See :meth:`get_os_tuple`

        :rtype: str
        :raises UnsupportedOsError: if OS was not detected correctly
        """
        return "%s:%s" % self.get_os_tuple()

    def get_default_installer_name(self):
        """Get name of default installer for current os.

        :meth:`setup_installers` needs to be called beforehand.
        """
        return self.os_support.get_current_os().get_default_installer_name()

    def get_installer_names(self):
        """Get all configured installers for current os.

        :meth:`setup_installers` needs to be called beforehand.
        """
        return map(lambda i: i.get_name(), self.installers)

    def get_installer(self, name):
        """Get installer object by name."""
        for inst in self.installers:
            if inst.get_name() == name:
                return inst
        return None

    def get_installer_priority(self, name):
        """Get configured priority for specific installer and current os.

        :meth:`setup_installers` needs to be called beforehand.
        """
        return self.installer_priorities.get(name, None)

    def setup_installers(self):
        """For current os, setup configured installers.

        Installers are set up with their priorities for the current os
        and based on user config, os plugins and installer plugins.
        """
        os = self.os_support.get_current_os()
        os_name, os_version = os.get_tuple()

        self.installers = []
        self.installer_priorities = {}

        # Go through all installers and check if they should be used for
        # the current os. Precedence for which priority is used is the
        # following: user config > os plugin > installer plugin
        for inst in self.installer_plugins:
            inst_name = inst.get_name()
            # TODO: check here what the user config has to say about
            # installer priority, overriding the values from OS or
            # installer plugin
            priority = None  # TODO: read user config here
            priority = priority or os.get_installer_priority(inst_name)
            priority = priority or inst.get_priority_for_os(os_name,
                                                            os_version)
            if priority is not None:
                self.installers.append(inst)
                self.installer_priorities[inst_name] = priority

        # TODO: this can happen when installer plugin is not installed.
        # We can still resolve, so let this happen maybe?
#        if self.default_installer_name not in self.get_installer_names():
            # TODO: Maybe use custom exception class?
#            raise RuntimeError(
#                "Default installer '{0}' does not appear in configured "
#                "installers '{1}'".format(
#                    self.default_installer_name,
#                    self.get_installer_names()))

        # TODO: check which of the installers defined by OS (besides
        # default) has not been registered and possibly issue warning

        # TODO: allow to completely disable installers for platform in
        # config


# TODO: is 'resolved' the same as 'installer rule', or can it be a
# processed 'installer rule' also?

class Installer(object):

    """Installer class that custom installer plugins derive from.

    The :class:`Installer` API is designed around opaque *resolved*
    parameters. These parameters can be any type of sequence object,
    but they must obey set arithmetic.  They should also implement
    ``__str__()`` methods so they can be pretty printed.
    """

    @staticmethod
    def get_name():
        """Get the name of the installer this class implements.

        This is the name that is referenced in the rules files, user
        configuration or OS plugins. There may only be one installer for
        a any given name at runtime, i.e. plugins defining installers
        with existing names might be ignored.

        :return str: installer name
        """
        raise NotImplementedError('subclasses must implement')

    def is_installed(self, resolved_item):
        """Check if single opaque installation item is installed.

        :param resolved_item: single opaque resolved installation item
        :returns: ``True`` if all of the *resolved* items are installed
            on the local system
        """
        raise NotImplementedError('subclasses must implement')
        # TODO: generalize this as 'prerequisites' abstraction

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        """Get command line invocations to install list of items.

        :param resolved: [resolution].  List of opaque resolved
            installation items
        :param interactive: If `False`, disable interactive prompts,
            e.g. pass through ``-y`` or equivalent to package manager.
        :param reinstall: If ``True``, install everything even if
            already installed
        :return: List of commands, each command being a list of strings.
        :rtype: ``[[str]]``
        """
        raise NotImplementedError('subclasses must implement')

    # get_depends should not live here. The way to specify options
    # should be standardized and the dependency extraction should be
    # done beforehand.
    def get_depends(self, rule_args):
        """Get list list of dependencies on other xylem keys.

        :param dict rule_args: argument dictionary to the xylem rule for
            this package manager
        :return: List of dependencies on other xylem keys. Only
            necessary if the package manager doesn't handle
            dependencies.
        :rtype: list of str
        """
        return []

    def resolve(self, rule_args):
        """Return list of resolutions from rules dictionary entry.

        :param dict rule_args: argument dictionary to the xylem rule for
            this package manager
        :returns: [resolution].  Resolved objects should be printable to
            a user, but are otherwise opaque.
        """
        raise NotImplementedError('subclasses must implement')

    def get_priority_for_os(self, os_name, os_version):
        """Get the priority of this installer according to installer plugin.

        Given an OS name/version tuple, the installer can declare that
        it should be used on that OS with the returned priority. If the
        installer does not want to declare itself for this OS, None is
        returned.

        :rtype: number or None
        """
        return None
