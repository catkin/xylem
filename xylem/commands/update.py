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

from __future__ import print_function

import argparse
import sys

from xylem.log_utils import info

from xylem.update import update

from xylem.util import add_global_arguments
from xylem.util import handle_global_arguments

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
        update(dry_run=args.dry_run)
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)


# This describes this command to the loader
description = dict(
    title='update',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments
)
