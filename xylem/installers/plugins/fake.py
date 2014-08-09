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

:var INSTALL_LOCATION: the installation folder
:var definition: definition of the installer plugin to be referenced
    by the according entry point
"""

# TODO: rename to `fake apt`

from __future__ import unicode_literals

import os.path

from xylem.installers.package_manager_installer import PackageManagerInstaller

DESCRIPTION = """\
This is a fake installer plugin for testing.

It is able to install any package and 'installs'/'removes' packages by
touching/removing files in a folder.
"""

__doc__ %= format(DESCRIPTION)


FAKE_INSTALLER_PLUGIN = 'fake'
"""Name of the fake installer plugin."""

FAKE_INSTALLER = 'apt'
"""Name of the fake installer. Pretend it is called 'apt' so we get the
resolutions from the existing rosdep rules when overriding os with
Ubuntu for testing."""

INSTALL_LOCATION = 'fake-installer'
"""Install folder where the installed packages are 'installed' by touching
files. Can be relative (to the cwd of xylem invocation) or absolute."""


def get_install_dir():
    return os.path.abspath(os.path.expanduser(INSTALL_LOCATION))


def get_installer_filename(package):
    """Return the location of the file indicating installation of item."""
    return os.path.abspath(os.path.join(get_install_dir(), package))


class FakeInstaller(PackageManagerInstaller):

    """FakeInstaller class for testing.

    Packages are installed by touching files in `INSTALL_LOCATION`. The
    folder must exist, else installation fails and all packages are
    assumed uninstalled.
    """

    def __init__(self):
        super(FakeInstaller, self).__init__("touch")
        self.options_description.items["as_root"].default = False

    @property
    def name(self):
        return FAKE_INSTALLER

    def get_install_commands_no_root(self,
                                     resolved,
                                     interactive=True,
                                     reinstall=False):
        return [["touch", self.get_installer_filename(item.package)] for
                item in resolved]

    def filter_uninstalled(self, resolved):
        return [r for r in resolved
                if not os.path.exists(get_installer_filename(r.package))]

    def is_package_manager_installed(self):
        """Fake installer is installer if that folder is an existing dir."""
        return os.path.isdir(get_install_dir())

    def install_package_manager(self, os_tuple):
        """Installing fake installer means creating that folder."""
        if not os.path.exists(get_install_dir()):
            os.makedirs(get_install_dir())


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=FAKE_INSTALLER_PLUGIN,
    description=DESCRIPTION,
    installer=FakeInstaller
)
