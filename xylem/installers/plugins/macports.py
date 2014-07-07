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
