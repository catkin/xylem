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

"""Provides common utility functions for xylem.

Importing this module will install a custom exception hook if the
current script name is `xylem`.
"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import sys
import tempfile
import subprocess

from six import StringIO

from xylem.text_utils import to_str
from xylem.exception import exc_to_str


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


# TODO: document this soft dependency on pygments, and also add unit
# test for printing exceptions with and without pygments (maybe in
# "install" section of docs)

# TODO: document all hidden debug environment variables and arguments
# (may in "development setion" of docs)s


_pdb = False


def enable_pdb(pdb=True):
    global _pdb
    _pdb = pdb


def pdb_enabled():
    global _pdb
    return _pdb


def print_exc(exc_str):
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
    # Print traceback, ...
    print_exc(exc_to_str(value, tb))
    if not pdb_enabled() or hasattr(sys, 'ps1') or not sys.stderr.isatty():
        pass
    else:
        # ...then start the debugger in post-mortem mode.
        import pdb
        pdb.set_trace()


def set_excepthook():
    sys.excepthook = custom_exception_handler


def running_script_name():
    """Return the name of the currently executing python script."""
    return os.path.basename(os.path.realpath(sys.argv[0]))


if running_script_name() == "xylem":
    set_excepthook()


def create_temporary_directory(prefix_dir=None):
    """Create a temporary directory and return its location."""
    from tempfile import mkdtemp
    return mkdtemp(prefix='xylem_', dir=prefix_dir)


def read_stdout(cmd):
    """Execute a command synchronously and return stdout.

    :param cmd: executable and arguments
    :type cmd: `list` of `str`
    :return str: captured stdout
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = p.communicate()
    return to_str(std_out)


def read_stdout_err(cmd):
    """Execute a command synchronously and return stdout, stderr and exit code.

    :param cmd: executable and arguments
    :type cmd: `list` of `str`
    :return: tuple of stdout, stderr and exit code
    :rtype: ``(str, str, int)``
    """
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = p.communicate()
    return (to_str(std_out), to_str(std_err), p.returncode)


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


def remove_duplicates(seq):
    """Remove duplicates for a list while preserving the order.

    The first occurrence for each item is used.
    """
    items = set()
    return [x for x in seq if not (x in items or items.add(x))]


def indent(text, width, character=' ', exclude_first=False):
    indentation = width * character
    prefix = '' if exclude_first else indentation
    return prefix + ('\n' + indentation).join(text.split('\n'))
