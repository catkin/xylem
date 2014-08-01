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

"""Module to describe config files and expose some items on the command line.

Configuration is done in YAML files containing dictionaries with string
keys and on the command line with `argparse`.  `ConfigDescription`
objects can be created that describe the items config files, how they
are parsed, exposed on the command line and how values from multiple
sources are merged to the effective configuration.  Single items are
described by `ConfigItem` objects, whose type is defined by `ConfigType`
objects.  Implemented config types include `Any`, `Boolean`, `String`,
`Path`, `List`, `Dict`, `MergingDict`.  The created configuration
dictionaries are of type `ConfigDict`, which derives from `dict` to
allow attribute access like ``config.os_override`` instead of only
``config["os_override"]``.

High-level API functions include:
 - :meth:`ConfigDescription.add`
 - :meth:`ConfigDescription.add_arguments`
 - :func:`add_global_config_arguments`
 - :func:`handle_global_config_arguments`
 - :func:`handle_global_config_arguments_post`
 - :func:`load_config`

Example usage:

.. code-block:: python

    TOOL_NAME="foo-tool"

    # describe config structure and types
    description = ConfigDescription("config.yaml")
    add = description.add
    add("foo", type=String,
        command_line=True)
    add("bar-flag", type=Boolean, default=False,
        command_line_argument="bar")
    add("quux/fiz", type=Path,
        command_line=True,
        help="`~` is correctly expanded")
    add("quux/faz", type=List(String),
        command_line_metavar='"faz1,faz2,..."')
    add("dict_of_lists", type=MergingDict(List(String)),
        command_line_metavar='"inst1:[key1,key2,...] ..."')
    add("dict_of_dicts", type=MergingDict(Dict(Any)),
        help="dict of dict of any value; not exposed to command line")

    # create argparse parser and add arguments for config items
    parser = argparse.ArgumentParser(formatter_class=ConfigHelpFormatter)
    description.add_arguments(parser)

    # add argument groups and some global config-related arguments that
    # are independent from the description
    group = parser.add_argument_group('global arguments')
    add_global_config_arguments(group, "footool")

    # parse command line arguments
    args = parser.parse_args()

    # handle global config arguments
    handle_global_config_arguments(args, TOOL_NAME)

    # load config from files, merging with values from command line
    config = load_config(args, description, TOOL_NAME)

    # handle global arguments that require the loaded config (e.g.
    # `--print-config`)
    handle_global_config_arguments_post(args, config, TOOL_NAME)

    # access `config` like a dictionary or with attribute access
    print(config["quux"]["fiz"])
    print(config.quux.faz)
    print(config.dict_of_lists['foo'][0:3])
"""

# TODO: for Boolean possibly add two mutually exclusive options --foo
#       and --no-foo both with store_true instead of one argument
#       taking a value

from __future__ import unicode_literals

import six
import os
import argparse
import textwrap
import re

from copy import deepcopy
from yaml import YAMLError

from .text_utils import type_name
from .text_utils import text_type
from .text_utils import to_str
from .util import raise_from
from .yaml_utils import load_yaml
from .yaml_utils import dump_yaml
from .log_utils import info
from .log_utils import debug
from .exception import XylemError
from .exception import type_error_msg


UNSET_YAML = None
"""Value to interpret as 'unset' in YAML file."""

UNSET_COMMAND_LINE = None
"""Value to interpret as 'unset' for command line arguments."""

DEFAULT_PREFIX = "/"
DEFAULT_USER_CONFIG_DIR_UNEXPANDED = "~/.config"
DEFAULT_USER_CONFIG_DIR = os.path.expanduser(
    DEFAULT_USER_CONFIG_DIR_UNEXPANDED)
SYSTEM_CONFIG_PATH = "etc"
SYSTEM_CACHE_PATH = "var/cache"
USER_CACHE_PATH = "cache"


class ConfigError(XylemError):

    """Type for any errors related to config description and parsing."""


class ConfigValueError(ConfigError):

    """Input from file or command line has wrong type or cannot be parsed.

    This is supposed to indicate a configuration error (rather than a
    programming error).
    """


class ConfigDescriptionError(ConfigError):

    """ConfigDescription is invalid.

    This probably indicates a programming error.
    """


def system_config_dir(prefix, tool_name):
    """Path to system configuration, given prefix and tool name."""
    return os.path.join(prefix, SYSTEM_CONFIG_PATH, tool_name)


def system_cache_dir(prefix, tool_name):
    """Path to system cache, given prefix and tool name."""
    return os.path.join(prefix, SYSTEM_CACHE_PATH, tool_name)


def user_config_dir(tool_name):
    """Path to user configuration, given tool name."""
    return os.path.join(DEFAULT_USER_CONFIG_DIR, tool_name)


def user_cache_dir(config_dir):
    """Path to user cache dir, given the user config dir."""
    return os.path.join(config_dir, USER_CACHE_PATH)


def split_group(name):
    """Split item name containing ``'/'`` into tuple of group/subname.

    Examples:
     - an input of ``'foo/bar'`` results in ``('foo', 'bar')``
     - an input of ``'foo/bar/baz'`` results in ``('foo/bar', 'baz')``
    """
    return tuple(reversed([x[::-1] for x in name[::-1].split("/", 1)]))


def dashify(name):
    """Replace ``_`` and ``/`` with ``-``."""
    return name.replace("_", "-").replace("/", "-")


def underscorify(name):
    """Replace ``-`` and ``/`` with ``_``."""
    return name.replace("-", "_").replace("/", "_")


def strip_leading_dashdash(name):
    """Remove leading ``'--'`` if present."""
    if name.startswith('--'):
        return name[2:]
    else:
        return name


def expand_input_path(value):
    """Expand and normalize path, unless it is ``None``."""
    if value is None:
        return None
    return os.path.abspath(os.path.expanduser(value))


def process_config_file_yaml(config):
    """Utility for parsing yaml config files.

    Handles empty files and makes sure config file is dictionary with
    strings as keys.

    :raises ConfigValueError: if config is not ``None`` or dictionary
        with string keys
    """
    if config is None:
        # allow empty config file
        config = dict()
    if not isinstance(config, dict):
        raise ConfigValueError(
            "Config file cannot be interpreted as dictionary. "
            "Parsed as type '{}'.".format(type_name(config)))
    for key in config:
        if not isinstance(key, text_type):
            raise ConfigValueError(
                type_error_msg('text', key, what_for="config keys"))
    return config


def load_config_file_yaml(path):
    """Utility for loading yaml config files.

    Makes sure to always return a dict with strings as keys.  Non-
    existent or empty files result in an empty dictionary.

    :raises ConfigValueError: if config file cannot be opened, decode or
        parsed
    """
    try:
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                binary_data = f.read()
            config = load_yaml(to_str(binary_data))
        else:
            config = None
        return process_config_file_yaml(config)
    except EnvironmentError as e:
        raise_from(ConfigValueError,
                   "failed to read config file `{}`".format(path), e)
    except UnicodeError as e:
        raise_from(ConfigValueError,
                   "failed to decode config file `{}`".format(path), e)
    except YAMLError as e:
        raise_from(ConfigValueError,
                   "failed to parse config file as YAML `{}`".format(path), e)
    except ConfigValueError as e:
        raise_from(ConfigValueError,
                   "config file has invalid structure `{}`".format(path), e)


def maybe_instantiate(class_or_object):
    """Helper for :class:`ConfigType`.

    We want to allow passing uninstantiated classes ``String`` (instead
    of ``String()``) but we also want to allow instantiated ones as in
    ``List(String)``.  I.e. the user can pass either a
    :class:`ConfigType` derived class, or an instantiated
    :class:`ConfigType` object.
    """
    if isinstance(class_or_object, type):
        return class_or_object()
    else:
        return class_or_object


class ConfigHelpFormatter(argparse.HelpFormatter):

    """Help formatter for argparse with support for line-breaks and paragraphs.

    The standard argparse formatter formats all argument help texts and
    section descriptions into one block, ignoring all existing line-
    breaks. With this formatter, three or more consecutive line-breaks
    are interpreted as a paragraph break (replaced by ``\\n\\n``) and
    within paragraphs, two consecutive line-breaks are interpreted as a
    hard line-break (replaced by ``\\n``). Each blocks within a paragraph
    (between the hard line-breaks) is still formatted as in the standard
    help formatter.

    The formatter also supports raw pre-formatted paragraphs. If the
    paragraphs starts with ``R|``, it is only re-indented appropriately,
    but not otherwise formatted.
    """

    def __init__(self, *args, **kwargs):
        super(ConfigHelpFormatter, self).__init__(*args, **kwargs)
        self._paragraph_break_matcher = re.compile(r'\n\n\n+')
        self._line_break_matcher = re.compile(r'\n\n')
        self._raw_marker_matcher = re.compile(r'^\s*R\|')

    def _wrap_paragraphs(self, text, width, indent=''):
        result = []
        for para in self._paragraph_break_matcher.split(text):
            if self._raw_marker_matcher.match(para):
                para = self._raw_marker_matcher.sub(
                    lambda m: ' '*(m.end()-m.start()), para)
                para = textwrap.dedent(para).splitlines()
                result.extend([indent + l for l in para])
            else:
                for nobreak in self._line_break_matcher.split(para):
                    block = self._whitespace_matcher.sub(' ', nobreak).strip()
                    result.extend(textwrap.wrap(block, width,
                                                initial_indent=indent,
                                                subsequent_indent=indent))
            result.append("")
        if result:
            result = result[0:-1]
        return result

    def _split_lines(self, text, width):
        return self._wrap_paragraphs(text, width)

    def _fill_text(self, text, width, indent):
        return "\n".join(self._wrap_paragraphs(text, width, indent))


class ConfigDict(dict):

    """Derivative of ``dict`` to allow attribute access.

    This is used for all config dicts to allow attribute access like
    ``config.os_override`` instead of ``config["os_override"]``.
    """

    def __init__(self, *args, **kwargs):
        super(ConfigDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def ceorce_config_dict(config):
    """Helper to convert a regular dictionary to a config dict.

    Calls ``ceorce_config_dict`` recursively on dict type values. Does
    not copy or modify if ``config`` is already of type ``ConfigDict``.

    The resulting config dict may share structure with the input.

    :type config: `dict` or `ConfigDict`
    """
    if isinstance(config, ConfigDict):
        return config
    if not isinstance(config, dict):
        return config
    result = ConfigDict()
    for k, v in six.iteritems(config):
        result[k] = ceorce_config_dict(v)


def copy_to_dict(config):
    """Helper to copy a ConfigDict instance to a regular dict.

    Calls ``copy_to_dict`` recursively on values of type `ConfigDict`,
    and `deepcopy` on keys and other values.

    :param ConfigDict config: (nested) config dict
    """
    result = {}
    for k, v in six.iteritems(config):
        if isinstance(v, ConfigDict):
            v = copy_to_dict(v)
        else:
            v = deepcopy(v)
        result[deepcopy(k)] = v
    return result


class ConfigType(object):

    """Type describing a config file entry.

    The config type provides information on how to parse config values
    from yaml and command line and how to verify appropriate values.  It
    further describes how multiple values from a cascade of config files
    (e.g. command line, user config, system config, default) are to be
    merged.

    A value of ``None`` by default refers to the config item being
    unset, but custom 'unset' values can be specified with
    :meth:`unset_value`.
    """

    def from_yaml(self, value):
        """Create config value from yaml loaded config value.

        This for example allows to expand shorthand notation into a
        uniform representations, or transform yaml into custom datatypes
        as needed.

        A value of `UNSET_YAML` should be interpreted as 'unset'.


        :param value: python data structure representing the loaded yaml
            from the config file.  Thus the type is one of (None, bool,
            str, list, dict)
        :raises ConfigValueError: if ``value`` has invalid type or
            structure
        """
        if value == UNSET_YAML:
            return self.unset_value()
        return self.verify(value)

    def from_command_line(self, value):
        """Create config value from value of command line parser.

        A value of `UNSET_COMMAND_LINE` should be interpreted as
        'unset'.

        The default implementation parses the input string as yaml and
        then invokes :meth:`from_yaml`.

        Before returning a value, :meth:`verify` should be used to
        verify the validity of the parsed value.

        :param value: value from the command line parser, which is a
            string when :meth:`command_line_multiple()` is false and a
            list of strings otherwise, or `UNSET_COMMAND_LINE` if the
            argument was omitted on the command line.
        :raises ConfigValueError: if ``value`` cannot be parsed properly
            or has invalid type or structure
        """
        if value == UNSET_COMMAND_LINE:
            return self.unset_value()
        try:
            return self.from_yaml(load_yaml(value))
        except YAMLError as e:
            raise_from(
                ConfigValueError, "parsing command line value failed", e)

    def verify(self, value):
        """Verify that value is of correct type and structure.

        This should be called by :meth:`from_yaml` or
        :meth:`from_command_line` before returning the parsed value, but
        can also be used independently for example when changing the
        configuration value from within the program.

        An value of :meth:`unset_value` is considered valid.

        :returns: ``value`` unchanged
        :raises ConfigValueError: if ``value`` is not of appropriate
            type and structure
        """
        return value

    def merge(self, top, bottom):
        """Merge two values of this config entry.

        The default implementation replaces ``bottom`` with ``top``,
        unless top is :meth`unset_value`.

        :param top: new value taking priority
        :param bottom: value being overwritten or extended
        """
        if not self.is_unset(top):
            return top
        else:
            return bottom

    def unset_value(self):
        """Value representing an unset config option for this type.

        Determines what value should appear in the config dict if this
        option is omitted from all config files (and on the command
        line) and no default value was specified. Unset value comparison
        is done by equality (`==`).

        :meth:`verify` should accept this value as valid.  :meth:`merge`
        should properly handle this value and :meth:`from_yaml` as well
        as :meth:`from_command_line` should convert
        `UNSET_YAML`/`UNSET_COMMAND_LINE` to this 'unset' value.
        """
        return None

    def is_unset(self, value):
        """Return ``True`` if ``value`` equals :meth:`unset_value`."""
        return value == self.unset_value()

    def command_line_multiple(self):
        """Determine if we should allow multiple command line options.

        Types like "List" and "Dict" can be composed of multiple command
        line options.  If this returns `True`,
        :meth:`from_command_line` needs to handle input of type list.
        """
        return False

    def command_line_default_metavar(self):
        """Customize the default metavar used for command line help.

        By default, this returns None meaning argparse is setting the
        default metavar.
        """
        return None

    @staticmethod
    def command_line_parsing_help():
        return None


class Any(ConfigType):

    """Config type allowing arbitrary (yaml) structures."""

    @staticmethod
    def command_line_parsing_help():
        return """any YAML structure"""


class String(ConfigType):

    """Config type for simple unparsed strings."""

    def verify(self, value):
        if not self.is_unset(value):
            if not isinstance(value, text_type):
                raise ConfigValueError(type_error_msg('string', value))
        return value

    def from_command_line(self, value):
        if value == UNSET_COMMAND_LINE:
            return self.unset_value()
        return self.from_yaml(to_str(value))

    def command_line_default_metavar(self):
        return "STRING"

    @staticmethod
    def command_line_parsing_help():
        return """string parsed as-is"""


class Boolean(ConfigType):

    """Config type for booleans (parsed as YAML)."""

    def verify(self, value):
        if not self.is_unset(value):
            if not isinstance(value, bool):
                raise ConfigValueError(type_error_msg('bool', value))
        return value

    def command_line_default_metavar(self):
        return "yes|no"


class List(ConfigType):

    """Config type for lists supporting custom element types."""

    def __init__(self, element_type=Any):
        self.element_type = maybe_instantiate(element_type)

    def from_yaml(self, value):
        if value == UNSET_YAML:
            return self.unset_value()
        if not isinstance(value, list):
            raise ConfigValueError(type_error_msg('list', value))
        return self.verify(
            [self.element_type.from_yaml(elt) for elt in value])

    def from_command_line(self, value):
        if value == UNSET_COMMAND_LINE:
            return self.unset_value()

        def parse_single(input):
            try:
                result = load_yaml(input)
            except YAMLError:
                result = None
            if not isinstance(result, list):
                # special parsing allowing lists without enclosing `[]`
                try:
                    result = load_yaml("[" + input + "]")
                except YAMLError as e:
                    raise_from(ConfigValueError,
                               "failed to parse `{}` as list".format(input), e)
            if not isinstance(result, list):
                raise ConfigValueError(type_error_msg("list", result))
            return result

        # list value means multiple command line arguments that should
        # be concatenated
        if not isinstance(value, list):
            value = [value]
        result = []
        for string in value:
            result.extend(parse_single(string))
        return self.from_yaml(result)

    def verify(self, value):
        if not self.is_unset(value):
            if not isinstance(value, list):
                raise ConfigValueError(type_error_msg('list', value))
            try:
                for elt in value:
                    self.element_type.verify(elt)
            except ConfigValueError as e:
                raise_from(ConfigValueError, "invalid list element", e)
        return value

    def command_line_multiple(self):
        return True

    def command_line_default_metavar(self):
        return '"item1,item2,..."'

    @staticmethod
    def command_line_parsing_help():
        return """the outer '[]' can be omitted; multiple occurrences of
        the same command line argument are concatenated"""


class Dict(ConfigType):

    """Config type for dictionaries supporting custom key and value types."""

    def __init__(self, value_type=Any, key_type=String):
        self.key_type = maybe_instantiate(key_type)
        self.value_type = maybe_instantiate(value_type)

    def from_yaml(self, value):
        if value == UNSET_YAML:
            return self.unset_value()
        if not isinstance(value, dict):
            raise ConfigValueError(type_error_msg("dict", value))
        result = {}
        for k, v in six.iteritems(value):
            result[self.key_type.from_yaml(k)] = \
                self.value_type.from_yaml(v)
        return self.verify(result)

    def from_command_line(self, value):
        if value == UNSET_COMMAND_LINE:
            return self.unset_value()

        def parse_single(input):
            try:
                result = load_yaml(input)
            except YAMLError:
                result = None
            if not isinstance(result, dict):
                # special parsing allowing lists without enclosing `{}`
                try:
                    result = load_yaml("{" + input + "}")
                except YAMLError as e:
                    raise_from(ConfigValueError,
                               "failed to parse `{}` as dict".format(input), e)
            if not isinstance(result, dict):
                raise ConfigValueError(type_error_msg("dict", result))
            return result

        # list value means multiple command line arguments to be merged
        if not isinstance(value, list):
            value = [value]
        result = {}
        for d in value:
            d = parse_single(d)
            existing_keys = set(d.keys()) & set(result.keys())
            if existing_keys:
                raise ConfigValueError(
                    "Dicts defined via multiple command line arguments must "
                    "have unique keys. These keys occur more than once: `{}`.".
                    format(existing_keys))
            result.update(d)
        return self.from_yaml(result)

    def verify(self, value):
        if not self.is_unset(value):
            if not isinstance(value, dict):
                raise ConfigValueError(type_error_msg('dict', value))
            try:
                for k, v in six.iteritems(value):
                    self.key_type.verify(k)
                    self.value_type.verify(v)
            except ConfigValueError as e:
                raise_from(ConfigValueError, "invalid key or value", e)
        return value

    def command_line_multiple(self):
        return True

    def command_line_default_metavar(self):
        return '"key:value,key2:value2,..."'

    @staticmethod
    def command_line_parsing_help():
        return """the outer '{}' can be omitted; multiple occurrences of
        the same command line argument are merged"""


class MergingDict(Dict):

    """Dictionary whose entries are merged when config files are merged."""

    def __init__(self, *args, **kwargs):
        super(MergingDict, self).__init__(*args, **kwargs)

    def merge(self, top, bottom):
        # merge the dictionary key by key
        result = bottom.copy()
        result.update(top)
        return result

    def unset_value(self):
        return {}

    @staticmethod
    def command_line_parsing_help():
        return Dict.command_line_parsing_help() + \
            "; value is merged with the config file entries"


class Path(String):

    """Path that gets expanded and normalized."""

    def from_yaml(self, value):
        if value == UNSET_YAML:
            return self.unset_value()
        value = super(Path, self).from_yaml(value)
        return self.verify(expand_input_path(value))

    def command_line_default_metavar(self):
        return "PATH"

    @staticmethod
    def command_line_parsing_help():
        return """string parsed as-is; path is expanded (e.g. `~`)"""


class ConfigItem(object):

    """Holds meta information about one entry in a config file.

    :ivar str name: name of the config item; may contain (up to one) '/'
        to specify grouping into a sub-dictionary, which is interpreted
        as 'group/subname'
    :ivar str help: description of the config item for the argument
        parser help
    :ivar ConfigType type: type of config item describing how it is
        parsed and merged
    :ivar default: default value to be used if unset
    :ivar bool command_line: if true, this config is exposed on the
        command line; ``False`` by default, but specifying any other
        ``command_line_...`` arguments implies ``True`` for
        ``command_line``, unless explicitly set to ``False``.
    :ivar command_line_argument: command line argument name (without
        leading dashdash); if not explicitly supplied, this is derived
        from name by replacing all '_' and '/' with '-'
    :ivar command_line_metavar: command line argument metavar; if not
        explicitly supplied, the default for the type is used
    """

    def __init__(self,
                 name,
                 help=None,
                 type=Any,
                 default=None,
                 command_line=None,
                 command_line_argument=None,
                 command_line_metavar=None):
        self.name = name
        self.help = help
        self.type = maybe_instantiate(type)
        if default is None:
            self.default = self.type.unset_value()
        else:
            self.default = default
        if command_line is None:
            command_line = any([x is not None for x in [command_line_argument,
                                                        command_line_metavar]])
        if command_line_argument:
            command_line_argument = \
                strip_leading_dashdash(command_line_argument)
        elif command_line:
            command_line_argument = dashify(name)
        self.command_line = command_line
        self.command_line_argument = command_line_argument
        if command_line_metavar is None:
            command_line_metavar = self.type.command_line_default_metavar()
        self.command_line_metavar = command_line_metavar

    @staticmethod
    def is_group_name(name):
        return "/" in name

    def is_group(self):
        return self.is_group_name(self.name)

    def help_string(self):
        """Compose help string for command line parser."""
        help = ""
        if self.help:
            help += self.help + "\n\n"
        info = []
        if self.is_group() or self.command_line_argument != dashify(self.name):
            info += ["config: `{}`".format(self.name)]
        info += ["type: {}".format(type_name(self.type))]
        if self.default != self.type.unset_value():
            info.append("default: {}".format(self.default))
        help += "(" + ", ".join(info) + ")"
        return help

    def add_argument(self, parser):
        """Add command line argument for this config item to ``parser``."""
        assert(self.command_line)
        kwargs = {}
        kwargs["help"] = self.help_string()
        kwargs["default"] = UNSET_COMMAND_LINE
        if self.type.command_line_multiple():
            kwargs["action"] = "append"
        if self.command_line_metavar is not None:
            kwargs["metavar"] = self.command_line_metavar
        parser.add_argument('--' + self.command_line_argument, **kwargs)


class ConfigDescription(object):

    """Describes structure of a config file.

    It also describes which options are exposed to command line and how
    to parse them.

    A configuration is a dictionary, where each item corresponds to a
    entry in that dictionary with the item name as key.  There is
    support for one level of grouping.  Item names containing a '/' are
    interpreted as 'group/subname'.  Groups are sub-dictionaries as
    entries in the config dictionary.  The subnames of the config items
    constitute the keys of the group dicts.  When config dicts are
    merged, Group dicts are merged automatically key but key.

    :ivar str namespace: path of the config file relative to the root
        config directory
    :ivar list itemlist: list of all items in order (including items in
        groups)
    :ivar dict items: mapping names to items (including full
        names for items in groups)
    :ivar dict groups: mapping group names to dict of subnames to items
    :ivar dict command_line_arguments: mapping command line argument
        names to items
    """

    def __init__(self, namespace):
        self.namespace = namespace
        self.itemlist = []
        self.items = {}
        self.groups = {}
        self.command_line_arguments = {}

    def add(self, name, *args, **kwargs):
        """Add item with given name to the description.

        Additional arguments are passed to the :class:`ConfigItem`
        constructor.

        :raises ConfigDescriptionError: if the newly added config item
            is invalid or conflicting with the existing items
        """
        if name in self.items:
            raise ConfigDescriptionError("Duplicate name '{}'".format(name))
        if name in self.groups:
            raise ConfigDescriptionError(
                "Name '{}' already exists as group".format(name))

        item = ConfigItem(name, *args, **kwargs)

        if "/" in name:
            group, subname = split_group(name)
            if group not in self.groups:
                if group in self.items:
                    raise ConfigDescriptionError(
                        "Group name '{}' already exists as non-group item.".
                        format(group))
                else:
                    self.groups[group] = {}
            self.groups[group][subname] = item

        self.itemlist.append(item)
        self.items[name] = item

        if item.command_line:
            arg_name = item.command_line_argument
            if arg_name in self.command_line_arguments:
                raise ConfigDescriptionError(
                    "Duplicate command line argument name '{}' for config "
                    "item '{}' and '{}'.".
                    format(arg_name, item.name,
                           self.command_line_arguments[arg_name].name))
            self.command_line_arguments[arg_name] = item

    def add_arguments(self, parser):
        """Create a group and add all command-line-enabled items to it.

        See :func:`config_from_args` on how to process the passed
        arguments to a config dict.
        """
        typeset = {type(i.type) for i in self.itemlist
                   if i.type.command_line_parsing_help()}
        if typeset:
            typelist = list(typeset)
            typelist.sort(key=to_str)
            helplist = ["{}: {}".format(to_str(t),
                                        t.command_line_parsing_help())
                        for t in typelist]
            typehelp = "\n\n\nThere are some special cases and short hand " \
                "notation for parsing config arguments:\n\n* " + "\n\n* ". \
                join(helplist)
        else:
            typehelp = ""
        subparser = parser.add_argument_group(
            "config arguments", description="""The following typed
            arguments correspond to entries in the config file.  Command
            line argument values are interpreted as YAML and override
            the corresponding entries in user/system config files.  """
            + typehelp)
        for item in self.itemlist:
            if item.command_line:
                item.add_argument(subparser)


def add_global_config_arguments(parser, tool_name):
    """Add global command line arguments related to the configuration setup.

    These options are independent from a config description.

    See :func:`handle_global_config_arguments`,
    :func:`handle_global_config_arguments_post`
    """
    prefix_env_var = "{}_PREFIX".format(tool_name.upper())
    config_dir_env_var = "{}_DIR".format(tool_name.upper())
    config_argument = "--{}-dir".format(tool_name)

    add = parser.add_argument
    add('--print-config', action='store_true',
        help="""print the effective configuration (from command line and
        config files) and exit""")
    add('--no-user-config', action="store_true",
        help="""disable user config (system-wide config only)""")
    add('--prefix', metavar=prefix_env_var,
        help="""Set the FHS prefix for finding system-wide
        configurations and caches.  System-wide configuration files will
        be looked for in '{0}' and cache files will be placed in '{1}'.
        The default prefix is '{2}'.  The prefix can also be set by the
        {3} environment variable, but the command line option takes
        precedence.""".format(
            system_config_dir(prefix_env_var, tool_name),
            system_cache_dir(prefix_env_var, tool_name),
            DEFAULT_PREFIX, prefix_env_var))
    add(config_argument, metavar=config_dir_env_var, dest="config_dir",
        help="""Specify the path of directory to use for configuration
        and caches.  Configuration files will be looked for in '{0}' and
        caches will be placed in '{1}'.  This is intended to be used by
        tools that want to create a local configuration and cache
        independent from the system-wide setup.  If set, only the
        configuration files in {0} are used instead of system and user
        configuration files, i.e.  {2} will be ignored.  This can also
        be set by the {0} environment variable, but the command line
        option takes precedence.""".format(
            config_dir_env_var,
            user_cache_dir(config_dir_env_var),
            prefix_env_var))


def handle_global_config_arguments(args, tool_name):
    """Handle global configuration-related command line arguments.

    This deals with expanding provided paths, as well as looking up
    environment variables for arguments not passed.  It updates ``args``
    accordingly.

    It is intended to be called before the effective config dict is
    created.

    See :func:`add_global_config_arguments`,
    :func:`handle_global_config_arguments_post`

    :param argparse.Namespace args: parsed command line arguments
    :param str tool_name: name of the tool to determine config file
        locations, argument names and environment variables
    """
    prefix_env_var = "{}_PREFIX".format(tool_name.upper())
    config_dir_env_var = "{}_DIR".format(tool_name.upper())

    if args.config_dir is None:
        args.config_dir = os.environ.get(config_dir_env_var, None)
    if args.prefix is None:
        args.prefix = os.environ.get(prefix_env_var, DEFAULT_PREFIX)

    args.config_dir = expand_input_path(args.config_dir)
    args.prefix = expand_input_path(args.prefix)
    if args.config_dir and args.prefix:
        debug("Specifed both prefix `{}` and {} dir `{}`. The prefix will be "
              "ignored.".format(args.prefix, tool_name, args.config_dir))


def handle_global_config_arguments_post(args, config, tool_name):
    """Handle global configuration-related command line arguments with config.

    This deals with global config-related arguments that require the
    loaded configuration, e.g. ``--print-config``.

    The is intended to be called after the effective config dict has
    been created.

    See :func:`add_global_config_arguments`,
    :func:`handle_global_config_arguments`

    :param argparse.Namespace args: parsed command line arguments
    :param dict config: config dict
    :param str tool_name: name of the tool to determine config file
        locations, argument names and environment variables
    """
    if args.print_config:
        info(dump_yaml(config))
        exit(0)


def copy_conifg_dict(description, config):
    """Utility to shallow-copy config dict."""
    result = ConfigDict(config)
    for group in description.groups:
        result[group] = ConfigDict(result[group])
    return result


def merge_configs(description, top, *more_configs):
    """Merge two or more config dicts.

    The configurations are merged on a key by key basis as described by
    ``description``, using the :meth:`ConfigType.merge` for each
    :class:`ConfigItem`.

    ``top`` takes highest priority and the configs in ``more_configs``
    have decreasing priority.  The config dicts are assumed to have been
    loaded with the ``config_from_...`` functions using ``description``.
    This means it is assumed that all keys and groups as described by
    ``description`` exist in all input config dicts.

    :param description: description of the config dicts; the type
        information of each entry is used for merging
    :type description: `ConfigDescription`
    :param dict top: config dict with structure defined by
        ``description``
    :param more_configs: list of configuration dicts with structure
        defined by ``description``
    :type more_configs: list of dicts
    """
    result = copy_conifg_dict(description, top)
    for bottom_config in more_configs:
        for name, item in six.iteritems(description.items):
            if "/" in name:
                group, subname = split_group(name)
                result[group][subname] = item.type.merge(
                    result[group][subname],
                    bottom_config[group][subname])
            else:
                result[name] = item.type.merge(result[name],
                                               bottom_config[name])
    return result


def load_config(args, description, tool_name):
    """Load configuration from config files and command line arguments.

    High-level API for loading config defined by system/user config
    files and config from the command line ``args``.

    Uses :func:`merge_configs` on config dicts loaded by
    :func:`config_from_defaults`, :func:`config_from_file` and
    :func:`config_from_args`.

    :param argparse.Namespace args: parsed command line arguments
    :param description: description of the items comprising the
        configuration
    :type description: `ConfigDescription`
    :param str tool_name: name of the tool to determine config file
        location
    :returns: config dict with structure as defined by ``description``
    :raises ConfigValueError: if parsing of files or arguments fails
    """
    if args.config_dir is not None:
        dirs = [args.config_dir]
    else:
        system_dir = system_config_dir(args.prefix, tool_name)
        user_dir = user_config_dir(tool_name)
        if args.no_user_config:
            dirs = [system_dir]
        else:
            dirs = [user_dir, system_dir]
    filenames = [os.path.join(d, description.namespace) for d in dirs]
    configs = [config_from_args(args, description)] + \
              [config_from_file(f, description) for f in filenames] + \
              [config_from_defaults(description)]
    return merge_configs(description, *configs)


def config_from_defaults(description):
    """Return a config dictionary with default values for all items.

    :param description: description of the items comprising the
        configuration
    :type description: `ConfigDescription`
    :returns: config dict with structure as defined by ``description``
    """
    result = ConfigDict()
    for name, item in six.iteritems(description.items):
        if "/" in name:
            group, subname = split_group(name)
            if group not in result:
                result[group] = ConfigDict()
            result[group][subname] = item.default
        else:
            result[name] = item.default
    return result


def config_from_args(args, description):
    """Return config dictionary from command line arguments.

    See :meth:`ConfigDescription.add_arguments` for creating compatible
    command line arguments.

    :param argparse.Namespace args: parsed command line arguments
    :param description: description of the items comprising the
        configuration
    :type description: `ConfigDescription`
    :returns: config dict with structure as defined by ``description``
    :raises ConfigValueError: if parsing of arguments fails
    """
    config = ConfigDict()
    args_dict = vars(args)

    def process_item(target_dict, key, item):
        if item.command_line:
            value = item.type.from_command_line(
                args_dict[underscorify(item.command_line_argument)])
        else:
            value = item.type.unset_value()
        target_dict[key] = value

    for group, group_dict in six.iteritems(description.groups):
        config[group] = ConfigDict()
        for subname, item in six.iteritems(group_dict):
            process_item(config[group], subname, item)
    for name, item in six.iteritems(description.items):
        # only non-group items
        if "/" not in name:
            process_item(config, name, item)
    return config


def config_from_file(filename, description):
    """Return config dictionary from config file.

    :param str filename: path to the config file
    :param description: description of the items comprising the
        configuration; config dict is created according to this
        description; any missing keys are created with 'unset' values
        and unknown entries are ignored
    :type description: `ConfigDescription`
    :returns: config dict with structure as defined by ``description``
    :raises ConfigValueError: if parsing of files fails
    """
    contents = load_config_file_yaml(filename)
    return config_from_parsed_yaml(contents, description)


def config_from_parsed_yaml(data, description):
    """Utility for creating config dict from parsed YAML file.

    :param dict data: dictionary (nested yaml structure) as read from
        file (see :func:`load_config_file_yaml`)
    :param description: config dict is created according to this
        description; any missing keys are created with 'unset' values
        and unknown entries are ignored
    :type description: `ConfigDescription`
    :returns: config dict with structure as defined by ``description``
    :raises ConfigValueError: if parsing of files fails
    """
    def process_item(target_dict, source_dict, key, item):
        value = source_dict.get(key, None)
        value = item.type.from_yaml(value)
        target_dict[key] = value

    config = ConfigDict()
    for group, group_dict in six.iteritems(description.groups):
        config[group] = ConfigDict()
        data_group = data.get(group, {})
        for subname, item in six.iteritems(group_dict):
            process_item(config[group], data_group, subname, item)
    for name, item in six.iteritems(description.items):
        # only handle non-group items
        if "/" not in name:
            process_item(config, data, name, item)
    return config
