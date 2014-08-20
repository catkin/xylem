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

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from xylem.text_utils import to_str
from xylem.text_utils import to_bytes

from xylem.terminal_color import ansi
from xylem.terminal_color import enable_ANSI_colors

_ansi = {}
_debug = False
_verbose = False

# Default to ansi colors on
enable_ANSI_colors()


def enable_verbose(state=True):
    """En- or disable printing verbose output to console."""
    global _verbose
    _verbose = state


def is_verbose():
    """Return true if xylem is set to verbose console output."""
    global _verbose
    return _verbose


def enable_debug(state=True):
    """En- or disable printing debug output to console."""
    global _debug
    _debug = state


def is_debug():
    """Return true if xylem is set to debug console output."""
    global _debug
    return _debug


# Default to debug off or on if in the environment
enable_debug('XYLEM_DEBUG' in os.environ)


def debug(msg, file=None, *args, **kwargs):
    """Print debug to console or file.

    Works like :func:`print`, optionally uses terminal colors and
    tries to handle unicode correctly by encoding to ``utf-8`` before
    printing. Can be enabled or disabled with
    :func:`enable_debug`.
    """
    file = file if file is not None else sys.stderr
    global _debug
    msg = to_str(msg)
    msg = ansi('greenf') + msg + ansi('reset')
    if is_debug():
        print(to_bytes(msg), file=file, *args, **kwargs)
    return msg


def info(msg, file=None, *args, **kwargs):
    """Print info to console or file.

    Works like :func:`print`, optionally uses terminal colors and
    tries to handle unicode correctly by encoding to ``utf-8`` before
    printing.
    """
    file = file if file is not None else sys.stdout
    msg = to_str(msg)
    msg = msg + ansi('reset')  # Assume that msg might contain colors
    print(to_bytes(msg), file=file, *args, **kwargs)
    return msg


def warning(msg, file=None, *args, **kwargs):
    """Print warning to console or file.

    Works like :func:`print`, optionally uses terminal colors and
    tries to handle unicode correctly by encoding to ``utf-8`` before
    printing. Can be enabled or disabled with
    :func:`enable_debug`.
    """
    file = file if file is not None else sys.stderr
    msg = to_str(msg)
    msg = ansi('yellowf') + msg + ansi('reset')
    print(to_bytes(msg), file=file, *args, **kwargs)
    return msg


def error(msg, file=None, exit=False, *args, **kwargs):
    """Print error statement and optionally exit.

    Works like :func:`print`, optionally uses terminal colors and
    tries to handle unicode correctly by encoding to ``utf-8`` before
    printing.
    """
    file = file if file is not None else sys.stderr
    msg = to_str(msg)
    msg = ansi('redf') + ansi('boldon') + msg + ansi('reset')
    if exit:
        sys.exit(to_bytes(msg))
    print(to_bytes(msg), file=file, *args, **kwargs)
    return msg


def info_v(msg, file=None, *args, **kwargs):
    """Like :func:`info`, but only if :func:`is_verbose` is `True`.

    Prints to stderr by default.
    """
    if is_verbose():
        return info(msg, file=(file or sys.stderr), *args, **kwargs)
    else:
        return None
