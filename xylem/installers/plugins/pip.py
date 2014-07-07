"""
%s

:var description: description of the installer plugin to be referenced
    by the according entry point
"""

from __future__ import unicode_literals

import subprocess

from ..package_manager_installer import PackageManagerInstaller
from ...util import read_stdout
from ...exception import InstallerNotAvailable

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
