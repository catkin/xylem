# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from __future__ import unicode_literals

import abc
import six

from ..text_utils import to_str
from ..text_utils import text_type
from ..plugin_utils import PluginBase
from ..plugin_utils import get_plugin_list


SPEC_GROUP = 'xylem.specs'


class Spec(six.with_metaclass(abc.ABCMeta, PluginBase)):

    """Spec plugin abstract base class.

    Spec plugins are stateless classes such that all functions get are
    their needed parameters passed on every invocation.

    The `data` and `arguments` (e.g. url for the 'rules' spec plugin)
    are managed by the `..sources.database.RulesSource` class in the
    `..sources.database.RulesDatabase`.
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


def get_spec_plugin_list():
    """Return list of spec plugin objects unique by name.

    See :func:`get_plugin_list`
    """
    return get_plugin_list("spec", Spec, SPEC_GROUP)


def verify_spec_name(spec_name):
    """Verify that a ``spec_name`` is valid spec name.

    :param str spec_name: spec name
    :raises ValueError: if spec name is invalid
    """
    if not isinstance(spec_name, text_type):
        raise ValueError(
            "expected spec name of string type, but got '{0}' of type '{1}'".
            format(spec_name, to_str(type(spec_name))))
