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

from ..log_utils import info

from ..resolve import resolve
from ..installers import InstallerContext

from ..arguments import add_global_arguments
from ..arguments import handle_global_arguments

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
