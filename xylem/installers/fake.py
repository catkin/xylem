"""
%s

:var INSTALL_LOCATION: the installation folder
:var description: description of the installer plugin to be referenced
    by the according entry point
"""


from __future__ import print_function
import os.path

from .package_manager_installer import PackageManagerInstaller

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


def get_installer_filename(resolved_item):
    """Return the location of the file indicating installation of item."""
    return os.path.abspath(os.path.join(INSTALL_LOCATION, resolved_item))


def detect_fn(resolved):
    """Return list of subset of  installed packages."""
    return filter(lambda pkg: os.path.exists(get_installer_filename(pkg)),
                  resolved)


class FakeInstaller(PackageManagerInstaller):

    """FakeInstaller class for testing.

    The opaque installer items are simply strings (package names).

    Packages are installed by touching files in `INSTALL_LOCATION`. The
    folder must exist, else installation fails and all packages are
    assumed uninstalled.
    """

    @staticmethod
    def get_name():
        return FAKE_INSTALLER

    def __init__(self):
        super(FakeInstaller, self).__init__(detect_fn, supports_depends=True)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        return [["touch", self.get_installer_filename(item)] for
                item in resolved]


# This describes this installer to the plugin loader
description = dict(
    plugin_name=FAKE_INSTALLER_PLUGIN,
    description=DESCRIPTION,
    installer=FakeInstaller
)
