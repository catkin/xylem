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

# TODO: update docstrings

"""Implements the update functionality.

This includes the functions to collect and process source files. Part of
this process is to load and run the spec parser, which are given by name
in the source files.
"""

from __future__ import unicode_literals

from .sources import SourcesContext
from .sources import RulesDatabase


# TODO: remove handle_spec_urls (move some logic into the accoring
# method in Rules database)

# def handle_spec_urls(spec, urls):
#     """Load a given spec parser by spec name and processed all urls.

#     Return a list of new rules dicts from parsed urls.

#     :param str spec: name of a spec parser to load
#     :param urls: list of urls to load for the given spec parser
#     :type urls: :py:obj:`list` of :py:obj:`str`
#     """
#     rules_dict_list = []
#     spec_parser = get_spec_parser(spec)
#     if spec_parser is None:
#         error("Failed to load spec parser for '{0}' spec, skipping."
#               .format(spec))
#         return {}
#     for url in urls:
#         info("Hit {0}".format(url))
#         try:
#             data = load_url(url)
#             rules = spec_parser(data)
#             verify_rules(rules, spec)
#             rules_dict_list.append(rules)
#         except Exception as exc:
#             debug(traceback.format_exc())
#             error("Error: failed to load or parse rule file:")
#             error_lines = [s.rstrip() for s in ('  ' + to_str(exc))
#                            .splitlines()]
#             info('\n  '.join(error_lines))
#     return rules_dict_list


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
    sources_context = SourcesContext(prefix=prefix)
    sources_context.ensure_cache_dir()
    database = RulesDatabase(sources_context)
    database.print_info = True
    # support partial update of local sources even without connectivity:
    database.raise_on_error = False
    database.update()
