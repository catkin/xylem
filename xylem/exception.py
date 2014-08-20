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

"""Utilities for error handling in xylem.

All custom exception classes should derive from `XylemError` to allow
catch-all for tools using the xylem API.

Use `raise_from` to chain exceptions in a py2/3 compatible manner.
`exc_to_str` helps to print such chained exceptions in a similar
way to py3, but also allows to not print the tracebacks for more compact
error reporting.
"""


from __future__ import unicode_literals

import six
import sys
import traceback

from xylem.text_utils import type_name


# TODO: adapt custom exception handler to use exc_to_str
# TODO: high level try catch block at command level using exc_to_str


class XylemError(Exception):

    """Common base class for all custom xylem exceptions."""


class XylemInternalError(XylemError):

    """Internal error which may be caused by a programming error."""

    # TODO: custom error message indicating that a bug report should be filed


def type_error_msg(expected_type_name, value, what_for=None):
    """Helper for exception error messages about wrong type."""
    if what_for:
        what_for = ' as ' + what_for
    else:
        what_for = ''
    return "Expected type '{}'{}, but got '{}' of type '{}'.".format(
        expected_type_name, what_for, value, type_name(value))


def _format_no_chain(exc, tb, limit):
    """Helper for `exc_to_str`."""
    if six.PY2:
        return "".join(traceback.format_exception(type(exc), exc, tb, limit))
    else:
        return "".join(traceback.format_exception(type(exc), exc, tb, limit,
                                                  False))


def exc_to_str(exc, tb=False, limit=None, chain=True):
    """Format chained exceptions.

    This helper emulates the way that chained exceptions are formatted
    in py3. See :func:`raise_from` for a helper to raise chained
    exceptions. Note that different from `traceback.format_exception`
    this returns a single string, not a list of strings.

    :param Exception exc: exception to be formatted; maybe chained
    :param tb: current traceback or ``None``, or ``bool``; ``None`` or
        ``False`` means that no tracebacks are included in output
        string; when passing ``True`` the current traceback is looked
        up; otherwise ``tb`` is interpreted as the traceback for ``exc``
    :param limit: limit on the number of frames in the tracebacks
    :param bool chain: indicates if only the current exception is
        formatted or all chained exceptions
    :return str: the exception formatted as one string
    """
    if tb is True:
        if six.PY2:
            _, curr_exc, curr_tb = sys.exc_info()
            if curr_exc is exc:
                tb = curr_tb
            else:
                tb = None
        else:
            tb = exc.__traceback__
    elif tb is False:
        tb = None
    if not chain:
        return _format_no_chain(exc, tb, limit)
    result = []
    next_exc = exc
    next_tb = tb
    while next_exc:
        result.insert(0, _format_no_chain(next_exc, next_tb, limit))
        next_exc = getattr(next_exc, '__cause__', None)
        next_tb = tb and getattr(next_exc, '__traceback__', None)
    cause_text = "The above error was the direct cause of the following:"
    if tb:
        link = "\n{}\n\n".format(cause_text)
    else:
        link = " --- {}\n".format(cause_text)
    return link.join(result).rstrip("\n")


def chain_exception(exc_type, exc_args, from_exc):
    """Helper for creating chained exceptions.

    Like :func:`raise_from`, but returning the exception object instead
    of raising it.
    """
    if six.PY2:
        # emulate the way python3 stores tracebacks in exception objects
        _, curr_exc, curr_tb = sys.exc_info()
        if curr_exc is from_exc:
            from_exc.__traceback__ = curr_tb
    # the following is a py2-syntax-correct equivalent of
    # `raise exc_type(exc_args) from from_exc`
    exc = exc_type(exc_args)
    exc.__cause__ = from_exc
    return exc


def raise_from(exc_type, exc_args, from_exc):
    """Raise new exception directly caused by ``from_exc``.

    This implements exception chaining and makes sure the current
    traceback is stored in ``from_exc``.

    With py3, this is equivalent to ``raise exc_type(exc_args) from
    from_exc`` and with py2 the same thing is emulated manually.

    See :func:`exc_to_str`, which can format chained exceptions raised
    with this helper.
    """
    raise chain_exception(exc_type, exc_args, from_exc)
