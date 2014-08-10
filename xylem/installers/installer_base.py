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

from xylem.exception import type_error_msg

from xylem.text_utils import text_type

from xylem.exception import raise_from

from xylem.log_utils import warning

from xylem.config_utils import ConfigDescription
from xylem.config_utils import ConfigValueError
from xylem.config_utils import Boolean
from xylem.config_utils import config_from_parsed_yaml
from xylem.config_utils import config_from_defaults


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

    :ivar Configdescription options_description: description of
        structure and types of :ivar:`options` property. Deriving
        installers may modify it in their `__init__`, but not after
        `options` has been accessed for the first time. Initialization
        of :ivar:`options` with default values from this description is
        delayed until first access.
    """

    def __init__(self):
        self.options_description = ConfigDescription("options")
        self.options_description.add("as_root", type=Boolean, default=True)
        self._options = None  # delay loading default config to first access

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

    def get_depends(self, installer_rule):
        if not isinstance(installer_rule, dict):
            raise InvalidRuleError(type_error_msg(
                "dict", installer_rule, what_for="installer rule for "
                "installer '{}'".format(self.name)))
        if "depends" in installer_rule:
            if not isinstance(installer_rule["depends"], list):
                raise InvalidRuleError(type_error_msg(
                    "list", installer_rule["depends"], what_for="`depends` "
                    "in installer rule `{}` for installer '{}'".
                    format(installer_rule, self.name)))
            for d in installer_rule["depends"]:
                if isinstance(d, text_type):
                    raise InvalidRuleError(type_error_msg(
                        "string", d, what_for="dependency in `depends` of "
                        "installer rule `{}` for installer '{}'".
                        format(installer_rule, self.name)))
            return installer_rule["depends"][:]
        else:
            return []

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
