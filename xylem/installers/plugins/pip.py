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

import subprocess

from xylem.installers import PackageManagerInstaller
from xylem.util import read_stdout
from xylem.exception import InstallerNotAvailable

DESCRIPTION = """\
This is a installer plugin for the pip python package manager.

See https://pypi.python.org/pypi/pip
"""

__doc__ %= format(DESCRIPTION)

PIP_INSTALLER = 'pip'


def is_pip_installed():
    """Return True if 'pip' can be executed."""
    try:
        subprocess.Popen(['pip'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
        return True
    except OSError:
        return False


def pip_detect(pkgs, exec_fn=None):
    """
    Given a list of package, return the list of installed packages.

    :param exec_fn: function to execute Popen and read stdout (for testing)
    """
    if exec_fn is None:
        exec_fn = read_stdout
    pkg_list = exec_fn(['pip', 'freeze']).split('\n')

    # TODO: this does not retain order of pkgs
    # TODO: what about packages installed with `develop`?
    ret_list = []
    for pkg in pkg_list:
        pkg_row = pkg.split("==")
        if pkg_row[0] in pkgs:
            ret_list.append(pkg_row[0])
    return ret_list


class PipInstaller(PackageManagerInstaller):
    """
    Installer support for pip.
    """

    @staticmethod
    def get_name():
        return PIP_INSTALLER

    def __init__(self):
        super(PipInstaller, self).__init__(pip_detect, supports_depends=True)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        if not is_pip_installed():
            raise InstallerNotAvailable("pip is not installed")
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        return [['sudo', 'pip', 'install', '-U', p] for p in packages]

    def get_priority_for_os(self, os_name, os_version):
        # return a medium priority on any OS
        return 50


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=PIP_INSTALLER,
    description=DESCRIPTION,
    installer=PipInstaller
)
