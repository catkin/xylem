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

from __future__ import unicode_literals

from . import Installer
from xylem.exception import InvalidDataError


class PackageManagerInstaller(Installer):

    # FIXME: 'supports_depends' is misnomer, since it can get confused
    # with the assertion that the package manger supports dependency
    # resolution, which is somewhat antithetical to the rules definition
    # supporting dependencies. Do we need this flag at all? Can't we
    # just interpret the 'depends' key for all installers?

    """Base class from a variety of package manager installers.

    General form of a package manager :class:`Installer` implementation
    that assumes:

     - installer rule-args spec is a list of package names stored with
       the key "packages"
     - a detect function exists that given a list of packages, returns a
       list of the installed packages

    Also, if *supports_depends* is set to ``True``:

     - installer rule-args spec can also include dependency
       specification with the key "depends"

    Subclasses need to provide implementation of
    ``get_install_command``.

    In addition, if subclass provide their own ``resolve`` method, the
    resolved items need not be package names (i.e. strings). Methods
    other than ``get_isntall_command``, ``resolve`` and the
    ``detect_fn`` treat the resolved items as opaque objects.
    """

    def __init__(self, detect_fn, supports_depends=False):
        """
        :param detect_fn: function that takes list of opaque resolved
            installation items and returns list of the subset of
            installed items.
        :param bool supports_depends: package manager supports
            dependency key
        """
        self.detect_fn = detect_fn
        self.supports_depends = supports_depends

    def is_installed(self, resolved_item):
        return not self.get_packages_to_install([resolved_item])

    def get_depends(self, rule_args):
        """Get list list of dependencies on other xylem keys.

        :param dict rule_args: argument dictionary to the xylem rule for
            this package manager
        :return: List of dependencies on other xylem keys read from the
            'depends' key in `rule_args` if `self.supports_depends` is
            `True`.
        """
        if self.supports_depends and isinstance(rule_args, dict):
            return rule_args.get('depends', [])
        else:
            return []

    def resolve(self, rules_args):
        """
        See :meth:`Installer.resolve()`.
        """
        packages = None
        if isinstance(rules_args, dict):
            packages = rules_args.get("packages", [])
            if isinstance(packages, str):
                packages = packages.split()
        elif isinstance(rules_args, str):
            packages = rules_args.split()
        elif isinstance(rules_args, list):
            packages = rules_args
        else:
            raise InvalidDataError("Invalid rule args: %s" % (rules_args))
        return packages

    def get_packages_to_install(self, resolved, reinstall=False):
        if reinstall:
            return resolved
        if not resolved:
            return []
        else:
            return list(set(resolved) - set(self.detect_fn(resolved)))
