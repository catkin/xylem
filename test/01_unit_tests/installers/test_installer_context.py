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

from __future__ import print_function
from __future__ import unicode_literals
from xylem.installers import InstallerContext
from xylem.config import get_default_config
import unittest
from six.moves import map

# TODO: Use mock to replace the functions loading the plugins


class InstallerContextTestCase(unittest.TestCase):

    def test_setup_installers(self):
        config = get_default_config()
        config.os_override = ("ubuntu", "precise")
        ic = InstallerContext(config=config)
        assert(ic.get_default_installer_name() == 'apt')
        assert(ic.lookup_installer(ic.get_default_installer_name()).name == 'apt')
        assert(ic.core_installers == [ic.lookup_installer("apt")])
