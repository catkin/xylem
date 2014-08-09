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

import os
import shutil
import sys
import tempfile
import six
import subprocess

from six import StringIO

from .text_utils import to_str


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


# TODO: change this to not update the message in PY2, but manually add
# the `cause` attribute and create a custom exception printer that
# prints is like in PY3. Normally format exceptions without stack trace
# and in this custom manner with "CAUSED BY:". When in debug mode, or
# when catching non XylemError, print with all stack traces like in
# Python 3

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


# TODO: document this soft dependency on pygments, and also add unit
# test for printing exceptions with and without pygments


_pdb = False


def enable_pdb(pdb=True):
    global _pdb
    _pdb = pdb


def pdb_enabled():
    global _pdb
    return _pdb


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
    # Print traceback
    import traceback
    print_exc(traceback.format_exception(type, value, tb))
    if not pdb_enabled() or hasattr(sys, 'ps1') or not sys.stderr.isatty():
        pass
    else:
        # ...then start the debugger in post-mortem mode.
        import pdb
        pdb.set_trace()


sys.excepthook = custom_exception_handler


def pdb_hook():
    if pdb_enabled():
        import pdb
        pdb.set_trace()


def create_temporary_directory(prefix_dir=None):
    """Create a temporary directory and return its location."""
    from tempfile import mkdtemp
    return mkdtemp(prefix='xylem_', dir=prefix_dir)


def read_stdout(cmd):
    """Execute a command and return stdout.

    :param cmd: executable and arguments
    :type cmd: `list` of `str`
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = p.communicate()
    return to_str(std_out)


def is_program_installed(executable_name):
    """Test whether executable is found.

    :param str executable_name: name of the program
    """
    try:
        subprocess.Popen([executable_name],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
        return True
    except OSError:
        return False
