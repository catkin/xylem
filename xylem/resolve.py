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

import six

from xylem.config import ensure_config

from xylem.installers import ensure_installer_context
from xylem.installers import InstallerError

from xylem.sources import RulesDatabase
from xylem.sources import ensure_sources_context

from xylem.text_utils import to_str

from xylem.log_utils import error
from xylem.log_utils import info_v

from xylem.exception import chain_exception
from xylem.exception import XylemError

from xylem.util import remove_duplicates


class ResolutionError(XylemError):

    """Exception for failed resolution of keys."""


def resolve(xylem_keys,
            all_keys=False,
            config=None,
            database=None,
            sources_context=None,
            installer_context=None):
    """TODO"""

    #  1. Prepare config and contexts and load database
    config = ensure_config(config)
    ic = ensure_installer_context(installer_context, config)
    del installer_context  # don't use further down, use `ic` only
    if not database:
        sources_context = ensure_sources_context(sources_context, config)
        database = RulesDatabase(sources_context)
        database.load_from_cache()
    del sources_context  # don't use further down, use `database` only

    #  2. Prepare set of keys to look up
    if all_keys:
        lookup_keys = remove_duplicates(xylem_keys + sorted(database.keys(ic)))
    else:
        lookup_keys = remove_duplicates(xylem_keys)

    result = []
    errors = []

    # 3. Create an inverse install-from mapping
    # TODO: maybe allow pattern matching here like
    #       `install-from "pip: python-*"`
    install_from_map = dict()
    for inst, keys in six.iteritems(config.install_from):
        for k in keys:
            if k in install_from_map:
                error("ignoring 'install from {}' for key '{}'; "
                      "already configured to install from '{}'".
                      format(inst, k, install_from_map[k]))
            else:
                install_from_map[k] = inst

    # 4. Resolve each key
    for key in lookup_keys:

        # 4.1.  Lookup key in the database
        try:
            installer_dict = database.lookup(key, ic)
            if not installer_dict:
                errors.append((key, ResolutionError(
                    "could not find rule for xylem key '{}' on '{}'.".
                    format(key, ic.get_os_string()))))
                continue
        except LookupError as e:
            errors.append((key, chain_exception(
                ResolutionError, "lookup for key '{}' failed".format(key), e)))
            continue

        # 4.2.  Decide which installer to use
        if key in install_from_map:
            inst_name = install_from_map[key]
            if not ic.lookup_installer(inst_name):
                errors.append((key, ResolutionError(
                    "explicitly requested to install '{}' from '{}', but that "
                    "installer is not loaded".format(key, inst_name))))
                continue
            if inst_name not in installer_dict:
                errors.append((key, ResolutionError(
                    "explicitly requested to install '{}' from '{}', but no "
                    "rule for that installer was found; found rules for "
                    "installers: `{}`".
                    format(key, inst_name, to_str(installer_dict.keys())))))
                continue
            info_v("found rule for key '{}' for explicitly requested "
                   "installer '{}'".format(key, inst_name))
            rule = installer_dict[inst_name]
            installer = ic.lookup_installer(inst_name)
        else:
            installer = None
            for inst in ic.core_installers:
                if inst.name in installer_dict:
                    info_v("found rule for key '{}' for core installer '{}'".
                           format(key, inst.name))
                    rule = installer_dict[inst.name]
                    installer = inst
                    break
            if installer is None:
                for inst in ic.additional_installers:
                    if inst.name in installer_dict:
                        info_v("found rule for key '{}' for additional "
                               "installer '{}'".format(key, inst.name))
                        rule = installer_dict[inst.name]
                        installer = inst
            if installer is None:
                errors.append((key, ResolutionError(
                    "did not find rule for key '{}' for neither core "
                    "installers '{}' nor additional installers '{}'; rules "
                    "found for installers: '{}'".
                    format(key,
                           to_str(ic.core_installer_names),
                           to_str(ic.additional_installer_names),
                           to_str(installer_dict.keys())))))
                continue

        # 4.3.  Resolve with determined installer
        try:
            resolutions = installer.resolve(rule)
        except InstallerError as e:
            errors.append((key, chain_exception(
                ResolutionError,
                "failed to resolve with installer '{}'".format(installer.name),
                e)))
        else:
            result.append((key, (installer.name, resolutions)))

    return result, errors


# TODO: do dependency resolution here

# TODO: use that to determine flattened tree

# TODO: return and display dependencies in output of `resolve` command

# TODO: deal with resolution objects of the same package, but different
#       options (version, apt-repositories, formula options, etc)

# def resolve_one(xylem_key, installers, )
