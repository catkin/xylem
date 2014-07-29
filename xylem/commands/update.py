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

from ..update import update
from ..log_utils import info
from .main import command_handle_args


DESCRIPTION = """\
Updates the xylem cache according to the source config files.

Location for sources files and cache are determined from the
configuration.
"""


def prepare_arguments(parser):
    # TODO: do we need this `--dry-run` argument? What about consistency
    # with `install --simulate`
    parser.add_argument('-n', '--dry-run', action='store_true', default=False,
                        help="shows affect of an update only")


def prepare_config(description):
    pass


def main(args=None):
    args = command_handle_args(args, definition)
    try:
        update(dry_run=args.dry_run)
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)


# This describes this command to the loader
definition = dict(
    title='update',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments,
    prepare_config=prepare_config
)
