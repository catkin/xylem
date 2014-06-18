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

import os
import sys

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


# Default to debug off or on if in the environment
enable_debug('XYLEM_DEBUG' in os.environ)


def debug(msg, file=None, *args, **kwargs):
    """Print debug to console or file.

    Works like :py:obj:`print` and optionally uses terminal colors. Can
    be enabled or disabled with :func:`enable_debug`.
    """
    file = file if file is not None else sys.stdout
    global _debug
    msg = str(msg)
    msg = ansi('greenf') + msg + ansi('reset')
    if _debug:
        print(msg, file=file, *args, **kwargs)
    return msg


def info(msg, file=None, *args, **kwargs):
    """Print info to console or file.

    Works like :py:obj:`print` and optionally uses terminal colors.
    """
    file = file if file is not None else sys.stdout
    msg = str(msg)
    print(msg, file=file, *args, **kwargs)
    return msg


def warning(msg, file=None, *args, **kwargs):
    """Print warning to console or file.

    Works like :py:obj:`print` and optionally uses terminal colors.
    """
    file = file if file is not None else sys.stdout
    msg = str(msg)
    msg = ansi('yellowf') + msg + ansi('reset')
    print(msg, file=file, *args, **kwargs)
    return msg


def error(msg, file=None, exit=False, *args, **kwargs):
    """Print error statement and optionally exit.

    Works like :py:obj:`print` and optionally uses terminal colors.
    """
    file = file if file is not None else sys.stdout
    msg = str(msg)
    msg = ansi('redf') + ansi('boldon') + msg + ansi('reset')
    if exit:
        sys.exit(msg)
    print(msg, file=file, *args, **kwargs)
    return msg
