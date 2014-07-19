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
