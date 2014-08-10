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

"""Module containing for common base class for OS plugins."""

from __future__ import unicode_literals

from .impl import OS
from .impl import UnsupportedOSVersionError

from xylem.exception import raise_from

from xylem.log_utils import warning

from xylem.config_utils import ConfigDescription
from xylem.config_utils import ConfigValueError
from xylem.config_utils import String
from xylem.config_utils import List
from xylem.config_utils import config_from_parsed_yaml
from xylem.config_utils import config_from_defaults


def version_order_from_list(versions):
    """Return order function from list of verions."""
    # check uniqueness
    assert(len(versions) == len(set(versions)))
    # copy versions since the returned function references it
    versions = versions[:]

    def less(a, b):
        if a not in versions:
            raise UnsupportedOSVersionError(
                "cannot order unknown version '{}'".format(a))
        if b not in versions:
            raise UnsupportedOSVersionError(
                "cannot order unknown version '{}'".format(b))
        return versions.index(a) < versions.index(b)

    return less


class OSBase(OS):

    """Some sensible default implementations of parts of the `OS` interface.

    This class may be used by OS plugins as a base class instead of
    `OS`. Deriving installers must call this class' :meth:`__init__`.

    :ivar ConfigDescription options_description: description of
        structure and types of ``options`` property. Deriving os plugins
        may modify it in their :meth:`__init__`, but not after
        ``options`` has been accessed for the first time. Initialization
        of ``options`` with default values from this description is
        delayed until first access.
    :ivar options: the options property can be set as a dictionary and
        is parsed according to ``options_description`` with default
        values filled in; it is always returned as a
        `xylem.config_utils.ConfigDict` instance.
    """

    def __init__(self):
        self.options_description = ConfigDescription("options")
        self.options_description.add(
            "features", type=List(String), default=[])
        # TODO: encode the available features in the type, something like
        #       List(OneOf("python3", "ruby3"), unique=True)
        self._options = None  # delay loading default config to first access

    @property
    def options(self):
        if self._options is None:
            self._options = config_from_defaults(self.options_description)
        return self._options

    @options.setter
    def options(self, value):
        try:
            self._options = config_from_parsed_yaml(
                value, self.options_description, use_defaults=True)
        except ConfigValueError as e:
            raise_from(ConfigValueError, "invalid options `{}` for os plugin "
                       "'{}'".format(value, self.name), e)
        unused_keys = set(value.keys()) - set(self._options.keys())
        if unused_keys:
            warning("Ignoring the following unknown options for os plugin "
                    "'{}': {}. Known options are: {}.".
                    format(self.name, ", ".join(unused_keys),
                           ", ".join(self._options.keys())))

    @property
    def name(self):
        return self.all_names[0]

    def get_tuple(self):
        return (self.name, self.get_version())

    @property
    def default_installer(self):
        return None

    @property
    def version_less_fn(self):
        return version_order_from_list(self.known_versions)
