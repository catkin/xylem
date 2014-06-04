from .impl import OS
from .os_detect import OS_DEBIAN, OS_OSX, OS_UBUNTU, OsDetect


class Debian(OS):

    def __init__(self):
        self.names = [OS_DEBIAN]
        self.detect = OsDetect().get_detector(OS_DEBIAN)
        self.use_codename = True


class Ubuntu(Debian):

    def __init__(self):
        self.names = [OS_DEBIAN, OS_UBUNTU]
        self.detect = OsDetect().get_detector(OS_UBUNTU)
        self.use_codename = True


class OSX(OS):

    def __init__(self):
        self.names = [OS_OSX]
        self.detect = OsDetect().get_detector(OS_OSX)
        self.use_codename = True
