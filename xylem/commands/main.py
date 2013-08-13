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

import argparse
import sys
import pkg_resources

from xylem.log_utils import error
from xylem.log_utils import info

from xylem.util import add_global_arguments
from xylem.util import handle_global_arguments

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
        description='Call `xylem <command> -h` for help on a specific command.',
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
        description="xylem is a package manager abstraction tool."
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
