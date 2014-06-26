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

"""This module implements parsing and validating of rules spec files.

Note: These xylem rules files are compatible with rosdep's files.

xylem Rules File Specification
==============================

First, the top level rules file has these properties:

- The rules file is a YAML 1.1 compliant file
- The rules file contains a single dictionary, the rules dict

the rules dict
^^^^^^^^^^^^^^

The rules dict contains a mapping between xylem keys and definitions for
specific operating systems and package managers.

The rules dict has these properties:

- The keys of the rules dict are package manager agnostic xylem keys
- The values of the rules dict must be a dictionaries also, os
  definition dicts

the os specific definition dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An os specific definition dict is a mapping of operating system names to
os specific definitions. They have these properties:

- It has keys which map to os_names, e.g. ubuntu, osx
- There is a special 'any' key, i.e. 'any_os'
- It can have values of type dict, with os_version keys
- It can have values of type list, a set of packages for the default
  installer
- It can have values of type str, a package for the default installer
- A value of null or '[]' indicates no action is required to resolve for
  this os

When the value is a dict, then the keys of that dict are os_version's
and the values of that dict are os_name and os_version specific
definitions for those xylem keys.

the 'any_os' key
----------------

The 'any_os' key for the os specific definition dict can be used to
indicate that the following definition matches any operating systems.
This is useful for situations like the pip installer, which works on
most operating systems, but is not specific to any one operating system.
When the 'any_os' key is used, then the installer must be specified
explicitly, i.e. no default key is used. Conversely, if the 'any_os' key
is used, then the 'any_version' key must be used for the os_version as
well, which makes sense because it doesn't make sense to have a
definition which matches all operating systems but only a specific
operating system version.

For example, consider this rule snippet::

    foo:
      any_os:
        any_version:
          pip:
            packages: [foo]
      ubuntu: [python-foo]
      debian: [python-foo]
      osx:
        any_version:
          homebrew: [foo]

In this case ``foo`` will be resolved like this::

    windows:7         -> pip:foo
    ubuntu:precise    -> apt:python-foo
    debian:wheezy     -> apt:python-foo
    osx:mountain_lion -> homebrew:foo

You can imagine the logic to implement this behavior as such::

    # foo_dict is a dictionary like the above YAML structure
    os_name = get_os_name()
    os_version = get_os_version()
    if os_name in foo_dict:
        if os_version in foo_dict[os_name]:
            return foo_dict[os_name][os_version]
        elif 'any_version' in foo_dict[os_name]:
            return foo_dict[os_name]['any_version']
    elif 'any_os' in foo_dict:
        if 'any_version' in foo_dict['any_os']:
            return foo_dict['any_os']['any_version']
    raise NotFound

list and string expansion into os_version's any_version
-------------------------------------------------------

When the value of the os definition dict is a str, then it is converted
into a list containing that str.

Whether the value is a str converted into a list or originally a list,
the list is expanded into an any version ('any_version') key-value pair,
where the list is the value. Then the processing continues as normal.

For example, this snippet::

    foo:
      ubuntu: [libfoo]

is expanded to::

    foo:
      ubuntu:
        any_version: [libfoo]

The above snippet is a intermediate expansion, as ``any_version:
[libfoo]`` will get expanded further later.

The case where no action is required, can occur when the package exists
on the system by default. For example, on OS X many times the software
package comes with OS X and no action is required for it to be resolved.
This is represented with an empty list or null.

Whether originally a dict or expanded to a dict from a list, the
resulting os specific definition dict always has os_names for keys and
os_version specific definitions as values.

the os_version specific definition dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The os_version specific definition dict's have these properties:

- It has keys which map to os_version's for the parent os_name.
- There can be one any_version key, i.e. 'any_version'
- The values can be a list or str, and are converted like the os
  definition dict
- The final values must be an installer specific definition dict

The os_version specific definition dict's are exactly like the os_name
specific definition dict's, except that the resulting values are
installer specific definition dict's, and there is a wild card key.

the 'any_version' key
---------------------

The any_version key, 'any_version', indicates that the value, which is
an installer specific definition dict, applies to all os_version's which
do not have an explicit definition. For example, consider this snippet::

    foo:
      ubuntu:
        lucid: [libfoo-1.8]
        any_version: [libfoo]

The above snippet will provide ``libfoo-1.8`` if you ask xylem to
resolve ``foo`` for ``ubuntu:lucid``, but will return ``libfoo`` for any
other version of ``ubuntu``, e.g. for ``ubuntu:precise`` xylem will
resolve it as ``libfoo``.

the installer specific definition dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The installer specific definition dict has keys for installers, e.g.
``apt``, ``pip``, or ``homebrew``. The installer specific definition
dict is similar to the os_version specific definition dict except the
default_installer key is interpreted differently.

the 'default_installer' key
---------------------------

When the default installer key, 'default_installer', is used in the
installer specific definition dict, that indicates that the following
definition is for the *default* installer for that operating system.
This key cannot be used under the `any_os` key.


Examples
========

Basic::

    foo:  # xylem key
      ubuntu:  # os name
        precise:  # os version (or codename)
          apt:  # installer
            packages: [libfoo]  # packages are a list

This is an example of using some of the available shortcuts::

    foo:
      ubuntu: libfoo
      debian: libfoo
    bar:
      ubuntu:
        lucid: libbar-1.2
        any_version: libbar
    baz:
      any_os:
        any_version:
            pip: [baz]
      ubuntu: [libbaz]

Which expands to::

    foo:
      ubuntu:
        any_version:
          default_installer:
            packages: [libfoo]
      debian:
        any_version:
          default_installer:
            packages: [libfoo]
    bar:
      ubuntu:
        lucid:
          default_installer:
            packages: [libbar-1.2]
        any_version:
          default_installer:
            packages: [libbar]
    baz:
      any_os:
        any_version:
            pip:
              packages: [baz]
      ubuntu:
        any_version:
          default_installer:
            packages: [libbaz]
"""

# TODO: Update doc: for any_os only allow any_version
# TODO: Update doc: for any_os disallow default_installer


from __future__ import print_function
from __future__ import unicode_literals

import yaml

from xylem.specs import SpecParsingError

from xylem.util import load_yaml

from xylem.text_utils import text_type


def expand_definition(definition):
    if not isinstance(definition, (text_type, list, dict, type(None))):
        raise ValueError("Invalid installer specific definition, expected "
                         "dict, list, string, or null but got '{0}'"
                         .format(type(definition)))
    if definition is None:
        definition = []
    if isinstance(definition, text_type):
        # Up convert the str to a list
        definition = [definition]
    if isinstance(definition, list):
        # Convert to an default_installer dict
        definition = {'packages': definition}
    return definition


def expand_installer_definition(installer_dict):
    if not isinstance(installer_dict, (text_type, list, dict, type(None))):
        raise ValueError("Invalid installer specific definition, expected "
                         "dict, list, string, or null but got '{0}'"
                         .format(type(installer_dict)))
    if installer_dict is None:
        installer_dict = []
    if isinstance(installer_dict, text_type):
        # Up convert the str to a list
        installer_dict = [installer_dict]
    if isinstance(installer_dict, list):
        # Convert to an default_installer dict
        installer_dict = {'default_installer': installer_dict}
    for name, definition in installer_dict.items():
        installer_dict[name] = expand_definition(definition)
    return installer_dict


def expand_os_version_definition(os_name, version_dict):
    if not isinstance(version_dict, (text_type, list, dict, type(None))):
        raise ValueError("Invalid os version specific definition, expected "
                         "dict, list, string, or null but got '{0}'"
                         .format(type(version_dict)))
    if version_dict is None:
        version_dict = []
    if isinstance(version_dict, text_type):
        # Up convert the str to a list
        version_dict = [version_dict]
    if isinstance(version_dict, list):
        # Convert to an any_version dict
        version_dict = {'any_version': version_dict}
    if os_name == "any_os":
        if "any_version" in version_dict:
            if not len(version_dict) == 1:
                raise ValueError(
                    "'any_os' entry may only have 'any_version' version keys, "
                    "but got '{0}'".format(version_dict.keys()))
        else:
            # Interpret as installer_dict
            version_dict = {"any_version": version_dict}
    for name, installer_dict in version_dict.items():
        version_dict[name] = expand_installer_definition(installer_dict)
    return version_dict


def expand_os_definition(os_dict):
    if not isinstance(os_dict, dict):
        raise ValueError(
            "Invalid os specific definition, expected dict but got '{0}'".
            format(type(os_dict)))
    for os_name, version_dict in os_dict.items():
        os_dict[os_name] = expand_os_version_definition(os_name, version_dict)
    return os_dict

# TODO: for `any_os`, interpret dictionaries that are not `any_version`
# as installers

# `ubuntu: pip: [foo]` does not work and needs any_version. Should rule
# expansion make use of known installers/os_versions, or not? If not, it
# should at least use loaded installers to detect potential errors.


def expand_rules(rules):
    if not isinstance(rules, dict):
        raise ValueError("Invalid rules set, expected dict got '{0}'"
                         .format(type(rules)))
    for xylem_key, os_dict in rules.items():
        # Store the (possibly) updated os_dict
        try:
            rules[xylem_key] = expand_os_definition(os_dict)
        except ValueError as exc:
            raise SpecParsingError("Failed to expand rule for '{0}': {1}"
                                   .format(xylem_key, exc),
                                   yaml.dump({xylem_key: os_dict}))
    return rules


def rules_spec_parser(data):
    rules = load_yaml(data)
    rules = expand_rules(rules)
    return rules
