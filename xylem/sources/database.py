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
from __future__ import print_function

import os
import hashlib
import datetime

import six.moves.cPickle as pickle

from xylem import __version__
from xylem.log_utils import error
from xylem.log_utils import warning
from xylem.log_utils import info
from xylem.log_utils import is_verbose
from xylem.log_utils import debug
from .impl import get_default_source_descriptions
from .impl import get_source_descriptions
from xylem.text_utils import to_str
from xylem.sources.rules_dict import verify_installer_dict
from xylem.sources.rules_dict import merge_installer_dict


# TODO: Docstrings for RulesSource and RulesDatabase


def _id_string(unique_id):
    return hashlib.sha1(unique_id).hexdigest()


def _cache_file_path(cache_dir, unique_id):
    path = os.path.join(cache_dir, _id_string(unique_id) + ".pickle")
    return path


def _create_cache_data(xylem_version,
                       spec_name,
                       spec_version,
                       arguments,
                       origin,
                       data,
                       time_data_loaded):
    cache_data = dict(
        xylem_version=xylem_version,
        spec_name=spec_name,
        spec_version=spec_version,
        arguments=arguments,
        origin=origin,
        data=data,
        time_data_loaded=time_data_loaded
    )
    return cache_data


def _verify_cache_data_structure(cache_data):
    if not (isinstance(cache_data, dict) and
            'xylem_version' in cache_data and
            'spec_name' in cache_data and
            'spec_version' in cache_data and
            'arguments' in cache_data and
            'origin' in cache_data and
            'data' in cache_data and
            'time_data_loaded' in cache_data):
        raise ValueError(
            "Cache data has invalid structure: '{0}'".format(cache_data))


def _verify_cache_data_spec_name(cache_data, spec_name):
    if spec_name != cache_data['spec_name']:
        raise ValueError("Expected spec name '{0}' for cache data, but got "
                         "'{1}'.".format(spec_name, cache_data['spec_name']))


def _read_cache(filepath):
    with open(filepath, 'rb') as f:
        cache_data = pickle.load(f)
        _verify_cache_data_structure(cache_data)
        return cache_data


def _write_cache(cache_data, filepath):
    with open(filepath, 'wb') as f:
        # protocol 2 is compatible with python 2 and 3
        pickle.dump(cache_data, f, protocol=2)


class RulesSource(object):

    def __init__(self, spec, arguments, origin, sources_context):
        self.spec = spec
        self.arguments = arguments
        self.origin = origin
        self.sources_context = sources_context
        self.data = None
        self.time_data_loaded = None

        self.spec.verify_arguments(self.arguments)

    def unique_id(self):
        return self.spec.unique_id(self.arguments)

    def cache_file_path(self):
        path = _cache_file_path(self.sources_context.cache_dir,
                                self.unique_id())
        return path

    def load_from_source(self):
        data = self.spec.load_data(self.arguments)
        self.spec.verify_data(data, self.arguments)
        self.data = data
        self.time_data_loaded = datetime.datetime.now()

    def load_from_cache(self):
        cache_data = _read_cache(self.cache_file_path())
        _verify_cache_data_spec_name(cache_data, self.spec.name)
        self.spec.verify_arguments(self.arguments)
        self.spec.verify_data(cache_data['data'], self.arguments)
        self.arguments = cache_data['arguments']
        self.origin = cache_data['origin']
        self.data = cache_data['data']
        self.time_data_loaded = cache_data['time_data_loaded']

    def save_to_cache(self):
        cache_data = _create_cache_data(
            __version__,
            self.spec.name,
            self.spec.version,
            self.arguments,
            self.origin,
            self.data,
            self.time_data_loaded)
        cache_path = self.cache_file_path()
        _write_cache(cache_data, cache_path)

    def is_cache_outdated(self):
        if not self.is_cache_available():
            return True
        cache_data = _read_cache(self.cache_file_path())
        # here we could also check xylem version if needed in the future
        if self.spec.name != cache_data('spec_name'):
            return True
        return self.spec.is_data_outdated(cache_data['data'], self.arguments)

    def is_cache_available(self):
        path = self.cache_file_path()
        if os.path.isfile(path):
            return True
        return False

    def clear_cache(self):
        """Remove cache file.

        :raises OSError: if cache file cannot be removed
        """
        path = self.cache_file_path(self.sources_context)
        if os.path.exists(path):
            if is_verbose():
                info("Removing cache file '%s'.", path)
            os.remove(path)
        else:
            if is_verbose():
                info("Cache file '%s' already clear.", path)

    def lookup(self, xylem_key, installer_context):
        installer_dict = self.spec.lookup(
            self.data, xylem_key, installer_context)
        verify_installer_dict(installer_dict, allow_default_installer=False)
        return installer_dict

    def keys(self, installer_context):
        """Return list of keys defined for current os/version."""
        return self.spec.keys(self.data, installer_context)


class RulesDatabase(object):

    def __init__(self, sources_context):
        self.sources_context = sources_context
        self.sources = None  # Note: assuming those have unique ids
        self.init_from_sources()
        self.print_info = False
        self.raise_on_error = True

    def init_from_sources(self):
        debug("initializing database with sources dir `{}` and cache dir `{}`".
              format(self.sources_context.sources_dir,
                     self.sources_context.cache_dir))
        self.sources = []
        sources_dir = self.sources_context.sources_dir
        sources_gen = get_source_descriptions(sources_dir)
        if sources_gen is None:
            if not self.sources_context.is_default_dirs():
                warning("no source files found in source dir '{0}'; "
                        "using default sources".format(sources_dir))
            if is_verbose():
                info("Loading default source urls")
            sources_gen = get_default_source_descriptions()
        for source_file, source_descriptions in sources_gen:
            for descr in source_descriptions:
                spec_name, arguments = descr.items()[0]
                spec = self.sources_context.get_spec(spec_name)
                self.sources.append(RulesSource(
                    spec,
                    arguments,
                    source_file,
                    self.sources_context))
        self.verify_unique_ids()

    def verify_unique_ids(self):
        ids = [_id_string(s.unique_id()) for s in self.sources]
        if not len(ids) == len(set(ids)):
            # TODO: use custom Exception type
            raise RuntimeError(
                "Source ids in rules database are not unique: {0}".format(ids))

    def load_from_cache(self):
        for source in self.sources:
            try:
                source.load_from_cache()
            except Exception as e:
                # TODO: be more specific about which exceptions to catch here
                if self.raise_on_error:
                    raise
                else:
                    error("Failed to load source '{0}' from cache:\n{1}".
                          format(source.unique_id(), e))

    def save_to_cache(self):
        for source in self.sources:
            try:
                source.save_to_cache()
            except Exception as e:
                # TODO: be more specific about which exceptions to catch here
                if self.raise_on_error:
                    raise
                else:
                    error("Failed to save source '{0}' to cache:\n{1}".
                          format(source.unique_id(), e))

    def load_from_source(self):
        origins = set()
        for source in self.sources:
            if source.origin not in origins:
                origins.add(source.origin)
                if self.print_info:
                    info("Processing '{0}'...".format(source.origin))
            if self.print_info:
                info("Loading: {0} : {1}".
                     format(source.spec.name, source.arguments))
            try:
                source.load_from_source()
            except Exception as e:
                # TODO: be more specific about which exceptions to catch here
                if self.raise_on_error:
                    raise
                else:
                    error("Failed to load source '{0}':\n{1}".
                          format(source.unique_id(), e))

    def update(self):
        # TODO: save exceptions if they are not raised and then for the
        # cli command recognize permission errors and suggest to use
        # 'sudo'

        # We don't just call `load_from_source` and `save_to_cache` here
        # since we want errors with saving for each source to happen
        # directly after loading, not at the end.
        origins = set()
        for source in self.sources:
            if source.origin not in origins:
                origins.add(source.origin)
                if self.print_info:
                    info("Processing '{0}'...".format(source.origin))
            if self.print_info:
                info("Loading: {0} : {1}".
                     format(source.spec.name, source.arguments))
            try:
                source.load_from_source()
            except Exception as e:
                # TODO: be more specific about which exceptions to catch here
                if self.raise_on_error:
                    raise
                else:
                    error("Failed to load source '{0}':\n{1}".
                          format(source.unique_id(), e))
            else:
                try:
                    source.save_to_cache()
                except Exception as e:
                    # TODO: be more specific about which exceptions to catch
                    if self.raise_on_error:
                        raise
                    else:
                        error("Failed to save source '{0}' to cache:\n{1}".
                              format(source.unique_id(), to_str(e)))

    def lookup(self, xylem_key, installer_context):
        """Return rules for xylem key in current os."""
        installer_dict = {}
        # TODO: merge the other way round
        # TODO: catch errors down the line and wrap in meaningful LookupError
        for source in reversed(self.sources):
            new_rules = source.lookup(xylem_key, installer_context)
            merge_installer_dict(new_rules, installer_dict, None)
        return installer_dict

    def keys(self, installer_context):
        """Return list of keys defined for current os/version."""
        keys = set()
        for source in self.sources:
            keys.update(set(source.keys(installer_context)))
        return list(keys)
