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

from __future__ import print_function
from __future__ import unicode_literals

import pkg_resources

from xylem.text import to_str

SPECS_GROUP = 'xylem.specs'


class SpecParsingError(ValueError):

    """Raised when an invalid spec element is encountered while parsing."""

    def __init__(self, msg, related_snippet=None):
        if related_snippet:
            msg += "\n\n" + to_str(related_snippet)
        ValueError.__init__(self, msg)


def list_spec_parsers():
    """List available spec parsers, by name.

    :returns: list of spec parsers by name
    :rtype: :py:obj:`list`(:py:obj:`str`)
    """
    names = []
    for entry_point in pkg_resources.iter_entry_points(group=SPECS_GROUP):
        names.append(entry_point.name)
    return names


def get_spec_parser(name):
    """Return a spec parser of a given name, or None if it is not found.

    :param name: name of the requested spec parser
    :type name: str
    :returns: the requested spec parser, or None if it isn't found
    :rtype: types.FunctionType
    """
    for entry_point in pkg_resources.iter_entry_points(group=SPECS_GROUP):
        if name == entry_point.name:
            return entry_point.load()
