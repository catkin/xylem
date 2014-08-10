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
from xylem.specs.plugins.rules import compact_installer_dict
from xylem.config import get_config


def lookup(xylem_key, compact=False, config=None, sources_context=None,
           installer_context=None):

    if config is None:
        config = get_config()

    sources_context = sources_context or SourcesContext(config)
    ic = installer_context or InstallerContext(config)

    database = RulesDatabase(sources_context)
    database.load_from_cache()

    installer_dict = database.lookup(xylem_key, ic)

    if compact:
        default_installer_name = ic.get_default_installer_name()
        compacted = compact_installer_dict(installer_dict,
                                           default_installer_name)

    return compacted
