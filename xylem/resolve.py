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

from xylem.sources import SourcesContext
from xylem.sources import RulesDatabase
from xylem.installers import InstallerContext

from xylem.log_utils import debug
from xylem.config import get_config


def resolve(xylem_keys, all_keys=False, config=None, sources_context=None,
            installer_context=None):
    if config is None:
        config = get_config()
    sources_context = sources_context or SourcesContext(config=config)
    ic = installer_context or InstallerContext(config=config)

    # xylem_keys can be one key or list of keys, return value accordingly
    database = RulesDatabase(sources_context)
    database.load_from_cache()

    list_argument = isinstance(xylem_keys, list)
    if not list_argument:
        xylem_keys = [xylem_keys]
    requested_keys = list(xylem_keys)

    if all_keys:
        list_argument = True
        xylem_keys.extend(database.keys(ic))
        xylem_keys = set(xylem_keys)

    result = []
    for key in xylem_keys:
        installer_dict = database.lookup(key, ic)
        if not installer_dict:
            raise LookupError("Could not find rule for xylem key '{0}' on "
                              "'{1}'.".format(key, ic.get_os_string()))
        rules = []
        for installer in ic.get_installers():
            if installer.name in installer_dict:
                resolutions = installer.resolve(installer_dict[installer.name])
                rules.append((installer.name, resolutions))

        # TODO: check installers in installer dict that are not configured
        # debug("Ignoring installer '{0}' for resolution of '{1}' "
        #      "because it is not registered for '{2}'".
        #       format(installer_name, key, ic.get_os_string()))

            # TODO: use installer instead of installer_name here?
        if not rules:
            # This means we have rules, but non for registered
            # installers, ignore this key unless it is in the requested
            # list of keys
            if key in requested_keys:
                raise LookupError(
                    "Could not find rule for xylem key '{0}' on '{1}' for "
                    "registered installers '{2}'. Found rules for "
                    "installers '{3}'.".
                    format(key, ic.get_os_string(),
                           ", ".join(ic.get_installer_names()),
                           ", ".join(installer_dict.keys())))
            else:
                debug("Could not find rule for xylem key '{0}' on '{1}' for "
                      "registered installers '{2}'. Found rules for "
                      "installers '{3}'. Ignoring from 'all' keys.".
                      format(key, ic.get_os_string(),
                             ", ".join(ic.get_installer_names()),
                             ", ".join(installer_dict.keys())))
        else:
            result.append((key, rules))
    if not list_argument:
        assert(len(result) == 1)
        key, resolution = result[0]
        result = resolution
    else:
        result = sorted(result)
    return result
