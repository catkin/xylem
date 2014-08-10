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


from __future__ import unicode_literals

import abc

from xylem.text_utils import to_str
from xylem.text_utils import text_type
from xylem.plugin_utils import PluginBase
from xylem.plugin_utils import load_plugins


# TODO: docstrings for Spec class methods and module


SPEC_GROUP = 'xylem.specs'


def load_spec_plugins(disabled=[]):
    """Return list of spec plugin objects unique by name.

    See :func:`load_plugins`
    """
    return load_plugins("spec", Spec, SPEC_GROUP, disabled)


class Spec(PluginBase):

    """Spec plugin abstract base class.

    Spec plugins are stateless classes such that all functions get are
    their needed parameters passed on every invocation.

    The `data` and `arguments` (e.g. url for the 'rules' spec plugin)
    are managed by the `xylem.sources.database.RulesSource` class in the
    `xylem.sources.database.RulesDatabase`.
    """

    @abc.abstractproperty
    def name(self):
        return

    @abc.abstractproperty
    def version(self):
        return

    @abc.abstractmethod
    def unique_id(self, arguments):
        return

    @abc.abstractmethod
    def load_data(self, arguments):
        return

    @abc.abstractmethod
    def verify_arguments(self, arguments):
        return

    @abc.abstractmethod
    def verify_data(self, data, arguments):
        return

    @abc.abstractmethod
    # TODO: Should is_data_outdated be allowed to block for I/O (net
    # access) or does it need to return quickly?
    def is_data_outdated(self, data, arguments, data_load_time):
        return

    # TODO: possibly make use of URL HEAD request for is_data_outdated
    # to check age or resource. EXAMPLE:
    # import httplib
    # connection = httplib.HTTPConnection(url)
    # connection.request('HEAD', '/')
    # response = connection.getresponse()
    # if response.status == 200:
    #     print "Resource exists"

    @abc.abstractmethod
    def lookup(self, data, xylem_key, installer_context):
        # lookup should return installer_dict with resolved default_installer
        return

    # TODO: is `lookup` allowed to access the net? In general we assume
    # the lookup calls are quick. Also, it must not fail without
    # connectivity

    # TODO: pass optional showing existing rules (the ones from higher
    # priority rules sources, which would get merged with the result of
    # this lookup anyway), such that query can decide if it's answer
    # makes a difference (specifically for rosdistro spec plugin, which
    # can then decide that it does not even need the rosdistro command
    # if the xylem_key has an overriding resolution for 'apt')

    # NOTE: all lookup type queries need to take installer_context
    # argument

    # TODO: needs there be in addition to 'lookup' the capability for
    # spec plugins to dump their data as rules dict? Like lookup for all
    # key/os/versions triples, but might use any_os/any_version. This is
    # needed if we want to be able to dump the whole database for
    # debugging purposes

    # TODO: should there be a method to list the xylem keys defined by
    # this spec plugin? (similar to above todo about dump_db)

    # TODO: how exactly do we support various other queries such as 'who
    # needs' 'depends' 'depends-on' etc

    @abc.abstractmethod
    def keys(self, data, installer_context):
        """Return list of keys defined for current os/version."""


def verify_spec_name(spec_name):
    """Verify that a ``spec_name`` is valid spec name.

    :param str spec_name: spec name
    :raises ValueError: if spec name is invalid
    """
    if not isinstance(spec_name, text_type):
        raise ValueError(
            "expected spec name of string type, but got '{0}' of type '{1}'".
            format(spec_name, to_str(type(spec_name))))
