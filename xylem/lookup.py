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
from .specs.rules import compact_installer_dict


def lookup(xylem_key, prefix=None, os_override=None, compact=False):

    sources_context = SourcesContext(prefix=prefix)

    database = RulesDatabase(sources_context)
    database.load_from_cache()

    if isinstance(os_override, InstallerContext):
        ic = os_override
    else:
        ic = InstallerContext(os_override=os_override)

    installer_dict = database.lookup(xylem_key, ic)

    if compact:
        default_installer_name = ic.get_default_installer_name()
        compacted = compact_installer_dict(installer_dict,
                                           default_installer_name)

    return compacted
