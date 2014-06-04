from .impl import OS
from .os_detect import OS_DEBIAN, OS_OSX, OS_UBUNTU, OsDetect

# TODO: should we import the known installer name strings like "apt"
# from the `installer` module, i.e. APT_INSTALLER, in order to minimize
# the duplication of string constants and future renaming bugs? In
# general we do _not_ assume that the corresponding installer code can
# be referenced from within the os plugins (they might live in
# independent plugins)


class DetectorOS(OS):

    """OS plugin base class for builtin plugins.

    Derived classes should fill in the following member variables:
    - names: list of names
    - detect: Detector object supporting `is_os()`, `get_version()` and
      `get_codename()`
    - use_codename: boolean to decide if numbered version or codename
      should be used
    - installer_priorities: dict of installer_name => priority
    - default_installer_name: name of the desired default installer
    """

    def __init__(self):
        self.names = []
        self.detect = None
        self.use_codename = False
        self.installer_priorities = {}
        self.default_installer_name = ""

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

    def get_installer_priority(self, installer_name):
        return self.installer_priorities.get(installer_name, None)

    def get_default_installer_name(self):
        return self.default_installer_name


class Debian(DetectorOS):

    def __init__(self):
        super(Debian, self).__init__()
        self.names += [OS_DEBIAN]
        self.detect = OsDetect().get_detector(OS_DEBIAN)
        self.use_codename = True
        self.default_installer_name = "apt"
        self.installer_priorities["apt"] = 50
        self.installer_priorities["gem"] = 20
        self.installer_priorities["pip"] = 20


class Ubuntu(Debian):

    def __init__(self):
        super(Ubuntu, self).__init__()
        self.names += [OS_UBUNTU]
        self.detect = OsDetect().get_detector(OS_UBUNTU)


class OSX(DetectorOS):

    def __init__(self):
        super(OSX, self).__init__()
        self.names += [OS_OSX]
        self.detect = OsDetect().get_detector(OS_OSX)
        self.use_codename = True
        self.default_installer_name = "homebrew"
        self.installer_priorities["homebrew"] = 50
        self.installer_priorities["macports"] = 30
        self.installer_priorities["gem"] = 20
        self.installer_priorities["pip"] = 20
