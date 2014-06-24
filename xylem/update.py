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

"""Implements the update functionality.

This includes the functions to collect and process source files. Part of
this process is to load and run the spec parser, which are given by name
in the source files.
"""

from __future__ import print_function
from __future__ import unicode_literals

import socket
import time
import traceback
import urllib2
import cgi

from xylem.util import raise_from

from xylem.text import to_str

from xylem.log_utils import debug
from xylem.log_utils import error
from xylem.log_utils import info

from xylem.sources import get_default_source_urls
from xylem.sources import get_source_urls
from xylem.sources import merge_rules
from xylem.sources import verify_rules_dict

from xylem.specs import get_spec_parser


def load_url(url, retry=2, retry_period=1, timeout=10):
    """Load a given url with retries, retry_periods, and timeouts.

    Based on https://github.com/ros-infrastructure/rosdistro/blob/\
master/src/rosdistro/loader.py

    :param url: URL to load and return contents of
    :type url: str
    :param retry: number of times to retry the url on 503 or timeout
    :type retry: int
    :param retry_period: time to wait between retries in seconds
    :type retry_period: float
    :param timeout: timeout for opening the URL in seconds
    :type timeout: float
    :rtype: str
    """
    retry = max(retry, 0)  # negative retry count causes infinite loop
    while True:
        try:
            req = urllib2.urlopen(url, timeout=timeout)
        except urllib2.HTTPError as e:
            if e.code == 503 and retry:
                retry -= 1
                time.sleep(retry_period)
            else:
                raise_from(IOError, "Failed to load url '{0}'.".format(url), e)
        except urllib2.URLError as e:
            if isinstance(e.reason, socket.timeout) and retry:
                retry -= 1
                time.sleep(retry_period)
            else:
                raise_from(IOError, "Failed to load url '{0}'.".format(url), e)
        else:
            break
    _, params = cgi.parse_header(req.headers.get('Content-Type', ''))
    encoding = params.get('charset', 'utf-8')
    data = req.read()
    return to_str(data, encoding=encoding)


def verify_rules(rules, spec):
    """Verify that a set of rules are valid for internal storage.

    :param dict rules: set of nested dictionaries which is the internal
        DB format
    """
    verify_rules_dict(rules)


def handle_spec_urls(spec, urls):
    """Load a given spec parser by spec name and processed all urls.

    Return a list of new rules dicts from parsed urls.

    :param str spec: name of a spec parser to load
    :param urls: list of urls to load for the given spec parser
    :type urls: :py:obj:`list` of :py:obj:`str`
    """
    rules_dict_list = []
    spec_parser = get_spec_parser(spec)
    if spec_parser is None:
        error("Failed to load spec parser for '{0}' spec, skipping."
              .format(spec))
        return {}
    for url in urls:
        info("Hit {0}".format(url))
        try:
            data = load_url(url)
            rules = spec_parser(data)
            verify_rules(rules, spec)
            rules_dict_list.append(rules)
        except Exception as exc:
            debug(traceback.format_exc())
            error("Error: failed to load or parse rule file:")
            error_lines = [s.rstrip() for s in ('  ' + to_str(exc))
                           .splitlines()]
            info('\n  '.join(error_lines))
    return rules_dict_list


def update(prefix=None, dry_run=False):
    """Update the xylem cache.

    If the prefix is set then the source lists are searched for in the
    prefix. If the prefix is not set (None) or the source lists are not
    found in the prefix, then the default, builtin source list is used.

    :param prefix: The config and cache prefix, usually '/' or someother
        prefix
    :type prefix: :py:obj:`str` or :py:obj:`None`
    :param dry_run: If True, then no actual action is taken, only
        pretend to
    :type dry_run: bool
    """
    sources_gen = get_source_urls(prefix)
    rules_dict_list = []
    if sources_gen is None:
        if prefix is not None:
            debug("No configs found in prefix '{0}', using default sources."
                  .format(prefix))
        sources_gen = get_default_source_urls()
    for source_list_dict in sources_gen:
        for source_list_file, list_of_spec_dicts in source_list_dict.items():
            info("Processing '{0}'...".format(source_list_file))
            for spec_dict in list_of_spec_dicts:
                for spec, urls in spec_dict.items():
                    rules_dict_list.extend(handle_spec_urls(spec, urls))
    from pprint import pprint
    # Merging here is just a temporary debugging hack:
    from xylem.os_support import OSSupport
    o = OSSupport()
    pprint(merge_rules(rules_dict_list, o.get_default_installer_names()))
