
from __future__ import print_function

import pkg_resources

from ..log_utils import warning

OS_GROUP = 'xylem.os'


class UnsupportedOSError(Exception):

    """
    Operating system unsupported.

    Detected operating system is not supported or could not be
    identified.
    """

    pass


class OS(object):

    """OS plugin class.

    OS plugins should define entry points as classes derived from this.
    """

    def __init__(self):
        self.names = []
        self.detect = None
        self._use_codename = False

    def is_os(self):
        if self.detect:
            return self.detect.is_os()
        else:
            return False

    def get_name(self):
        if self.names:
            return self.names[-1]
        else:
            return ""

    def get_names(self):
        return self.names

    def get_version(self):
        if self.detect:
            if self.use_codename:
                return self.detect.get_codename()
            else:
                return self.detect.get_version()
        else:
            return ""

    def get_name_and_version(self):
        """Return (name,version) tuple."""
        return self.get_name(), self.get_version()


class OverrideOS(OS):

    """Acts as a proxy to another OS with fixed version.

    OverrideOS takes another OS object and delegates all queries to
    that, except for detection and version, which are fixed by the
    OverrideOS
    """

    def __init__(self, os, version):
        """Setup the OverrideOS with give os object and version string.

        :param OS os: object of class derived from OS that this object
            imitates
        :param str version: version of the imitated OS
        :raises UnsupportedOSError: If os is not valid
        """
        if not isinstance(os, OS):
            raise UnsupportedOSError("Invalid os object to override.")
        # Note: Should OS plugins know which versions they support? Maybe not..
        # if version not in os.get_versions():
        #     raise RuntimeError("Tried to override OS '{0}' with invalid "
        #                        "version '{1}'.".format(os.name(), version))
        self._os = os
        self._version = version

    def is_os(self):
        """Detection for OverrideOS is always `True`."""
        return True

    def get_name(self):
        """Return the delegate's name."""
        return self._os.get_name()

    def get_names(self):
        """Return the delegate's names."""
        return self._os.get_names()

    def get_version(self):
        """Return the saved version from setup."""
        return self._version


class OSSupport(object):

    """OSSupport manages the OS plugins and options such as override_os.

    Can detect the current OS from the installed OS plugins or use the
    override option. Moreover manages options such as disabling specific
    plugins.

    In order to set up, either call :func:`detect_os` or
    :func:`override_os` and subsequently access it with
    :func:`current_os`
    """

    # TODO: Configure to disable specific plugins

    def __init__(self):
        self._os = None
        self._os_plugin_list = get_os_list()

    def get_current_os(self):
        if not self._os:
            self.detect_os()
        return self._os

    def get_os_plugins(self):
        return self._os_plugin_list

    def get_os_plugin_names(self):
        return map(lambda x: x.get_name(), self.get_os_plugins())

    def get_os_plugin(self, name):
        for os in self.get_os_plugins():
            if name == os.get_name():
                return os
        return None

    def override_os(self, name, version):
        os = self.get_os_plugin(name)
        if not os:
            raise UnsupportedOSError(
                "Did not find OS plugin {0} to be used as override.".
                format(name))
        else:
            self._os = OverrideOS(os, version)

    def detect_os(self):
        result = None
        for os in self.get_os_plugins():
            if os.is_os():
                if not result:
                    result = os
                else:
                    warning("OS '{0}' detect, but '{1}' already detected.".
                            format(result.get_name(), os.get_name()))
        if not result:
            raise UnsupportedOSError(
                "None of the OS plugins {0} detected the current OS.".
                format(self.get_os_plugin_names()))
        self._os = result


# TODO: Document that the os plugins should be classes derived from OS
def get_os_list():
    """Return list of OS plugin objects unique by name.

    Load the os plugin classes from entry points, instantiating objects
    and ignoring duplicates (by os.name(), not entry point name).

    :return: list of the loaded plugin objects
    """
    # Note: We ignore the entry point name for now
    os_list = []
    name_set = set()
    for entry_point in pkg_resources.iter_entry_points(group=OS_GROUP):
        os_class = entry_point.load()
        os = os_class()
        name = os.get_name()
        if name in name_set:
            warning("Ignoring duplicate OS plugin '{0}'".format(name))
        else:
            name_set.add(name)
            os_list.append(os)
    return os_list
