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

"""Description of xylem configuration files using `.config_utils`.

The rest of the code base is supposed to interact with with
configuration only via this module, not `.config_utils` directly.

A global representation of configuration in form of a
`.config_utils.ConfigDescription` object can be accessed via
:func:`get_config_description`.  The resulting configuration dictionary
can be accessed via :func:`get_config` and :func:`set_config`.
"""

from __future__ import unicode_literals

import os

from six.moves import map

from .config_utils import DEFAULT_PREFIX
from .config_utils import ConfigDescription
from .config_utils import String
from .config_utils import List
from .config_utils import Boolean
from .config_utils import Dict
from .config_utils import MergingDict
from .config_utils import Any
from .config_utils import Path
from .config_utils import load_config
from .config_utils import config_from_defaults
from .config_utils import system_config_dir
from .config_utils import system_cache_dir
from .config_utils import user_cache_dir
from .config_utils import user_config_dir
from .config_utils import add_global_config_arguments as \
    _add_global_config_arguments
from .config_utils import handle_global_config_arguments as \
    _handle_global_config_arguments
from .config_utils import handle_global_config_arguments_post as \
    _handle_global_config_arguments_post

from .text_utils import text_type


def sources_dir(parent):
    """Utility returning the sources.d directory given a parent folder."""
    return os.path.join(parent, SOURCES_DIR)


XYLEM_TOOL_NAME = "xylem"
"""Name of the xylem tool as passed to various `.config_utils` APIs"""

SOURCES_DIR = "sources.d"
"""Sources folder inside the config directory."""

DEFAULT_CACHE_DIR = system_cache_dir(DEFAULT_PREFIX, XYLEM_TOOL_NAME)
"""Default system-wide cache folder."""

DEFAULT_SOURCES_DIR = sources_dir(system_config_dir(DEFAULT_PREFIX,
                                                    XYLEM_TOOL_NAME))
"""Default system-wide sources folder."""


def build_config_description():
    """Build the global configuration description for xylem.

    :rtype: `.config_utils.ConfigDescription`
    """
    description = ConfigDescription("config.yaml")
    add = description.add
    add("os_override", type=String,
        command_line_argument="os",
        command_line_metavar="name:version",
        help="""override os detection; if no ':' is present, the entire
                string is interpreted as the os name and the version is
                detected; may also be of the form
                `name:version&feature1,feature2` to concisely override
                the list of os features (takes precedence over
                `--os-features`).""")
    add("os_options/features", type=List(String),
        command_line_argument="os-features",
        command_line_metavar='"feature1,feature2,..."',
        help="""OS features to be used. The list of possible values and
                the default choice is defined by the os plugin for the
                selected OS.""")
    add("core_installers", type=List(String),
        command_line=True,
        command_line_metavar='"inst1,inst2,..."',
        help="""core installers to be used. The default list is defined
                by the OS plugin for the selected OS. Additional
                installers as defined by installer plugins may be used
                on top of the core installers unless the
                `use_additional_installers` option is set to False.""")
    add("use_additional_installers", type=Boolean, default=True,
        command_line=True,
        help="""if `True`, use additional installers as defined by
                installer plugins on top of the core installers""")
    add("install_from", type=MergingDict(List(String)),
        command_line_metavar='"inst1:[key1,key2,...] ..."',
        help="""mapping installer names to list of xylem keys;
        overwrites the installer priority such that the given keys are
        only ever installed with the specified installer""")
    add("installer_options", type=MergingDict(Dict(Any)),
        command_line_metavar='"inst1:{opt1:val1,...}, ..."',
        help="""options passed to installer plugins; valid options are
        specific to each installer plugin""")
    add("user_sources", type=Boolean, default=False,
        command_line=True,
        help="""if `True`, look for sources and cache in user directory
        instead of system-wide locations""")
    add("cache_dir", type=Path,
        command_line=True,
        help="""override the cache location""")
    add("sources_dir", type=Path,
        command_line=True,
        help="""override the sources directory""")
    return description


_config_description = build_config_description()
_config = config_from_defaults(_config_description)


def get_config_description():
    """Access the global configuration description for xylem.

    :rtype: `.config_utils.ConfigDescription`
    """
    global _config_description
    return _config_description


def get_default_config():
    """Create a fresh default config object."""
    return config_from_defaults(get_config_description())


def get_config():
    """Access the global config dict as built after command line parsing.

    See :func:`set_config`.

    :rtype: dict
    """
    global _config
    return _config


def set_config(config):
    """Set the global config dict.

    See :func:`get_config`.

    :param dict config: the config dict to set
    """
    global _config
    _config = config


def add_global_config_arguments(parser):
    """Add global config-related command line options.

    See :func:`.config_utils.add_global_config_arguments`.

    :param parser: :mod:`argparse` argument parser; does not create a
        subgroup, i.e. best pass a 'global' parser group
    """
    _add_global_config_arguments(parser, XYLEM_TOOL_NAME)


def handle_global_config_arguments(args):
    """Handle global config-related command line options before loading config.

    See :func:`.config_utils.handle_global_config_arguments`.

    :param argparse.Namespace args: arguments from command line
    """
    _handle_global_config_arguments(args, XYLEM_TOOL_NAME)


def add_config_arguments(parser):
    """Add arguments for config description in :func:`get_config_description`

    :param parser: :mod:`argparse` argument parser; an appropriate
        subgroup is created
    """
    description = get_config_description()
    description.add_arguments(parser)


def handle_config_arguments(args):
    """Handle xylem specific config-related command line options.

    Loads the configuration from config files and merges it
    appropriately with the command line arguments. Sets the global
    config with :func:`set_config`.

    :param argparse.Namespace args: arguments from command line
    """
    description = get_config_description()
    config = load_config(args, description, XYLEM_TOOL_NAME)
    process_config(config, args)
    _handle_global_config_arguments_post(args, config, XYLEM_TOOL_NAME)
    set_config(config)


def parse_os_override(os_arg):
    """Utility to parse os_override arguments.

    :param str os_arg: string of form
        ``"name:version&feature1,features2,..."`` where features and
        version is optional
    :returns: triple ``(name, version, list_of_features)``; ``version``
        and ``list_of_features`` may be ``None`` if no ``':'`` / ``'&'
        is contained in ``os_arg``
    """
    strip = text_type.strip
    if '&' in os_arg:
        os_tuple, features = map(strip, os_arg.split('&', 1))
        if features:
            features = list(map(strip, features.split(',')))
        else:
            features = []
    else:
        os_tuple, features = os_arg, None
    if ':' in os_tuple:
        os_name, os_version = map(strip, os_tuple.split(':', 1))
    else:
        os_name, os_version = os_tuple.strip(), None
    return (os_name, os_version, features)


def process_config(config, args):
    """Post-process the loaded config given the command line arguments.

    Ensures that the ``cache_dir`` and ``sources_dir`` entries in the
    config files have appropriate values.  See the argparse description
    set in :func:`.arguments.add_global_arguments` for a detailed
    description how these directories are computed if not explicitly
    set.

    Also parses ``"os_override"`` into (name, version) tuple and the
    potential override of ``"os_options/features"``.
    """
    if config.cache_dir is None:
        if args.config_dir:
            config.cache_dir = user_cache_dir(args.config_dir)
        else:
            if config.user_sources:
                config.cache_dir = user_cache_dir(
                    user_config_dir(XYLEM_TOOL_NAME))
            else:
                config.cache_dir = system_cache_dir(
                    args.prefix, XYLEM_TOOL_NAME)
    if config.sources_dir is None:
        if args.config_dir:
            config.sources_dir = sources_dir(args.config_dir)
        else:
            if config.user_sources:
                config.sources_dir = sources_dir(
                    user_config_dir(XYLEM_TOOL_NAME))
            else:
                config.sources_dir = sources_dir(
                    system_config_dir(args.prefix, XYLEM_TOOL_NAME))
    if config.os_override is not None:
        name, version, features = parse_os_override(config.os_override)
        config.os_override = (name, version)
        if features is not None:
            config.os_options.features = features
