from __future__ import print_function
from __future__ import unicode_literals
from xylem.installers import InstallerContext
import unittest
from six.moves import map

# TODO: Use mock to replace the functions loading the plugins


class InstallerContextTestCase(unittest.TestCase):

    def test_setup_installers(self):
        ic = InstallerContext()
        ic.set_os_override("ubuntu", "precise")
        print(ic.get_os_name_and_version())
        print(map(lambda i: i.get_name(), ic.installer_plugins))
        ic.setup_installers()
        assert(ic.get_default_installer().get_name() == 'apt')
        assert(ic.get_installer_priority('apt') == 50)
