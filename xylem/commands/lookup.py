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

from ..lookup import lookup

from ..installers import InstallerContext

from ..util import add_global_arguments
from ..util import handle_global_arguments
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
