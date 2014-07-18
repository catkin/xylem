
from __future__ import unicode_literals

import pkg_resources

from xylem.log_utils import warning
from xylem.exception import InvalidPluginError
from six.moves import map
# TODO: Document the description of how OS plugins look like (maybe in
#       module docstring?)

# COMMENT: @wjwwood: This is good to describe, minimally, in the module
#          docstring, however, the details on how to write one and what
#          all the ramifications and such are can go in a high level
#          document in the developer docs.
OS_GROUP = 'xylem.os'


# TODO: for installers and os, verfiy that the names used are valid and
# are not any of the special values like any_os, any_version,
# default_installer etc


def load_os_plugin(entry_point):
    """Load OS plugin from entry point.

    :param entry_point: entry point object from `pkg_resources`
    :raises InvalidPluginError: if the plugin is not valid
    """
    obj = entry_point.load()
    if not issubclass(obj, OS):
        # TODO: put this test in separate `verify_os_plugin` function
        raise InvalidPluginError(
            "Entry point '{0}' does not describe valid OS plugin. OS "
            "plugins need to be classes derived from `os_support.OS`.".
            format(entry_point.name))
    return obj


def get_os_plugin_list():
    """Return list of OS plugin objects unique by name.

    Load the os plugin classes from entry points, instantiating objects
    and ignoring duplicates (by os.name(), not entry point name).

    :return: list of the loaded plugin objects
    :raises InvalidPluginError: if one of the loaded plugins is invalid
    """
    # Note: We ignore the entry point name for now, maybe use a second
    # name independent from the OS name to allow replacing an builtin OS
    # support plugin with an external one (entry point name, or using a
    # dictionary with name/description/class fields as the entry point
    # instead of the class directly). This could be achieved by the user
    # disabling the builtin plugin in their config (since we allow only
    # one plugin for each OS to be loaded).
    os_list = []
    name_set = set()
    for entry_point in pkg_resources.iter_entry_points(group=OS_GROUP):
        os_class = load_os_plugin(entry_point)
        os = os_class()
        name = os.get_name()
        if name in name_set:
            warning("Ignoring duplicate OS plugin '{0}'".format(name))
        else:
            name_set.add(name)
            os_list.append(os)
    return os_list


class UnsupportedOSError(Exception):

    """
    Operating system unsupported.

    Detected operating system is not supported or could not be
    identified.
    """

    pass


# TODO: Should we enforce explicit inheritance from OS (during plugin
# loading), or should we allow duck typing? COMMENT: We will use ABC for
# now.

# TODO: Should @properties be preferred to all those `get_name` like
# methods? COMMENT: Properties should be nicer and are more idiomatic
# python. Change to use those.

class OS(object):

    # TODO: does it make sense to have a default installer that is
    # not in installer_priorities? If not, check that
    # default_installer appears in installer_priorities.

    # TODO: OS plugins should also specify a list of installers (not
    # just implicitly by query for priority) in order to e.g. inform
    # user (in debug mode) that a specified installer for the current OS
    # is not installed.

    """Abstract OS plugin base class.

    OS plugins should define entry points as classes derived from this.

    Operating systems are described by a list of increasingly specific
    names, where the most specific of those is referred to as the name
    of the operating system. The description furthermore includes a
    operating system version, which can be a version number string or
    code name.

    Operating systems can name their default installer and furthermore
    list additional applicable installer names, each with a number as
    priority (higher number take precedence).
    """

    def is_os(self):
        """Return true if the current OS matches the one this object describes.

        :rtype: bool
        """
        raise NotImplementedError()

    def get_name(self):
        """Get the most specific name of the described operating system.

        :rtype: string
        """
        raise NotImplementedError()

    def get_names(self):
        """Get a list of names describing this operating system.

        :return: list of increasingly specific os names
        :rtype: list of strings
        """
        raise NotImplementedError()

    def get_version(self):
        """Get version of this operating system.

        :rtype: string
        """
        raise NotImplementedError()

    def get_tuple(self):
        """Get (name,version) tuple.

        :rtype: (str,str)
        """
        return self.get_name(), self.get_version()

    def get_installer_priority(self, installer_name):
        """Get priority of installer as described by OS plugin.

        :param str installer_name: name of installer in question
        :return: priority of this installer if the os defines it, else None
        :rtype: number or None
        """
        raise NotImplementedError()

    def get_default_installer_name(self):
        """Get name of default installer as described by OS plugin.

        :rtype: str
        """
        raise NotImplementedError()
        # Note: should we remove the default package manager all together?


class OverrideOS(OS):

    """Special OS class that acts as a proxy to another OS with fixed version.

    OverrideOS takes another OS object and delegates all queries to
    that, except for detection and version, which are fixed by the
    OverrideOS.
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
        self.os = os
        self.version = version

    def is_os(self):
        """Detection for OverrideOS is always `True`."""
        return True

    def get_name(self):
        """Return the delegate's name."""
        return self.os.get_name()

    def get_names(self):
        """Return the delegate's names."""
        return self.os.get_names()

    def get_version(self):
        """Return the saved version from setup."""
        return self.version

    def get_installer_priority(self, installer_name):
        """Return the delegate's installer priority."""
        return self.os.get_installer_priority(installer_name)

    def get_default_installer_name(self):
        """Return the delegate's default installer."""
        return self.os.get_default_installer_name()


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
        self._os_plugin_list = get_os_plugin_list()

    def get_current_os(self):
        """Return OS object of current OS.

        Detect current OS if not yet detected or overridden.

        :rtype: OS
        :raises UnsupportedOSError: If OS is not set and cannot be
            detected.
        """
        if not self._os:
            self.detect_os()
        return self._os

    def get_os_plugins(self):
        """Return list of is plugin objects."""
        return self._os_plugin_list

    def get_os_plugin_names(self):
        """Return list of known/configured os names."""
        return map(lambda x: x.get_name(), self.get_os_plugins())

    def get_os_plugin(self, name):
        """Return os plugin object for given os name or None if not known."""
        for os in self.get_os_plugins():
            if name == os.get_name():
                return os
        return None

    def get_default_installer_names(self):
        """Return mapping of os name to default installer for all os."""
        return {os.get_name(): os.get_default_installer_name()
                for os in self.get_os_plugins()}

    def override_os(self, os_tuple):
        """Override to to (name,version) tuple.

        A plugin with ``name`` must be installed.

        :raises UnsupportedOSError: if specified os name is not known
        """
        if os_tuple:
            name, version = os_tuple
            os = self.get_os_plugin(name)
            if not os:
                raise UnsupportedOSError(
                    "Did not find OS plugin {0} to be used as override.".
                    format(name))
            else:
                self._os = OverrideOS(os, version)

    def detect_os(self):
        """Detects and sets the current OS.

        The first OS plugin that returns ``True`` for :meth:`OS.is_os`
        is the detected one. If multiple os plugins would accept the
        current OS, a warning is printed to the user.

        :raises UnsupportedOSError: If no OS plugin accepts the current OS
        """
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
