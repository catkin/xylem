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

from xylem.log_utils import info
from xylem.config import get_config
from xylem.lookup import lookup
from xylem.installers import InstallerContext
from xylem.yaml_utils import dump_yaml
from xylem.terminal_color import ansi

from .main import command_handle_args


DESCRIPTION = """\
Lookup all rules for a xylem key.
"""


def prepare_arguments(parser):
    parser.add_argument('xylem_key', nargs="+")


def prepare_config(description):
    pass


def main(args=None):
    args = command_handle_args(args, definition)
    config = get_config()
    try:
        # TODO: handle multiple keys in one go
        ic = InstallerContext(config)
        for key in args.xylem_key:
            result = lookup(key, compact=True, config=config,
                            installer_context=ic)
            info("Rules for '{}' on '{}':\n{}".
                 format(ansi('cyanf') + key + ansi('reset'),
                        ansi('cyanf') + ic.get_os_string() + ansi('reset'),
                        ansi('yellowf') + dump_yaml(result)[:-1]))
    except (KeyboardInterrupt, EOFError):
        # Note: @William why EOFError here?
        info('')
        sys.exit(1)


# This describes this command to the loader
definition = dict(
    title='lookup',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments,
    prepare_config=prepare_config
)
