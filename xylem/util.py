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

import argparse
import os
import shutil
import sys
import tempfile

from StringIO import StringIO

from xylem import DEFAULT_PREFIX

from xylem.log_utils import enable_debug, enable_verbose
from xylem.terminal_color import disable_ANSI_colors


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


def add_global_arguments(parser):
    from xylem import __version__
    group = parser.add_argument_group('global', description="""\
The XYLEM_PREFIX environment variable sets the path under which xylem operates
on source configurations and caches. If set, the XYLEM_DEBUG environment
variable enables debug messages. These environment variables override the
command line options below.""")
    add = group.add_argument
    add('-d', '--debug', help='enable debug messages',
        action='store_true', default=False)
    add('--pdb', help=argparse.SUPPRESS,
        action='store_true', default=False)
    add('--version', action='version', version=__version__,
        help="prints the xylem version")
    add('--verbose', action='store_true', default=False,
        help="verbose console output")
    add('--no-color', action='store_true', default=False,
        dest='no_color', help=argparse.SUPPRESS)
    add('-p', '--prefix', metavar='XYLEM_PREFIX', default=DEFAULT_PREFIX,
        help="Sets the prefix for finding configs and caches "
             "(overridden by XYLEM_PREFIX environment variable)")
    return parser

_pdb = False


def handle_global_arguments(args):
    global _pdb
    enable_debug(args.debug or 'XYLEM_DEBUG' in os.environ)
    _pdb = args.pdb
    if args.verbose:
        enable_verbose()
    if args.no_color:
        disable_ANSI_colors()
    if 'XYLEM_PREFIX' not in os.environ:
        # FIXME: arg should overwrite env var
        os.environ['XYLEM_PREFIX'] = args.prefix


def print_exc(exc):
    exc_str = ''.join(exc)
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
    return mkdtemp(prefix='bloom_', dir=prefix_dir)
