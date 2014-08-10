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
import os
import six

from .impl import Installer
from .impl import InvalidRuleError

from xylem.exception import raise_from

from xylem.log_utils import warning

from xylem.config_utils import ConfigDescription
from xylem.config_utils import ConfigValueError
from xylem.config_utils import Boolean
from xylem.config_utils import List
from xylem.config_utils import String
from xylem.config_utils import config_from_parsed_yaml
from xylem.config_utils import config_from_defaults


class Resolution(dict):

    """Resolution object as a dictionary with attribute access.

    Corresponds to a single package to be installed by a package
    manager. By default only key `package` is assumed. Equality is the
    same as dictionary equality. Set the ``_to_list_keys`` instance
    variable to define how the resolution is printed.

    These objects are hashable, which is used to remove duplicates of a
    list of resolutions. This means that once created by `resolve`, they
    should be considered immutable.
    """

    def __init__(self, *args, **kwargs):
        super(Resolution, self).__init__(*args, **kwargs)
        self.__dict__ = self  # this allows attribute access: `self.package`
        self._to_list_keys = ["package"]

    def __eq__(self, other):
        # use standard dict equality
        return super(Resolution, self).__eq__(other)

    def __hash__(self):
        return hash((type(self), tuple(self.items())))

    def __str__(self):
        return ' '.join(self.to_list())

    def to_list(self):
        result = []
        for key in self._to_list_keys:
            value = self[key]
            if isinstance(value, list):
                result.extend(value)
            else:
                result.append(value)
        return result


def is_root():
    return os.geteuid() == 0


def elevate_privileges(command):
    if command[0] != "sudo":
        return ["sudo"] + command
    else:
        return command


class InstallerBase(six.with_metaclass(abc.ABCMeta, Installer)):

    """Base class for installer plugins with some reasonable defaults.

    Deriving installers must call this class' :meth:`__init__`.

    :ivar ConfigDescription options_description: description of
        structure and types of ``options`` property. Deriving installers
        may modify it in their :meth:`__init__`, but not after
        ``options`` has been accessed for the first time. Initialization
        of ``options`` with default values from this description is
        delayed until first access.
    :ivar options: the options property can be set as a dictionary and
        is parsed according to ``options_description`` with default
        values filled in; it is always returned as a
        `xylem.config_utils.ConfigDict` instance.
    """

    def __init__(self):
        self.options_description = ConfigDescription("options")
        self.options_description.add("as_root", type=Boolean, default=True)
        self._options = None  # delay loading default config to first access
        self.installer_rule_description = ConfigDescription("rule")
        self.installer_rule_description.add(
            "packages", type=List(String), default=[])
        self.installer_rule_description.add(
            "depends", type=List(String), default=[])

    @property
    def options(self):
        if self._options is None:
            self._options = config_from_defaults(self.options_description)
        return self._options

    @options.setter
    def options(self, value):
        try:
            self._options = config_from_parsed_yaml(
                value, self.options_description, use_defaults=True)
        except ConfigValueError as e:
            raise_from(ConfigValueError, "invalid options `{}` for installer "
                       "'{}'".format(value, self.name), e)
        unused_keys = set(value.keys()) - set(self._options.keys())
        if unused_keys:
            warning("Ignoring the following unknown options for installer "
                    "'{}': {}. Known options are: {}.".
                    format(self.name, ", ".join(unused_keys),
                           ", ".join(self._options.keys())))

    def use_as_additional_installer(self, os_tuple):
        return False

    def _parse_installer_rule(self, installer_rule):
        """Helper to parse installer rule with the installer_description."""
        try:
            parsed_rule = config_from_parsed_yaml(
                installer_rule, self.installer_rule_description,
                use_defaults=True)
        except ConfigValueError as e:
            raise_from(InvalidRuleError, "invalid installer rule `{}` for "
                       "installer '{}'".format(installer_rule, self.name), e)
        unused_keys = set(installer_rule.keys()) - set(parsed_rule.keys())
        if unused_keys:
            warning("ignoring the following unknown keys '{}' while parsing "
                    "installer rule with packages '{}' for installer '{}'".
                    format(parsed_rule.packages, self.name,
                           ", ".join(unused_keys)))
        return parsed_rule

    def get_depends(self, installer_rule):
        parsed_rule = self._parse_installer_rule(installer_rule)
        return parsed_rule.depends

    def resolve(self, installer_rule):
        parsed_rule = self._parse_installer_rule(installer_rule)
        # each package gets its own resolution object
        packages = parsed_rule.pop("packages")
        # dependencies are not included in the resolution objects
        del parsed_rule["depends"]
        result = []
        for p in packages:
            # copy all other entries, e.g. options, to each resolution object
            resolution = Resolution(parsed_rule)
            resolution["package"] = p
            result.append(p)
        return result

    def is_installed(self, resolved):
        if not isinstance(resolved, list):
            resolved = [resolved]
        return not self.filter_uninstalled(resolved)

    def get_install_commands(self,
                             resolved,
                             interactive=True,
                             reinstall=False):
        commands = self.get_install_commands_no_root(self, resolved,
                                                     interactive, reinstall)
        if self.options.as_root and not is_root():
            return [elevate_privileges(cmd) for cmd in commands]
        else:
            return commands

    @abc.abstractmethod
    def get_install_commands_no_root(self,
                                     resolved,
                                     interactive=True,
                                     reinstall=False):
        """Return list of commands without root privileges.

        This is like :meth:`Installer.get_install_commands`, but
        `InstallerBase` takes care of elevating the privileges to root
        if needed. Derived classes should overwrite this method instead
        of :meth:`get_install_commands`.
        """
        raise NotImplementedError()
