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

from __future__ import unicode_literals

import argparse
import os

from . import DEFAULT_PREFIX
from .util import enable_pdb
from .log_utils import enable_debug

from .log_utils import enable_verbose
from .terminal_color import disable_ANSI_colors


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


def handle_global_arguments(args):
    enable_debug(args.debug or 'XYLEM_DEBUG' in os.environ)
    enable_pdb(args.pdb)
    args.prefix = os.path.expanduser(args.prefix)
    if args.verbose:
        enable_verbose()
    if args.no_color:
        disable_ANSI_colors()
