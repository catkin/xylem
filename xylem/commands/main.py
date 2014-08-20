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
import sys
import pkg_resources

from xylem.log_utils import error
from xylem.log_utils import info
from xylem.log_utils import ansi
from xylem.log_utils import is_debug

from xylem.arguments import add_global_arguments
from xylem.arguments import handle_global_arguments

from xylem.config import get_config_description
from xylem.config import add_config_arguments
from xylem.config import handle_config_arguments

from xylem.config_utils import ConfigHelpFormatter

from xylem.text_utils import type_name

from xylem.exception import exc_to_str
from xylem.exception import XylemError
from xylem.exception import XylemInternalError

from xylem.util import print_exc

XYLEM_CMDS_GROUP = 'xylem.commands'


def list_commands():
    commands = []
    for entry_point in pkg_resources.iter_entry_points(group=XYLEM_CMDS_GROUP):
        commands.append(entry_point.name)
    return commands


def load_command_definition(command_name):
    for entry_point in pkg_resources.iter_entry_points(group=XYLEM_CMDS_GROUP):
        if entry_point.name == command_name:
            defi = entry_point.load()
            if not isinstance(defi, dict):
                error("Invalid entry point: '{0}', expected dict got '{1}'"
                      .format(entry_point, type_name(defi)))
                return None
            return defi


def create_command_parser(command_defi, constructor, parser_title=False):
    args = [str(command_defi['title'])] if parser_title else []
    parser = constructor(*args,
                         description=command_defi['description'],
                         add_help=False,
                         formatter_class=ConfigHelpFormatter)
    parser = command_defi['prepare_arguments'](parser) or parser
    parser.set_defaults(func=command_defi['main'])
    command_defi['prepare_config'](get_config_description())
    add_config_arguments(parser)
    add_global_arguments(parser)


def command_handle_args(args, definition):
    """Helper for commands."""
    if args is None:
        parser = create_command_parser(definition, argparse.ArgumentParser)
        args = parser.parse_args()
        handle_global_arguments(args)
        handle_config_arguments(args)
    return args


def create_subparsers(parser, cmds):
    defis = []
    for cmd in list(cmds):
        defi = load_command_definition(cmd)
        if defi is None:
            error("skipping invalid command '{0}'".format(cmd))
            del cmds[cmds.index(cmd)]
            continue
        defis.append(defi)
    if not defis or not cmds:
        return
    public_cmds = [c for c in cmds if not c.startswith("_")]
    metavar = '[' + ' | '.join(public_cmds) + ']'
    subparser = parser.add_subparsers(
        title='commands',
        metavar=metavar,
        description="""Call `xylem <command> -h` for help on a specific
        command.""",
        dest='cmd'
    )
    for defi in defis:
        create_command_parser(defi, subparser.add_parser, parser_title=True)


# FIXME: Merge with help message somehow and decide when to print
def print_usage():
    info("xylem is a package manager abstraction tool.")
    info("")
    info("Here are some examples of how to use xylem:")
    info("  > xylem resolve boost")
    info("  libboost")
    info("")
    info("  > xylem update")
    info("")
    info("  > xylem install boost")
    info("")
    info("For complete list of options run `xylem -h`")


def main(sysargs=None):
    parser = argparse.ArgumentParser(
        description="xylem is a package manager abstraction tool.",
        add_help=False,
        formatter_class=ConfigHelpFormatter
    )
    add_config_arguments(parser)
    add_global_arguments(parser)

    cmds = list_commands()
    create_subparsers(parser, cmds)

    args = parser.parse_args(sysargs)
    handle_global_arguments(args)
    handle_config_arguments(args)

    # FIXME: the following logic and error handling
    try:
        args.func
        result = args.func(args)
    except XylemError as e:
        if is_debug() or isinstance(e, XylemInternalError):
            print_exc(exc_to_str(e, tb=True, chain=True))
        else:
            error(exc_to_str(e, tb=False, chain=True))
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)
    sys.stdout.write(ansi('reset'))
    sys.exit(result or 0)
