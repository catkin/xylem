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

import sys
import os

from ..specs.rules_dict import verify_rules_dict

from ..specs.rules import expand_rules
from ..specs.rules import compact_rules

from ..os_support import OSSupport
from ..log_utils import info

from ..text_utils import to_str
from ..text_utils import to_bytes

from ..yaml_utils import load_yaml
from ..yaml_utils import dump_yaml

from .main import command_handle_args


DESCRIPTION = """\
Parse a rules file and print it in canonical compact notation.

This is a utility command intended for rules file maintenance.
"""


def prepare_arguments(parser):
    add = parser.add_argument
    add('rules_file', metavar='rules-file', help="Path to rules file.")
    add('-w', '--write', action="store_true",
        help="Change the content of the original file instead of printing the "
             "compacted file.")


def prepare_config(description):
    pass


def main(args=None):
    args = command_handle_args(args, definition)
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
    prepare_arguments=prepare_arguments,
    prepare_config=prepare_config
)
