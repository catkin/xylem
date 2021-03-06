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

"""
Common tools for running tests
"""

from __future__ import print_function
from __future__ import unicode_literals

import functools
import os
import shlex
import shutil
import sys
import tempfile

from StringIO import StringIO

from subprocess import Popen, PIPE, CalledProcessError


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


def in_temporary_directory(f):
    @functools.wraps(f)
    def decorated(*args, **kwds):
        with temporary_directory() as directory:
            from inspect import getargspec
            # If it takes directory of kwargs and kwds does already have
            # directory, inject it
            if 'directory' not in kwds and 'directory' in getargspec(f)[0]:
                kwds['directory'] = directory
            return f(*args, **kwds)
    decorated.__name__ = f.__name__
    return decorated


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


def user_cd(cmd, **kwargs):
    """
    Used in system tests to emulate a user changing directories

    Used in place of user('cd <new_directory>')
    """
    if type(cmd) is str:
        assert cmd is not '', "no arguments passed to cd, not allowed"
        cmd = cmd.split()
    new_directory = cmd[0]
    assert os.path.exists(new_directory), \
        "user tried to cd to '" + new_directory + "' which does not exist"
    os.chdir(new_directory)
    return 0


def user_echo(cmd, **kwargs):
    """
    Used to emulate the user echoing something even to a file with >>
    """
    assert type(cmd) is str, "user echo only takes str for the cmd argument"
    cmd = shlex.split(cmd)
    if len(cmd) == 1:
        print(cmd[0])
    elif len(cmd) == 3 and cmd[1] in ['>>', '>']:
        # echo into somefile
        assert not os.path.isdir(cmd[2]), \
            "user tried to echo into a directory: '" + cmd[2] + "'"
        if cmd[1] == '>>':
            mode = 'a'
        else:
            mode = 'w+'
        with open(cmd[2], mode) as f:
            f.write(cmd[0])
    return 0


def user_mkdir(cmd, **kwargs):
    """
    Used in system tests to emulte a user creating a directory
    """
    if type(cmd) is str:
        assert cmd is not '', "no arguments passed to mkdir, not allowed"
        cmd = cmd.split()
    if len(cmd) == 2:
        assert '-p' in cmd, "two args to mkdir, neither is '-p', not allowed"
        cmd.remove('-p')
        mkdir_cmd = os.makedirs
    else:
        mkdir_cmd = os.mkdir
    new_dir = cmd[0]
    assert not os.path.exists(new_dir), \
        "directory '" + new_dir + "' already exists"
    mkdir_cmd(new_dir)
    return 0


def user_touch(cmd, **kwargs):
    """
    Used to emulat a user touching a file
    """
    assert not os.path.exists(cmd), \
        "user tried to touch a file '" + cmd + "' but it exists"
    if os.path.exists(cmd):
        os.utime(cmd, None)
    else:
        open(cmd, 'w').close()


_special_user_commands = {
    'cd': user_cd,
    'echo': user_echo,
    'mkdir': user_mkdir,
    'touch': user_touch
}


def user(cmd, directory=None, auto_assert=True, return_io=False,
         bash_only=False, silent=True):
    """Used in system tests to emulate a user action"""
    if type(cmd) in [list, tuple]:
        cmd = ' '.join(cmd)
    if not bash_only:
        # Handle special cases
        for case in _special_user_commands:
            if cmd.startswith(case):
                cmd = ''.join(cmd.split(case)[1:]).strip()
                return _special_user_commands[case](
                    cmd,
                    directory=directory,
                    auto_assert=auto_assert,
                    return_io=return_io,
                    silent=silent
                )
    ret = -1
    try:
        p = Popen(cmd, shell=True, cwd=directory, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        ret = p.returncode
    except CalledProcessError as err:
        ret = err.returncode
    if not silent:
        print(out, file=sys.stdout, end='')
        print(err, file=sys.stderr, end='')
    if auto_assert:
        assert ret == 0, \
            "user command '" + cmd + "' returned " + str(p.returncode)
    if return_io:
        return ret, out, err
    return ret
