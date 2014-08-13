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

"""Installer plugin for pip.

%s

:var definition: definition of the installer plugin to be referenced
    by the according entry point
"""

from __future__ import unicode_literals

from xylem.installers.package_manager_installer import PackageManagerInstaller

from xylem.util import read_stdout

from xylem.log_utils import warning


DESCRIPTION = """\
This is a installer plugin for the pip python package manager.

See https://pypi.python.org/pypi/pip
"""

__doc__ %= format(DESCRIPTION)

PIP_INSTALLER = 'pip'


class PipInstaller(PackageManagerInstaller):
    """
    Installer support for pip.
    """

    def __init__(self):
        super(PipInstaller, self).__init__("pip")

    @property
    def name(self):
        return PIP_INSTALLER

    def use_as_additional_installer(self, os_tuple):
        # use everywhere
        return True

    def get_install_commands_no_root(self,
                                     resolutions,
                                     interactive,
                                     reinstall):
        # TODO: reinstall
        if reinstall:
            warning("reinstall not implemented for installer 'pip'")
        return [["pip", "install", "-U", item.package] for item in resolutions]

    def filter_uninstalled(self, resolutions):
        installed = read_stdout(['pip', 'freeze']).split('\n')
        installed = set(row.split("==")[0] for row in installed)
        return [r for r in resolutions if r.package not in installed]

    def install_package_manager(self, os_tuple):
        # TODO: use get_pip or maybe apt on ubuntu to install pip
        raise NotImplementedError()


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=PIP_INSTALLER,
    description=DESCRIPTION,
    installer=PipInstaller
)
