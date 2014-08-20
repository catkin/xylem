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

"""Installer plugin for APT.

%s
"""

from __future__ import unicode_literals

from xylem.installers.package_manager_installer import PackageManagerInstaller

DESCRIPTION = """\
TODO: Describe and implement this
"""

__doc__ %= format(DESCRIPTION)

APT_INSTALLER = 'apt'


# TODO: implement 'apt-repositories' prerequisite


class AptInstaller(PackageManagerInstaller):

    def __init__(self):
        super(AptInstaller, self).__init__("apt-get")

    @property
    def name(self):
        return APT_INSTALLER

    def get_install_commands_no_root(self,
                                     resolved,
                                     interactive=True,
                                     reinstall=False):
        # FIXME
        return [["apt-get", "install", item.package] for item in resolved]

    def filter_uninstalled(self, resolved):
        # FIXME
        return resolved

    def install_package_manager(self, os_tuple):
        # TODO: raise UserInterventionRequiredError with instructions,
        # handle this error specially and print instructions
        raise NotImplementedError()


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=APT_INSTALLER,
    description=DESCRIPTION,
    installer=AptInstaller
)
