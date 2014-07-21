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

from .sources import SourcesContext
from .sources import RulesDatabase
from .installers import InstallerContext

from .log_utils import debug


def resolve(xylem_keys, prefix=None, os_override=None, all_keys=False):

    # xylem_keys can be one key or list of keys, return value accordingly

    sources_context = SourcesContext(prefix=prefix)

    database = RulesDatabase(sources_context)
    database.load_from_cache()

    if isinstance(os_override, InstallerContext):
        ic = os_override
    else:
        ic = InstallerContext(os_override=os_override)

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
        for installer_name, rule in installer_dict.items():
            priority = ic.get_installer_priority(installer_name)
            if priority is None:
                debug("Ignoring installer '{0}' for resolution of '{1}' "
                      "because it is not registered for '{2}'".
                      format(installer_name, key, ic.get_os_string()))
                continue
            if 'priority' in rule:
                priority = rule['priority']

            installer = ic.get_installer(installer_name)
            resolutions = installer.resolve(rule)

            # TODO: use installer instead of installer_name here?
            rules.append((priority, installer_name, resolutions))

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
            rules.sort(reverse=True)
            result.append((key, rules))

    if not list_argument:
        assert(len(result) == 1)
        key, resolution = result[0]
        result = resolution
    else:
        result = sorted(result)

    return result
