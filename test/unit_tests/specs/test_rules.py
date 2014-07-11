# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pprint import pprint
from copy import deepcopy

from xylem.specs.plugins.rules import expand_rules
from xylem.specs.plugins.rules import compact_rules
from xylem.util import load_yaml


_default_installers = dict(
    ubuntu="apt",
    debian="apt"
)

test1 = load_yaml("""
foo:
  ubuntu: libfoo
  debian: libfoo
bar:
  ubuntu:
    lucid: libbar-1.2
    maverick:
    any_version: libbar
  any_os:
    pip: bar
baz:
  any_os:
    any_version:
        pip: [baz]
  ubuntu: [libbaz, libbaz-dev]
unicöde:
  fedorä:
    schröndinger’s:
      füü:
        [baß]
""")

expected1 = load_yaml("""
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
    maverick:
      default_installer:
        packages: []
    any_version:
      default_installer:
        packages: [libbar]
  any_os:
    any_version:
      pip:
        packages: [bar]
baz:
  any_os:
    any_version:
        pip:
          packages: [baz]
  ubuntu:
    any_version:
      default_installer:
        packages: [libbaz, libbaz-dev]
unicöde:
  fedorä:
    schröndinger’s:
      füü:
        packages: [baß]
""")

expected2 = load_yaml("""
foo:
  ubuntu: [libfoo]
  debian: [libfoo]
bar:
  ubuntu:
    lucid: [libbar-1.2]
    maverick: []
    any_version: [libbar]
  any_os:
    pip: [bar]
baz:
  any_os:
    pip: [baz]
  ubuntu: [libbaz, libbaz-dev]
unicöde:
  fedorä:
    schröndinger’s:
      füü:
        [baß]
""")


def test_rules_expansion():
    # TODO: copy input to expand_rules
    result = expand_rules(deepcopy(test1))
    if result != expected1:
        print("result:")
        pprint(result)
        print("expected:")
        pprint(expected1)
    assert result == expected1


def test_rules_compacting():
    expanded = expand_rules(deepcopy(test1))
    result = compact_rules(deepcopy(expanded), _default_installers)
    result2 = compact_rules(deepcopy(expected1), _default_installers)
    if result != expected2:
        print("result:")
        pprint(result)
        print("expected:")
        pprint(expected2)
    if result2 != expected2:
        print("result:")
        pprint(result2)
        print("expected:")
        pprint(expected2)
    assert result == expected2
    assert result2 == expected2


# test compact expand

# test expand compact


def test_rules_expansion_idempotent():
    # TODO: copy
    expanded = expand_rules(deepcopy(test1))
    result = expand_rules(deepcopy(expanded))
    if result != expanded:
        print("result:")
        pprint(result)
        print("expected:")
        pprint(expanded)
    assert result == expanded
