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

from __future__ import unicode_literals

import argparse
import sys

from ..log_utils import info

from ..resolve import resolve
from ..installers import InstallerContext

from ..util import add_global_arguments
from ..util import handle_global_arguments

from ..text_utils import to_str

from ..terminal_color import ansi
from six.moves import map

DESCRIPTION = """\
Lookup a xylem key and resolve to unique, parsed rule based on
priorities.
"""


def prepare_arguments(parser):
    add = parser.add_argument
    add('xylem_key', nargs="*")
    add('--os',
        help="Override detected operating system with os:version pair.")
    add('--show-trumped', action="store_true",
        help="Show all possible resolutions for key, also for "
             "trumped installers.")
    add('--all', action="store_true",
        help="Resolve all keys with resolution for this OS.")
    add('--show-priority', action="store_true",
        help="Show priority of installer.")
    add('--show-default-installer', action="store_true",
        help="Show installer even if it is the default installer.")
    # TODO: add 'show-depends' option


# TODO: move this to os_support package
def parse_os_tuple(os_arg):
    if ':' in os_arg:
        os_tuple = tuple(os_arg.split(':', 1))
    else:
        os_tuple = os_arg, ''
    return os_tuple


def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(
            description=DESCRIPTION
        )
        prepare_arguments(parser)
        add_global_arguments(parser)
        args = parser.parse_args()
        handle_global_arguments(args)
    try:
        os_tuple = None
        if args.os:
            os_tuple = parse_os_tuple(args.os)

        ic = InstallerContext(os_override=os_tuple)
        default_installer_name = ic.get_default_installer_name()

        results = resolve(args.xylem_key,
                          prefix=args.prefix,
                          os_override=ic,
                          all_keys=args.all)

        for key, result in results:

            if not args.show_trumped:
                result = [result[0]]
                # TODO: this should be done inside `resolve`

                # TODO: Error if single resolution is requested, but
                # highest priority occurs multuple times (macports vs
                # homebrew)

            for priority, installer_name, resolutions in result:
                if installer_name != default_installer_name or \
                        args.show_default_installer or \
                        args.show_priority:
                    if args.show_priority:
                        installer_string = "{0} ({1}) : ".format(
                            installer_name, priority)
                    else:
                        installer_string = "{0} : ".format(installer_name)
                else:
                    installer_string = ""

                resolution_string = ', '.join(map(to_str, resolutions))

                info("{0} --> {1}{2}".
                     format(ansi("cyanf") + key + ansi("reset"),
                            ansi("bluef") + installer_string,
                            ansi("yellowf") + resolution_string))
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)


# This describes this command to the loader
definition = dict(
    title='resolve',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments
)
