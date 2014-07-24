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

from ..lookup import lookup

from ..installers import InstallerContext

from ..arguments import add_global_arguments
from ..arguments import handle_global_arguments

from ..util import dump_yaml

from ..terminal_color import ansi

DESCRIPTION = """\
Lookup all rules for a xylem key.
"""


def prepare_arguments(parser):
    parser.add_argument('xylem_key', nargs="+")
    parser.add_argument(
        '--os',
        help="Override detected operating system with os:version pair.")


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

        for key in args.xylem_key:
            result = lookup(
                key, prefix=args.prefix, os_override=ic, compact=True)
            info("Rules for '{0}' on '{1}':\n{2}".
                 format(ansi('cyanf') + key + ansi('reset'),
                        ansi('cyanf') + ic.get_os_string() + ansi('reset'),
                        ansi('yellowf') + dump_yaml(result)[:-1]))
    except (KeyboardInterrupt, EOFError):
        # Note: @William: why EOFError here?
        info('')
        sys.exit(1)


# This describes this command to the loader
definition = dict(
    title='lookup',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments
)
