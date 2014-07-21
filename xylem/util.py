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
import subprocess

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


# use this utility function throughout to make sure the custom
# constructors for unicode handling are loaded
def load_yaml(data):
    """Parse a unicode string containing yaml.

    This calls ``yaml.load(data)`` but makes sure unicode is handled correctly.

    See :func:`yaml.load`.

    :raises yaml.YAMLError: if parsing fails"""

    class MyLoader(yaml.SafeLoader):
        def construct_yaml_str(self, node):
            # Override the default string handling function
            # to always return unicode objects
            return self.construct_scalar(node)

    MyLoader.add_constructor(
        'tag:yaml.org,2002:str', MyLoader.construct_yaml_str)

    return yaml.load(data, Loader=MyLoader)


def dump_yaml(data, inline=False):
    """Dump data to unicode string."""

    class MyDumper(yaml.SafeDumper):
        def ignore_aliases(self, _data):
            return True

        def represent_sequence(self, tag, data, flow_style=False):
            # represent lists inline
            return yaml.SafeDumper.represent_sequence(
                self, tag, data, flow_style=True)

        def represent_none(self, data):
            return self.represent_scalar('tag:yaml.org,2002:null', '')

    MyDumper.add_representer(type(None), MyDumper.represent_none)

    result = yaml.dump(data,
                       Dumper=MyDumper,
                       # TODO: use this for inline==True ??
                       # default_style=None,
                       default_flow_style=False,
                       allow_unicode=True,
                       indent=2,
                       width=10000000)

    return result


def read_stdout(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = p.communicate()
    return to_str(std_out)
