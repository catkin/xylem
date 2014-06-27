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

"""Provides common utility functions for xylem."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os
import shutil
import sys
import tempfile
import six
import yaml

from six import StringIO

from . import DEFAULT_PREFIX
from .text_utils import to_str
from .log_utils import enable_debug, enable_verbose
from .terminal_color import disable_ANSI_colors


class change_directory(object):
    def __init__(self, directory=''):
        self.directory = directory
        self.original_cwd = None

    def __enter__(self):
        self.original_cwd = os.getcwd()
        os.chdir(self.directory)
        return self.directory

    def __exit__(self, exc_type, exc_value, traceback):
        if self.original_cwd and os.path.exists(self.original_cwd):
            os.chdir(self.original_cwd)


class redirected_stdio(object):
    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = out = StringIO()
        sys.stderr = err = StringIO()
        return out, err

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class temporary_directory(object):
    def __init__(self, prefix=''):
        self.prefix = prefix

    def __enter__(self):
        self.original_cwd = os.getcwd()
        self.temp_path = tempfile.mkdtemp(prefix=self.prefix)
        os.chdir(self.temp_path)
        return self.temp_path

    def __exit__(self, exc_type, exc_value, traceback):
        if self.temp_path and os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)
        if self.original_cwd and os.path.exists(self.original_cwd):
            os.chdir(self.original_cwd)


def raise_from(exc_type, exc_args, from_exc):
    """Raise new exception directly caused by ``from_exc``.

    On py3, this is equivalent to ``raise exc_type(exc_args) from
    from_exc`` and on py2 the messages are composed manually to retain
    the arguments of ``from_exc`` as well as the stack trace.
    """
    if six.PY2:
        exc_args = to_str(exc_args)
        exc_args += "\nCAUSED BY:\n"
        exc_args += to_str(type(from_exc)) + ": " + to_str(from_exc)
        # we need to use `exec` else py3 throws syntax error
        exec("raise exc_type, exc_type(exc_args), sys.exc_info()[2]")
    else:
        # the following is a py2-syntax-correct equivalent of
        # `raise exc_type(exc_args) from from_exc`
        exc = exc_type(exc_args)
        exc.__cause__ = from_exc
        raise exc


def add_global_arguments(parser):
    from xylem import __version__
    group = parser.add_argument_group('global', description="""\
The XYLEM_PREFIX environment variable sets the path under which xylem
operates on source configurations and caches, which can be overwritten
by the --prefix argument. If set, the XYLEM_DEBUG environment variable
enables debug messages.""")
    add = group.add_argument
    add('-d', '--debug', help='enable debug messages',
        action='store_true', default=False)
    add('--pdb', help=argparse.SUPPRESS,
        action='store_true', default=False)
    add('--version', action='version', version=__version__,
        help="prints the xylem version")
    add('-v', '--verbose', action='store_true', default=False,
        help="verbose console output")
    add('--no-color', action='store_true', default=False,
        dest='no_color', help=argparse.SUPPRESS)
    add('-p', '--prefix', metavar='XYLEM_PREFIX',
        default=os.environ.get('XYLEM_PREFIX', DEFAULT_PREFIX),
        help="Sets the prefix for finding configs and caches. "
             "The default is either '/' or, if set, the XYLEM_PREFIX "
             "environment variable.")
    return parser

_pdb = False


def handle_global_arguments(args):
    global _pdb
    enable_debug(args.debug or 'XYLEM_DEBUG' in os.environ)
    _pdb = args.pdb
    args.prefix = os.path.expanduser(args.prefix)
    if args.verbose:
        enable_verbose()
    if args.no_color:
        disable_ANSI_colors()


# TODO: document this soft dependency on pygments, and also add unit
# test for printing exceptions with and without pygments

def print_exc(formated_exc):
    exc_str = ''.join(formated_exc)
    try:
        from pygments import highlight
        from pygments.lexers import PythonTracebackLexer
        from pygments.formatters import TerminalFormatter

        exc_str = highlight(exc_str, PythonTracebackLexer(),
                            TerminalFormatter())
    except ImportError:
        pass
    print(exc_str, file=sys.stderr)


def custom_exception_handler(type, value, tb):
    global _pdb
    # Print traceback
    import traceback
    print_exc(traceback.format_exception(type, value, tb))
    if not _pdb or hasattr(sys, 'ps1') or not sys.stderr.isatty():
        pass
    else:
        # ...then start the debugger in post-mortem mode.
        import pdb
        pdb.set_trace()


sys.excepthook = custom_exception_handler


def pdb_hook():
    global _pdb
    if _pdb:
        import pdb
        pdb.set_trace()


def create_temporary_directory(prefix_dir=None):
    """Create a temporary directory and return its location."""
    from tempfile import mkdtemp
    return mkdtemp(prefix='xylem_', dir=prefix_dir)


def construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)


yaml.Loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)
yaml.SafeLoader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)


# use this utility function throughout to make sure the custom
# constructors for unicode handling are loaded
def load_yaml(data):
    """Parse a unicode string containing yaml.

    This calls ``yaml.load(data)`` but makes sure unicode is handled correctly.

    See :func:`yaml.load`.

    :raises yaml.YAMLError: if parsing fails"""
    return yaml.load(data)
