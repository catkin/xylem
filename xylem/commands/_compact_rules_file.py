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
import os

from ..sources.rules_dict import verify_rules_dict

from ..specs.rules import expand_rules
from ..specs.rules import compact_rules

from ..os_support import OSSupport
from ..log_utils import info

from ..text_utils import to_str
from ..text_utils import to_bytes

from ..util import load_yaml
from ..util import dump_yaml
from ..util import add_global_arguments
from ..util import handle_global_arguments

DESCRIPTION = """\
Compact a rules file.
"""


def prepare_arguments(parser):
    add = parser.add_argument
    add('rules_file', metavar='rules-file', help="Path to rules file.")
    add('-w', '--write', action="store_true",
        help="Change the content of the original file instead of printing the "
             "compacted file.")


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
        # prepare arguments
        filepath = os.path.abspath(os.path.expanduser(args.rules_file))

        # parse rules file
        with open(filepath, 'rb') as f:
            data = to_str(f.read())
        rules = load_yaml(data)
        rules = expand_rules(rules)
        verify_rules_dict(rules)

        # compact rules
        compacted = compact_rules(
            rules, OSSupport().get_default_installer_names())

        # output result
        dump = dump_yaml(compacted)
        if args.write:
            with open(filepath, 'wb') as f:
                f.write(to_bytes(dump))
        else:
            info(dump)
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)


# This describes this command to the loader
definition = dict(
    title='_compact_rules_file',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments
)
