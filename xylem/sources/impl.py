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

import os
import pkg_resources
import yaml

from .. import DEFAULT_PREFIX
from ..log_utils import error
from ..log_utils import is_verbose
from ..log_utils import info
from ..log_utils import debug
from ..util import load_yaml
from ..util import raise_from
from ..text_utils import to_str
from ..specs import verify_spec_name
from ..specs import get_spec_plugin_list


# is supposed to work like a entry_point? Does package data work that
# way? ... It seems no, but maybe we should realize a form of 'default
# sources' plugin
SOURCES_GROUP = 'xylem.sources'


# TODO: fix docstrings

def get_default_source_descriptions():
    """Return the list of default source urls.

    :returns: lists of source urls keyed by spec type
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    files = pkg_resources.resource_listdir(SOURCES_GROUP, 'sources.d')
    for file_path in files:
        file_path = os.path.join('sources.d', file_path)
        data = pkg_resources.resource_string(SOURCES_GROUP, file_path)
        yield parse_source_descriptions(
            data, 'xylem_default_sources:' + file_path)


def get_source_descriptions(sources_dir):
    """Return a list of source urls.

    :returns: lists of source urls keyed by spec, or None if no configs
        found
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    if os.path.exists(sources_dir):
            if is_verbose():
                info("Loading source urls from '{0}'".format(sources_dir))
            return load_sources_from_path(sources_dir)


def load_sources_from_path(path):
    """Return a list of source urls from a given directory of source lists.

    Only files which have the .yaml extension are processed, other
    files, hidden files, and directories are ignored.

    :param path: directory containing source list files
    :type path: str
    :returns: lists of source urls keyed by spec type
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    return _load_sources(
        [os.path.join(path, s) for s in os.listdir(path)])


def _load_sources(files):
    for file_path in files:
        if file_path.startswith('.'):
            continue
        if not file_path.endswith('.yaml'):
            continue
        if not os.path.isfile(file_path):
            continue
        yield parse_source_file(file_path)


def parse_source_file(file_path):
    """Parse a given list file and returns a list of source urls.

    :param file_path: path to file containing a list of source urls
    :type file_path: str
    :returns: lists of source urls keyed by spec type
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    with open(file_path, 'r') as f:
        data = f.read()
        return parse_source_descriptions(to_str(data), file_path)


# TODO: raise error by default?

def parse_source_descriptions(data, file_path='<string>'):
    """Parse a YAML string as source descriptions.

    If parsing failes an error message is printed to console and an
    empty list is returned.

    :param str data: string containing YAML representation of source
        descriptions
    :param str file_path: name of the file whose contents ``data``
        contains
    :returns: tuple of ``file_path`` and parsed source descriptions
    :rtype: `tuple(str, list)`
    """
    try:
        descriptions = load_yaml(data)
        verify_source_description_list(descriptions)

    except yaml.YAMLError as exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark.line
            col = exc.problem_mark.column
            error("Invalid YAML in source list file '{0}' at '{1}:{2}':\n"
                  .format(file_path, mark + 1, col + 1) + to_str(exc))
        else:
            error("Invalid YAML in source list file '{0}':\n"
                  .format(file_path) + to_str(exc))
        descriptions = []
    return (file_path, descriptions)


def verify_source_description_list(descr_list):
    """Verify that a source description list has valid structure.

    :param list descr_list: list of source descriptions
    :raises ValueError: if structure of source descriptions is invalid
    """
    try:
        for descr in descr_list:
            verify_source_description(descr)
    except TypeError as e:
        raise_from(ValueError, "failed to verify source description list of "
                   "type '{0}'".format(to_str(type(descr_list))), e)
    except ValueError as e:
        raise_from(ValueError, "source description list contains invalid "
                   "source descriptions", e)


def verify_source_description(descr):
    """Verify that a source description has valid structure.

    :param dict descr_list: source description
    :raises ValueError: if structure of source description is invalid
    """
    if not isinstance(descr, dict):
        raise ValueError("Expected source description to be a dictionary, but "
                         "got '{0}'.".format(to_str(type(descr))))
    keys = descr.keys()
    if not len(keys) == 1:
        raise ValueError("Expected source description to have one entry, but "
                         "got keys '{0}'.".format(keys))
    try:
        verify_spec_name(keys[0])
    except ValueError as e:
        raise_from(ValueError, "source description does not have valid "
                   "spec name '{0}'".format(keys[0], e))


def sources_dir_from_prefix(prefix):
    return os.path.join(prefix, "etc", "xylem", "sources.d")


def cache_dir_from_prefix(prefix):
    return os.path.join(prefix, "var", "cache", "xylem", "sources")


def sources_dir_from_xylem_dir(xylem_dir):
    return os.path.join(xylem_dir, "sources.d")


def cache_dir_from_xylem_dir(xylem_dir):
    return os.path.join(xylem_dir, "cache", "sources")


# TODO: Introduce CachePermissionError to specifically indicate
# permission problems with creating or manipulating the cache dir


class UnknownSpecError(Exception):

    pass


# TODO: Should plugins be registered globally (singleton) instead of
# these context objects? How are they supposed to register with the
# argument parser. Maybe extra kind of plugin for augmenting the
# argument parser and arguments themselves are passed over to context
# objects by which they reach the plugins (I am thinking rosdistro
# argument for the rosdistro spec plugin). Keeping plugins single-
# purpose seems like a good idea.

# TODO: rethink 'prefix': don't use environment variable; provide better
# default for sources.d/cache in user home dir (no fhs structure);
# possibly provide option to set sources.d separately; Note: we have a
# suggestion towards this with the `xylem_dir` below, which can be set
# alternative to `prefix` (use prefix in FHS scenario and xylem_dir to
# manage sources/cache in user's home or in temporary directory)

class SourcesContext(object):

    def __init__(self, prefix=None, xylem_dir=None, spec_plugins=None):
        self.setup_paths(prefix, xylem_dir)
        self.spec_plugins = spec_plugins or get_spec_plugin_list()

    def setup_paths(self, prefix=None, xylem_dir=None):
        if prefix and xylem_dir:
            debug("Specifed both prefix '{0}' and xylem dir '{1}'. "
                  "The prefix will be ignored.".format(prefix, xylem_dir))
        if xylem_dir:
            self.xylem_dir = xylem_dir
            self.prefix = None
            self.sources_dir = sources_dir_from_xylem_dir(self.xylem_dir)
            self.cache_dir = cache_dir_from_xylem_dir(self.xylem_dir)
        else:
            self.prefix = prefix or DEFAULT_PREFIX
            self.xylem_dir = None
            self.sources_dir = sources_dir_from_prefix(self.prefix)
            self.cache_dir = cache_dir_from_prefix(self.prefix)

    def ensure_cache_dir(self):
        if not self.cache_dir_exists():
            os.makedirs(self.cache_dir)
        # TODO: check if dir is directory (or link to dir) not file

    def cache_dir_exists(self):
        return os.path.exists(self.cache_dir)
        # TODO: check if dir is directory (or link to dir) not file

    def sources_dir_exists(self):
        return os.path.exists(self.sources_dir)
        # TODO: check if dir is directory (or link to dir) not file

    def is_default_dirs(self):
        return self.prefix == DEFAULT_PREFIX

    def get_spec(self, spec_name):
        for spec in self.spec_plugins:
            if spec.name == spec_name:
                return spec
        raise UnknownSpecError("Spec '{0}' unknown".format(spec_name))
