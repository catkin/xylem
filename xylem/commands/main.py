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

from xylem.arguments import add_global_arguments
from xylem.arguments import handle_global_arguments

XYLEM_CMDS_GROUP = 'xylem.commands'


def list_commands():
    commands = []
    for entry_point in pkg_resources.iter_entry_points(group=XYLEM_CMDS_GROUP):
        commands.append(entry_point.name)
    return commands


def load_command_description(command_name):
    for entry_point in pkg_resources.iter_entry_points(group=XYLEM_CMDS_GROUP):
        if entry_point.name == command_name:
            desc = entry_point.load()
            if not isinstance(desc, dict):
                error("Invalid entry point: '{0}', expected dict got '{1}'"
                      .format(entry_point, type(desc)))
                return None
            return desc


def create_subparsers(parser, cmds):
    descs = []
    for cmd in list(cmds):
        desc = load_command_description(cmd)
        if desc is None:
            info("Skipping invalid command '{0}'".format(cmd))
            del cmds[cmds.index(cmd)]
            continue
        descs.append(desc)
    if not descs or not cmds:
        add_global_arguments(parser)
        return
    metavar = '[' + ' | '.join(cmds) + ']'
    subparser = parser.add_subparsers(
        title='commands',
        metavar=metavar,
        description='Call `xylem <command> -h` for help on a specific '
                    'command.',
        dest='cmd'
    )
    for desc in descs:
        cmd_parser = subparser.add_parser(desc['title'],
                                          description=desc['description'])
        cmd_parser = desc['prepare_arguments'](cmd_parser) or cmd_parser
        cmd_parser.set_defaults(func=desc['main'])
        add_global_arguments(cmd_parser)


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
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    add_global_arguments(parser)

    cmds = list_commands()

    create_subparsers(parser, cmds)

    args = parser.parse_args(sysargs)
    handle_global_arguments(args)

    try:
        args.func
    except AttributeError:
        print_usage()
        return
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)
    sys.exit(args.func(args) or 0)
