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

import xylem.os_support.plugins

from xylem.os_support import OSSupport
from xylem.os_support import UnsupportedOSError
from xylem.os_support import UnsupportedOSVersionError

import unittest
from mock import patch
from pprint import pprint

# List of OS plugins to not rely on entry points for these tests
_os_plugin_list = [
    xylem.os_support.plugins.Debian(),
    xylem.os_support.plugins.Ubuntu(),
    xylem.os_support.plugins.OSX()
]

# Default installers matching when the above list of os plugins define
_default_installers = {
    'debian': 'apt',
    'ubuntu': 'apt',
    'osx': 'homebrew'
}

# TODO: test the real `xylem.os_support.impl.get_os_plugin_list`


class OSSupportCurrentTestCase(unittest.TestCase):

    def test_detect_running_os(self):
        # test that the actual OS is detected (no exception is raised)
        o = OSSupport()
        name, version = o.get_current_os().get_tuple()
        assert(name is not None)
        assert(version is not None)

    def test_detect_version_only(self):
        # test that the actual OS is detected (no exception is raised)
        o = OSSupport()
        name, version = o.get_current_os().get_tuple()

        o = OSSupport()
        o.override_os((name, None))
        os = o.get_current_os()
        assert(name == os.name)
        assert(version == os.get_version())


@patch('xylem.os_support.impl.get_os_plugin_list', autospec=True)
class OSSupportTestCase(unittest.TestCase):

    def test_current_os_throws(self, mock_get_os_plugin_list):
        mock_get_os_plugin_list.return_value = _os_plugin_list

        o = OSSupport()

        # override invalid os
        with self.assertRaises(UnsupportedOSError):
            o.override_os(("foo", "bar"))
            print("invalid os 'foo' did not raise")

        with self.assertRaises(UnsupportedOSVersionError):
            o.override_os(("ubuntu", "bar"))
            print("invlid ubuntu version 'bar' did not raise")

        # fake failed detection
        o._os_plugin_list = []
        with self.assertRaises(UnsupportedOSError):
            o.detect_os()
            print("failed detection did not raise")

    def test_default_installer_name(self, mock_get_os_plugin_list):
        mock_get_os_plugin_list.return_value = _os_plugin_list

        o = OSSupport()

        expected = _default_installers
        result = o.get_default_installer_names()
        if expected != result:
            print("result:")
            pprint(result)
            print("expected:")
            pprint(expected)
        assert(expected == result)

    def test_get_current_os(self, mock_get_os_plugin_list):
        mock_get_os_plugin_list.return_value = _os_plugin_list

        # get_current_os calls detect_os if no os not set yet
        o1 = OSSupport()
        o1.detect_os()
        os1 = o1.get_current_os()

        o2 = OSSupport()
        os2 = o2.get_current_os()

        assert(os1.get_tuple() == os2.get_tuple())

    def test_override_os(self, mock_get_os_plugin_list):
        mock_get_os_plugin_list.return_value = _os_plugin_list

        o = OSSupport()
        o.override_os(("ubuntu", "precise"))
        os = o.get_current_os()
        assert(os.name == "ubuntu")
        assert(os.all_names == ["ubuntu", "debian"])
        assert(os.get_version() == "precise")
        assert(os.get_all_tuples("precise") == [("ubuntu", "precise"), ("debian", None)])
        assert(os.default_installer == "apt")
        assert(os.core_installers == ["apt"])
