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

"""
%s

:var definition: definition of the installer plugin to be referenced
    by the according entry point
"""

from __future__ import unicode_literals

from ..package_manager_installer import PackageManagerInstaller

DESCRIPTION = """\
TODO: Describe and implement this
"""

__doc__ %= format(DESCRIPTION)

MACPORTS_INSTALLER = 'macports'


def fixme_detect(pkgs, exec_fn=None):
    return pkgs


class MacportsInstaller(PackageManagerInstaller):

    @staticmethod
    def get_name():
        return MACPORTS_INSTALLER

    def __init__(self):
        super(MacportsInstaller, self).__init__(
            fixme_detect, supports_depends=True)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        return [['fixme', 'port', 'install', p] for p in packages]


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=MACPORTS_INSTALLER,
    description=DESCRIPTION,
    installer=MacportsInstaller
)
