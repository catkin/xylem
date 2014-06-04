"""
Fake installer for testing.

See ``DESCRIPTION``
"""

# TODO: proper symbol reference in above docstring.

from __future__ import print_function
import os.path

from package_manager_installer import PackageManagerInstaller

DESCRIPTION = """\
This is a fake installer plugin for testing.

It is able to install any package and 'installs'/'removes' packages by
touching/removing files in a folder.
"""

# pretend we are apt so we get the resolutions from the existing rosdep
# when overriding os with ubuntu for testing
FAKE_INSTALLER_PLUGIN = 'fake'
FAKE_INSTALLER = 'apt'

# TODO: howto docstrings for global variables?

# Folder in which the installer 'installs' packages
INSTALL_LOCATION = 'fake-installer'


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
