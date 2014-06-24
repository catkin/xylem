# Software License Agreement (BSD License)
#
# Copyright (c) 2013 - 2014, Open Source Robotics Foundation, Inc.
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
from __future__ import unicode_literals

import os
import pkg_resources

import yaml

from xylem.log_utils import error

from xylem.terminal_color import fmt
from xylem.util import load_yaml
from xylem.text import to_str

SOURCES_GROUP = 'xylem.sources'


def get_default_source_urls():
    """Return the list of default source urls.

    :returns: lists of source urls keyed by spec type
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    files = pkg_resources.resource_listdir(SOURCES_GROUP, 'sources.list.d')
    for file_path in files:
        file_path = os.path.join('sources.list.d', file_path)
        data = pkg_resources.resource_string(SOURCES_GROUP, file_path)
        yield parse_list(data, 'xylem_default_sources:' + file_path)


def get_source_urls(prefix):
    """Return a list of source urls.

    :param prefix: prefix on which to look for etc/xylem/sources.list.d
    :type: prefix: str
    :returns: lists of source urls keyed by spec, or None if no configs
        found
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    if prefix:
        source_list_path = os.path.join(
            prefix, 'etc', 'xylem', 'sources.list.d')
        if os.path.exists(source_list_path):
            return load_source_lists_from_path(source_list_path)
    return get_default_source_urls()


def load_source_lists_from_path(path):
    """Return a list of source urls from a given directory of source lists.

    Only files which have the .yaml extension are processed, other
    files, hidden files, and directories are ignored.

    :param path: directory containing source list files
    :type path: str
    :returns: lists of source urls keyed by spec type
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    return _load_source_lists(
        [os.path.join(path, s) for s in os.listdir(path)])


def _load_source_lists(files):
    for file_path in files:
        if file_path.startswith('.'):
            continue
        if not file_path.endswith('.yaml'):
            continue
        if not os.path.isfile(file_path):
            continue
        yield parse_list_file(file_path)


def parse_list_file(file_path):
    """Parse a given list file and returns a list of source urls.

    :param file_path: path to file containing a list of source urls
    :type file_path: str
    :returns: lists of source urls keyed by spec type
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    """
    with open(file_path, 'r') as f:
        data = f.read()
        return parse_list(to_str(data), file_path)


def parse_list(data, file_path='<string>'):
    """Parse a given list of urls and returns them as a list of source urls.

    :param data: string containing a list of source urls
    :type data: str
    :returns: lists of source urls keyed by spec type
    :rtype: :py:obj:`dict`(:py:obj:`str`: :py:obj:`list`(:py:obj:`str`))
    :raises: ValueError, yaml.YAMLError
    """
    sources_dict = {}
    try:
        sources_dict[file_path] = load_yaml(data)
        if not isinstance(sources_dict, dict):
            raise ValueError("Invalid source list expected dict got '{0}'"
                             .format(type(sources_dict)))
    except ValueError as exc:
        error("Failed to load source list file '{0}': {1}"
              .format(file_path, to_str(exc)))
    except yaml.YAMLError as exc:
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark.line
            col = exc.problem_mark.column
            error(fmt(
                "Invalid YAML in source list file '{0}' at '{1}:{2}': \n@|"
                .format(file_path, mark + 1, col + 1)) + to_str(exc))
        else:
            error(fmt("Invalid YAML in source list file '{0}': \n@|"
                      .format(file_path)) + to_str(exc))
    return sources_dict
