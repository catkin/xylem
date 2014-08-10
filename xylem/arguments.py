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

"""Handling of command line arguments shared by multiple xylem commands.

This includes arguments related to the configuration (see
:mod:`xylem.config`).
"""

from __future__ import unicode_literals

import argparse
import pydoc
import os
from six import StringIO

from xylem.config import add_global_config_arguments
from xylem.config import handle_global_config_arguments

from xylem.util import enable_pdb
from xylem.log_utils import enable_verbose
from xylem.log_utils import enable_debug
from xylem.terminal_color import disable_ANSI_colors


class PagerHelpAction(argparse._HelpAction):

    """Custom help action that uses pydoc.pager.

    On ttys this presents a scrollable output akin to ``less``.
    """

    def __init__(self, *args, **kwargs):
        super(PagerHelpAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        output = StringIO()
        parser.print_help(output)
        text = output.getvalue()
        output.close()
        pydoc.pager(text)
        parser.exit()


def add_global_arguments(parser):
    """Add a 'global' argparse group and add comon arguments.

    See :func:`handle_global_arguments`

    :param parser: argparse parser to which the group is added
    """
    from xylem import __version__
    group = parser.add_argument_group(
        'global arguments', description="""By default xylem operates
        with system-wide configuration of sources and cache.  The path
        under which those are found can be set with the XYLEM_PREFIX
        environment variable (or `--prefix` argument).  To instead use
        sources and directories in the user's home directory, make use
        of the `--user- sources` argument.  An alternative mode of
        configuration is by setting the XYLEM_DIR environment variable
        (or `--xylem-dir` argument).  With that, only config files in
        that directory are used and sources/cache folder is local to the
        XYLEM_DIR.  This can be used by third party tools to utilize
        xylem with config/sources/cache in a temporary directory.""")
    add = group.add_argument
    add("-h", "--help", action=PagerHelpAction,
        help="show this help message and exit")
    add('--version', action='version', version=__version__,
        help="print xylem version and exit")
    add('-v', '--verbose', action='store_true',
        help="verbose console output")
    add('-d', '--debug', action='store_true',
        help="""enable debug messages (overwrites the XYLEM_DEBUG
        environment variable)""")
    add('--pdb', action='store_true',
        help=argparse.SUPPRESS,)
    add('--no-color', action='store_true',
        help=argparse.SUPPRESS)
    add_global_config_arguments(group)
    return parser


def handle_global_arguments(args):
    """Handle common arguments

    See :func:`add_global_arguments`

    :param argparse.Namespace args: parsed arguments
    """
    enable_debug(args.debug or 'XYLEM_DEBUG' in os.environ)
    enable_pdb(args.pdb or 'XYLEM_PDB' in os.environ)
    if args.verbose:
        enable_verbose()
    if args.no_color:
        disable_ANSI_colors()
    handle_global_config_arguments(args)
