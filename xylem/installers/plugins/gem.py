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

"""Installer plugin for ruby gem.

%s
"""

from __future__ import unicode_literals

from xylem.installers.package_manager_installer import PackageManagerInstaller

from xylem.util import read_stdout

from xylem.log_utils import warning


DESCRIPTION = """\
This is a installer plugin for the gem ruby package manager.
"""

__doc__ %= format(DESCRIPTION)

GEM_INSTALLER = 'gem'


class GemInstaller(PackageManagerInstaller):
    """
    Installer support for ruby gem.
    """

    def __init__(self):
        super(GemInstaller, self).__init__("gem")

    @property
    def name(self):
        return GEM_INSTALLER

    def use_as_additional_installer(self, os_tuple):
        # use everywhere
        return True

    def get_install_commands_no_root(self,
                                     resolved,
                                     interactive,
                                     reinstall):
        # TODO: reinstall
        if reinstall:
            warning("reinstall not implemented for installer 'gem'")
        return [["gem", "install", item.package] for item in resolved]

    def filter_uninstalled(self, resolved):
        installed = read_stdout(['gem', 'list']).split('\n')
        installed = set(row.split(" ")[0] for row in installed)
        return [r for r in resolved if r.package not in installed]

    def install_package_manager(self, os_tuple):
        # TODO: install gem if not present or notify user that something
        #       is wrong
        raise NotImplementedError()


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=GEM_INSTALLER,
    description=DESCRIPTION,
    installer=GemInstaller
)
