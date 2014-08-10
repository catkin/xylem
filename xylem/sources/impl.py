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

from xylem.config import DEFAULT_SOURCES_DIR
from xylem.config import DEFAULT_CACHE_DIR
from xylem.config import get_config
from xylem.log_utils import error
from xylem.log_utils import is_verbose
from xylem.log_utils import info
from xylem.yaml_utils import load_yaml
from xylem.exception import raise_from
from xylem.text_utils import to_str
from xylem.specs import verify_spec_name
from xylem.specs import load_spec_plugins
from xylem.exception import XylemError


SOURCES_CACHE_PATH = "sources"
"""Path of sources cache inside the cache dir."""


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


def sources_cache_dir(cache_dir):
    return os.path.join(cache_dir, SOURCES_CACHE_PATH)


# TODO: Introduce CachePermissionError to specifically indicate
# permission problems with creating or manipulating the cache dir


class UnknownSpecError(XylemError):

    pass


# TODO: Should plugins be registered globally (singleton) instead of
# these context objects? How are they supposed to register with the
# argument parser. Maybe extra kind of plugin for augmenting the
# argument parser and arguments themselves are passed over to context
# objects by which they reach the plugins (I am thinking rosdistro
# argument for the rosdistro spec plugin). Keeping plugins single-
# purpose seems like a good idea.


class SourcesContext(object):

    def __init__(self, config=None, spec_plugins=None):
        if config is None:
            config = get_config()
        self.setup_paths(config)
        self.spec_plugins = spec_plugins or load_spec_plugins(
            config.disabled_plugins.spec)

    def setup_paths(self, config):
        self.sources_dir = config.sources_dir or DEFAULT_SOURCES_DIR
        cache_dir = config.cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir = sources_cache_dir(cache_dir)

    def ensure_cache_dir(self):
        if not self.cache_dir_exists():
            os.makedirs(self.cache_dir)
        if not self.cache_dir_exists():
            raise OSError("Could not create cache dir: `{}`".
                          format(self.cache_dir))

    def cache_dir_exists(self):
        return os.path.isdir(self.cache_dir)

    def sources_dir_exists(self):
        return os.path.isdir(self.sources_dir)

    def is_default_dirs(self):
        return (self.sources_dir == DEFAULT_SOURCES_DIR and
                self.cache_dir == sources_cache_dir(DEFAULT_CACHE_DIR))

    def get_spec(self, spec_name):
        for spec in self.spec_plugins:
            if spec.name == spec_name:
                return spec
        raise UnknownSpecError("Spec '{0}' unknown".format(spec_name))
