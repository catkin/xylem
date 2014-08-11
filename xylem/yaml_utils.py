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

"""Customize YAML loading and dumping to our needs.

Use these utility function throughout to make sure unicde is handled
correctly and output YAML looks consistent.
"""


from __future__ import unicode_literals


import yaml


def load_yaml(data):
    """Parse a unicode string containing yaml.

    This calls ``yaml.load(data)`` but makes sure unicode is handled correctly.

    See :func:`yaml.load`.

    :raises yaml.YAMLError: if parsing fails"""

    class MyLoader(yaml.SafeLoader):
        def construct_yaml_str(self, node):
            # Override the default string handling function
            # to always return unicode objects
            return self.construct_scalar(node)

    MyLoader.add_constructor(
        'tag:yaml.org,2002:str', MyLoader.construct_yaml_str)

    return yaml.load(data, Loader=MyLoader)


def dump_yaml(data, inline=False):
    """Dump data to unicode string."""

    # TODO: handle `inline` argument properly to produce output on a
    #       single line

    # delay import to prevent circular import
    from .config_utils import ConfigDict

    class MyDumper(yaml.SafeDumper):
        def ignore_aliases(self, _data):
            return True

        def represent_sequence(self, tag, data, flow_style=False):
            # represent lists inline
            return yaml.SafeDumper.represent_sequence(
                self, tag, data, flow_style=True)

        def represent_none(self, data):
            return self.represent_scalar('tag:yaml.org,2002:null', '')

    MyDumper.add_representer(type(None), MyDumper.represent_none)
    MyDumper.add_representer(ConfigDict, MyDumper.represent_dict)

    result = yaml.dump(data,
                       Dumper=MyDumper,
                       # TODO: use this for inline==True ??
                       # default_style=None,
                       default_flow_style=False,
                       allow_unicode=True,
                       indent=2,
                       width=10000000)

    return result
