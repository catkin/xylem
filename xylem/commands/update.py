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

from xylem.log_utils import info

from xylem.update import update

from xylem.arguments import add_global_arguments
from xylem.arguments import handle_global_arguments

DESCRIPTION = """\
Updates the xylem cache according to the source config files.

If no source config files are found under the current XYLEM_PREFIX, at
<prefix>/etc/xylem/sources.list.d, then the default, internal source
configs are used. The cache is always stored under the XYLEM_PREFIX in
the <prefix>/var/caches/xylem directory.
"""


def prepare_arguments(parser):
    parser.add_argument('-n', '--dry-run', action='store_true', default=False,
                        help="Shows affect of an update only")


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
        update(prefix=args.prefix, dry_run=args.dry_run)
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)


# This describes this command to the loader
definition = dict(
    title='update',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments
)
