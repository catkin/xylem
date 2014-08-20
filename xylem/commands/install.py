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

from xylem.install import install

from xylem.config import get_config

from xylem.log_utils import info
from xylem.log_utils import error

from xylem.exception import exc_to_str

from xylem.util import indent

from .main import command_handle_args


DESCRIPTION = """\
Resolve and install xylem keys.
"""


def prepare_arguments(parser):
    add = parser.add_argument
    add('xylem_key', nargs="+")
    add('--all', action="store_true",
        help="Resolve all keys with resolution for this OS.")
    add('--reinstall', action="store_true")
    add('--dry-run', action="store_true")
    add('--continue-on-error', action="store_true")
    add('--fix-prerequisites', action="store_true")


def prepare_config(description):
    pass


def main(args=None):
    args = command_handle_args(args, definition)
    config = get_config()
    try:
        resolve_errors, install_errors = install(
            args.xylem_key,
            all_keys=args.all,
            config=config,
            reinstall=args.reinstall,
            simulate=args.dry_run,
            continue_on_error=args.continue_on_error,
            fix_prerequisites=args.fix_prerequisites)
        if resolve_errors:
            # error("The following errors occurred during resolution:")
            error("\n".join(indent(exc_to_str(e), 2, exclude_first=True)
                            for _, e in resolve_errors))
        if install_errors:
            # error("The following errors occurred during installation:")
            error("\n".join(indent(exc_to_str(e), 2, exclude_first=True)
                            for e in install_errors))
        if resolve_errors or install_errors:
            sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)

# This describes this command to the loader
definition = dict(
    title='install',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments,
    prepare_config=prepare_config
)
