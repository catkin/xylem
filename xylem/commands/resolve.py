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

from six.moves import map

from xylem.log_utils import info
from xylem.log_utils import error

from xylem.resolve import resolve
from xylem.installers import InstallerContext

from xylem.text_utils import to_str

from xylem.terminal_color import ansi

from xylem.config import get_config

from xylem.exception import exc_to_str

from xylem.util import indent

from .main import command_handle_args


DESCRIPTION = """\
Lookup xylem keys and resolve to unique, parsed rules.
"""


# TODO: Abstract a way to add all arguments related to passing a list of
#       xylem keys to verbs. This is then also how the planned "frontend
#       plugins" hook into (for example the ros-package parsing
#       frontend, e.g. crawling a workspace folder with packages)


def prepare_arguments(parser):
    add = parser.add_argument
    # For now we make xylem_key required. The `--all` option is just
    # experimental and for debugging. I'm don't think there is a good
    # reason to not remove `--all` eventually. A unified concept for all
    # verbs taking "xylem_keys" as arguments is still TODO, but
    # something to add instead of `--all` might be allowing wildcards in
    # keys. I.e. what is now `--all` would then be `*`, but more
    # sophisticated uses are possible, e.g. `xylem resolve python-*`. We
    # have to check how this interferes with bash-globbing.
    add('xylem_key', nargs="+")
    add('--all', action="store_true",
        help="Resolve all keys with resolution for this OS.")

    # I would actually not have the `--show-trumped` option at all for
    # now. The lookup verb can show you all available installers.
    # add('--show-trumped', action="store_true",
    #     help="Show all possible resolutions for key, also for "
    #          "trumped installers.")
    add('--show-default-installer', action="store_true",
        help="""Show installer in the output even if it is the default
        installer.""")

    # TODO: add 'show-depends' option, showing the dependencies of a key
    #       in the output. Maybe like this:
    #
    #           boost (deps: foo, bar) --> homebrew: boost --with-python

    # TODO: even better than the above 'show-depends' would be a way to
    #       to format the dependency DAG


def prepare_config(description):
    pass


def main(args=None):
    args = command_handle_args(args, definition)
    config = get_config()
    try:
        ic = InstallerContext(config=config)
        default_installer_name = ic.get_default_installer_name()
        results, errors = resolve(args.xylem_key, all_keys=args.all,
                                  config=config, installer_context=ic)
        if errors:
            error("The following errors occurred during resolution:")
            error("\n\n".join(
                indent(exc_to_str(e), 2) for _, e in errors))
        for key, (installer_name, resolutions) in results:
            if installer_name != default_installer_name or \
                    args.show_default_installer:
                installer_string = "{0}: ".format(installer_name)
            else:
                installer_string = ""
            resolution_string = ', '.join(map(to_str, resolutions))
            info("{0} --> {1}{2}".
                 format(ansi("cyanf") + key + ansi("reset"),
                        ansi("bluef") + installer_string,
                        ansi("yellowf") + resolution_string))
        if errors:
            sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        info('')
        sys.exit(1)


# This describes this command to the loader
definition = dict(
    title='resolve',
    description=DESCRIPTION,
    main=main,
    prepare_arguments=prepare_arguments,
    prepare_config=prepare_config
)
