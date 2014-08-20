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

"""A fake installer plugin for testing.

%s

:var DEFAULT_INSTALL_DIR: the default installation folder
:var definition: definition of the installer plugin to be referenced
    by the according entry point
"""

# TODO: rename to `fake apt`

from __future__ import unicode_literals

import os.path

from xylem.installers.package_manager_installer import PackageManagerInstaller

from xylem.config_utils import String
from xylem.config_utils import Path


DESCRIPTION = """\
This is a fake installer plugin for testing.

It is able to install any package and 'installs'/'removes' packages by
touching/removing files in a folder.
"""

__doc__ %= format(DESCRIPTION)


FAKE_INSTALLER_PLUGIN = 'fake'
"""Name of the fake installer plugin."""

FAKE_INSTALLER_DEFAULT_NAME = 'fake'
"""Name of the fake installer if not set configured."""

DEFAULT_INSTALL_DIR = os.path.abspath(os.path.expanduser('~/.fake-installer'))
"""Install folder where the installed packages are 'installed' by touching
files. Can be relative (to the cwd of xylem invocation) or absolute."""


class FakeInstaller(PackageManagerInstaller):

    """FakeInstaller class for testing.

    Packages are installed by touching files in `INSTALL_LOCATION`. The
    folder must exist, else installation fails and all packages are
    assumed uninstalled.
    """

    def __init__(self):
        super(FakeInstaller, self).__init__("touch")
        self.options_description.items["as_root"].default = False
        self.options_description.add(
            "fake_name", type=String,
            default=FAKE_INSTALLER_DEFAULT_NAME)
        self.options_description.add(
            "install_dir", type=Path,
            default=DEFAULT_INSTALL_DIR)

    @property
    def name(self):
        return self.options.fake_name or FAKE_INSTALLER_DEFAULT_NAME

    def get_install_commands_no_root(self,
                                     resolved,
                                     interactive=True,
                                     reinstall=False):
        return [["touch", self.get_installer_filename(item.package)] for
                item in resolved]

    def filter_uninstalled(self, resolved):
        return [r for r in resolved
                if not os.path.exists(self.get_installer_filename(r.package))]

    def is_package_manager_installed(self):
        """Fake installer is installed if that folder is an existing dir."""
        return os.path.isdir(self.options.install_dir)

    def install_package_manager(self, os_tuple, interactive=True):
        """Installing fake installer means creating that folder."""
        if not os.path.exists(self.options.install_dir):
            os.makedirs(self.options.install_dir)

    def get_installer_filename(self, package):
        """Return the location of the file indicating installation of item."""
        return os.path.join(self.options.install_dir, package)


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=FAKE_INSTALLER_PLUGIN,
    description=DESCRIPTION,
    installer=FakeInstaller
)
