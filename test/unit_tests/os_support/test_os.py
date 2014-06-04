
# FIXME: How to deal with entry points for unit tests?

from xylem.os_support import OSSupport, UnsupportedOSError
import unittest


class OSSupportTestCase(unittest.TestCase):

    def test_current_os_throws(self):
        o = OSSupport()

        # override invalid os
        with self.assertRaises(UnsupportedOSError):
            o.override_os("foo", "bar")

        # fake failed detection
        o._os_plugin_list = []
        with self.assertRaises(UnsupportedOSError):
            o.detect_os()

    def test_get_current_os(self):
        # get_current_os calls detect_os if no os not set yet
        o1 = OSSupport()
        o1.detect_os()
        os1 = o1.get_current_os()

        o2 = OSSupport()
        os2 = o2.get_current_os()

        print(os1.get_name_and_version())
        print(os2.get_name_and_version())

        assert(os1.get_name_and_version() == os2.get_name_and_version())

    def test_detect_os(self):
        o = OSSupport()
        o.detect_os()
        os = o.get_current_os()
        # TODO: maybe independently detect some common cases like osx,
        # ubuntu, debian and for other oss the only test is that
        # current_os() doesn't throw after detect_os()
        print(o.get_os_plugin_names())
        print("Current: {0}, {1}, {2}".format(
            os.get_name(), os.get_names(), os.get_version()))

    def test_override_os(self):
        o = OSSupport()
        o.override_os("ubuntu", "precise")
        os = o.get_current_os()
        print(o.get_os_plugin_names())
        print("Override OS: {0}, {1}, {2}".format(
            os.get_name(), os.get_names(), os.get_version()))
        assert(os.get_name() == "ubuntu")
        assert(os.get_names() == ["debian", "ubuntu"])
        assert(os.get_version() == "precise")
        assert(os.get_default_installer_name() == "apt")
        assert(os.get_installer_priority("apt") == 50)
        assert(os.get_installer_priority("pip") == 20)
