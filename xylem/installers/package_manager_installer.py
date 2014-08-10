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

import six
import abc

from .installer_base import InstallerBase
from .impl import InstallerPrerequisiteError
from .impl import InvalidRuleError

from xylem.util import is_program_installed
from xylem.exception import raise_from

from xylem.log_utils import info_v
from xylem.log_utils import warning
from xylem.log_utils import error

from xylem.config_utils import ConfigDescription
from xylem.config_utils import ConfigValueError
from xylem.config_utils import List
from xylem.config_utils import String
from xylem.config_utils import config_from_parsed_yaml


class Resolution(dict):

    """Resolution object as a dictionary with attribute access.

    Corresponds to a single package to be installed by a package
    manager. By default only key `package` is assumed. Equality is the
    same as dictionary equality. Use :ivar:`_to_list_keys` to define how
    the resolution is printed.

    These objects are hashable, which is used to remove duplicates of a
    list of resolutions. This means that once created by `resolve`, they
    should be considered immutable.
    """

    def __init__(self, *args, **kwargs):
        super(Resolution, self).__init__(*args, **kwargs)
        self.__dict__ = self  # this allows attribute access `self.packages`
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


class PackageManagerInstaller(six.with_metaclass(abc.ABCMeta, InstallerBase)):

    # FIXME: 'supports_depends' is misnomer, since it can get confused
    # with the assertion that the package manger supports dependency
    # resolution, which is somewhat antithetical to the rules definition
    # supporting dependencies. Do we need this flag at all? Can't we
    # just interpret the 'depends' key for all installers?

    """Base class from a variety of package manager installers."""

    def __init__(self, executable_name):
        super(PackageManagerInstaller, self).__init__()
        self.executable_name = executable_name
        self.installer_rule_description = ConfigDescription("rule")
        self.installer_rule_description.add(
            "packages", type=List(String), default=[])
        self.installer_rule_description.add(
            "depends", type=List(String), default=[])

    # TODO: move this to InstallerBase
    def resolve(self, installer_rule):
        try:
            parsed_rule = config_from_parsed_yaml(
                installer_rule, self.installer_rule_description,
                use_defaults=True)
        except ConfigValueError as e:
            raise_from(InvalidRuleError, "invalid installer rule `{}` for "
                       "installer '{}'".format(installer_rule, self.name), e)
        unused_keys = set(installer_rule.keys()) - set(parsed_rule.keys())
        if unused_keys:
            warning("Ignoring the following unknown keys while parsing the "
                    "installer rule with packages '{}' for installer '{}': "
                    "{}.".format(parsed_rule.packages, self.name,
                                 ", ".join(unused_keys)))
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

    def check_general_prerequisites(self,
                                    os_tuple,
                                    fix_unsatisfied=False,
                                    interactive=True):
        info_v("Checking general prerequisites of installer '{}'...".
               format(self.name))
        self.check_package_manager_installer(
            os_tuple, fix_unsatisfied, interactive)
        self.check_package_manager_updated(
            os_tuple, fix_unsatisfied, interactive)

    def check_install_prerequisites(self,
                                    resolved,
                                    os_tuple,
                                    fix_unsatisfied=False,
                                    interactive=True):
        info_v("Checking install prerequisites of installer '{}'... "
               "No checks implemented.".format(self.name))

    def is_package_manager_installed(self):
        return is_program_installed(self._executable_name)

    def install_package_manager(self, os_tuple, interactive=True):
        raise NotImplementedError()

    def check_package_manager_installer(self,
                                        os_tuple,
                                        fix_unsatisfied=False,
                                        interactive=True):
        info_v("Checking if package manager '{}' is installed.".
               format(self.name))
        if self.is_package_manager_installed():
            info_v("Package manager '{}' is installed.".format(self.name))
            return
        info_v("Package manager '{}' not installed ('{}' not found).".
               format(self.name, self.executable_name))
        if fix_unsatisfied:
            info_v("Trying to install '{}'.".format(self.name))
            try:
                self.install_package_manager(os_tuple, interactive)
                if self.is_package_manager_installed():
                    return
            except NotImplementedError:
                error("Installer plugin '{}' does not support installing "
                      "itself.".format(self.name))
            else:
                error("Installer plugin '{}' failed to install itself.".
                      format(self.name))
        raise InstallerPrerequisiteError("Package manager '{}' not installed".
                                         format(self.name))

    def is_package_manager_updated(self):
        raise NotImplementedError()

    def update_package_manager(self, interactive=True):
        raise NotImplementedError()

    def check_package_manager_updated(self,
                                      os_tuple,
                                      fix_unsatisfied=False,
                                      interactive=True):
        info_v("Checking if package manager '{}' is updated.".
               format(self.name))
        try:
            updated = self.is_package_manager_updated()
        except NotImplementedError:
            info_v("Check if package manager '{}' is updated not implemented; "
                   "skipping check.".format(self.name))
            return
        if updated:
            info_v("Package manager '{}' is updated.".format(self.name))
            return
        info_v("Package manager '{}' not updated.".format(self.name))
        if fix_unsatisfied:
            info_v("Trying to update '{}'.".format(self.name))
            try:
                self.update_package_manager(interactive)
                if self.is_package_manager_updated():
                    return
            except NotImplementedError:
                error("Installer plugin '{}' does not support updating "
                      "itself.".format(self.name))
            else:
                error("Installer plugin '{}' failed to update itself.".
                      format(self.name))
        warning("Package manager '{}' seems to be out-of-date. Please "
                "consider updating for best results.")
