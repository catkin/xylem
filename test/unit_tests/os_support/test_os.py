from __future__ import print_function
from __future__ import unicode_literals

import xylem.os_support.plugins
from xylem.os_support import OSSupport, UnsupportedOSError

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


@patch('xylem.os_support.impl.get_os_plugin_list', autospec=True)
class OSSupportTestCase(unittest.TestCase):

    def test_current_os_throws(self, mock_get_os_plugin_list):
        mock_get_os_plugin_list.return_value = _os_plugin_list

        o = OSSupport()

        # override invalid os
        with self.assertRaises(UnsupportedOSError):
            o.override_os(("foo", "bar"))

        # fake failed detection
        o._os_plugin_list = []
        with self.assertRaises(UnsupportedOSError):
            o.detect_os()

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

        print(os1.get_tuple())
        print(os2.get_tuple())

        assert(os1.get_tuple() == os2.get_tuple())

    def test_detect_os(self, mock_get_os_plugin_list):
        mock_get_os_plugin_list.return_value = _os_plugin_list

        o = OSSupport()
        os = o.get_current_os()
        # TODO: maybe independently detect some common cases like osx,
        # ubuntu, debian and for other oss the only test is that
        # current_os() doesn't throw after detect_os()
        print(o.get_os_plugin_names())
        print("Current: {0}, {1}, {2}".format(
            os.get_name(), os.get_names(), os.get_version()))

    def test_override_os(self, mock_get_os_plugin_list):
        mock_get_os_plugin_list.return_value = _os_plugin_list

        o = OSSupport()
        o.override_os(("ubuntu", "precise"))
        os = o.get_current_os()
        print(o.get_os_plugin_names())
        print("Override OS: {0}, {1}, {2}".format(
            os.get_name(), os.get_names(), os.get_version()))
        assert(os.get_name() == "ubuntu")
        assert(os.get_names() == ["debian", "ubuntu"])
        assert(os.get_version() == "precise")
        assert(os.get_default_installer_name() == "apt")
        assert(os.get_installer_priority("apt") == 90)
        assert(os.get_installer_priority("pip") == 50)
