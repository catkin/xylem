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
import unittest
from six.moves import map

# TODO: Use mock to replace the functions loading the plugins


class InstallerContextTestCase(unittest.TestCase):

    def test_setup_installers(self):
        ic = InstallerContext()
        ic.set_os_override(("ubuntu", "precise"))
        print(ic.get_os_tuple())
        print(map(lambda i: i.get_name(), ic.installer_plugins))
        ic.setup_installers()
        assert(ic.get_default_installer_name() == 'apt')
        assert(ic.get_installer(ic.get_default_installer_name()).get_name() == 'apt')
        assert(ic.get_installer_priority('apt') == 90)
