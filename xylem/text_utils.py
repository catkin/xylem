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

"""Utility module for dealing with unicode/str/bytes in a uniform way.

This has been inspired by parts of the ``kitchen`` package, which is not
py3 compatible to date.
"""

from __future__ import unicode_literals

import six
import traceback

from six.moves import map

text_type = six.text_type


def to_str(obj, encoding='utf-8', errors='replace'):
    """Helper for converting to (unicode) text in py2 and py3."""
    if isinstance(obj, six.text_type):
        return obj
    elif isinstance(obj, six.binary_type):
        return obj.decode(encoding, errors)
    elif isinstance(obj, type):
        return to_str(obj.__name__)
    elif isinstance(obj, Exception):
        string = "".join(traceback.format_exception_only(type(obj), obj))
        if string and string[-1] == '\n':
            string = string[:-1]
        return string
    elif type(obj) is list and all(map(lambda x: isinstance(x, text_type),
                                       obj)):
        # avoid `[u"foo"]` in python2
        return "[" + (", ".join(obj)) + "]"
    else:
        value = None
        if six.PY2:
            try:
                value = obj.__unicode__()
            except (AttributeError, UnicodeError, TypeError):
                pass
        if value is None:
            try:
                value = str(obj)
            except UnicodeError:
                try:
                    value = obj.__str__()
                except (AttributeError, UnicodeError):
                    value = ''
        if not isinstance(value, six.text_type):
            value = six.text_type(value, encoding, errors)
        return value


def to_bytes(obj, encoding='utf-8', errors='replace'):
    """Helper for converting to encoded byte-strings in py2 and py3."""
    if isinstance(obj, six.text_type):
        return obj.encode(encoding, errors)
    if isinstance(obj, six.binary_type):
        return obj
    else:
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = obj.__str__()
            except (AttributeError, UnicodeError):
                value = ''
                if six.PY2:
                    try:
                        value = obj.__unicode__()
                    except (AttributeError, UnicodeError):
                        pass
        if isinstance(value, six.text_type):
            value = value.encode(encoding, errors)
        return value


def type_name(obj):
    """Return name of the type of ``obj``."""
    return to_str(type(obj))
