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

from xylem.log_utils import warning

from xylem.util import read_stdout

DESCRIPTION = """\
Installer plugin for the APT installer for debian/ubuntu, using the
`apt-get` command.
"""

__doc__ %= format(DESCRIPTION)

APT_INSTALLER = 'apt'


# TODO: implement 'apt-repositories' prerequisite

# TODO: use read_stdout_err and do proper error handling here and in
# other installer plugins


class AptInstaller(PackageManagerInstaller):

    def __init__(self):
        super(AptInstaller, self).__init__("apt-get")

    @property
    def name(self):
        return APT_INSTALLER

    def get_install_commands_no_root(self,
                                     resolutions,
                                     interactive,
                                     reinstall):
        # TODO: reinstall
        if reinstall:
            warning("reinstall not implemented for installer 'apt'")
        install_cmd = ["apt-get", "install"]
        if interactive:
            install_cmd.append("-y")
        return [install_cmd + [item.package] for item in resolutions]

    def filter_uninstalled(self, resolutions):

        # TODO: support what was implemented in rosdep with `version_lock_map`,
        #       but do it properly with some form of options:
        #
        #       this is mainly a hack to support version locking for eigen.
        #       we strip version-locking syntax, e.g. libeigen3-dev=3.0.1-*.
        #       our query does not do the validation on the version itself.

        pkgs = {r.package for r in resolutions}
        cmd = ["dpkg-query", "-W", "-f=\'${Package} ${Status}\n\'"] + pkgs
        std_out = read_stdout(cmd)
        output_rows = std_out.replace("\'", "").split("\n")
        installed = set()
        for row in output_rows:
            pkg_row = row.split()
            if len(pkg_row) == 4 and (pkg_row[3] == "installed"):
                installed.add(pkg_row[0])
        return [r for r in resolutions if r.package not in installed]

    def install_package_manager(self, os_tuple):
        # TODO: raise UserInterventionRequiredError with instructions,
        #       handle this error specially and print instructions
        raise NotImplementedError()


# This definition the installer to the plugin loader
definition = dict(
    plugin_name=APT_INSTALLER,
    description=DESCRIPTION,
    installer=AptInstaller
)
