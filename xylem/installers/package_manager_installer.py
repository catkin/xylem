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

from .installer_base import InstallerBase
from .impl import InstallerPrerequisiteError

from xylem.util import is_program_installed

from xylem.log_utils import info_v
from xylem.log_utils import warning
from xylem.log_utils import error


class PackageManagerInstaller(InstallerBase):

    """Base class from a variety of package manager installers."""

    def __init__(self, executable_name):
        super(PackageManagerInstaller, self).__init__()
        self.executable_name = executable_name

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

    def check_package_manager_installed(self,
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
