# -*- coding: UTF-8 -*-

import yaml

from pprint import pprint

from xylem.specs.rules import expand_rules

test1 = yaml.load("""
foo:
  ubuntu: libfoo
  debian: libfoo
bar:
  ubuntu:
    lucid: libbar-1.2
    any_version: libbar
  any_os:
    pip: bar
baz:
  any_os:
    any_version:
        pip: [baz]
  ubuntu: [libbaz]
unicöde:
  fedorä:
    schröndinger’s:
      füü:
        [baß]
""")

expected1 = yaml.load("""
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
        packages: [libbaz]
unicöde:
  fedorä:
    schröndinger’s:
      füü:
        packages: [baß]
""")


def test_rules_expansion():
    result = expand_rules(test1)
    if result != expected1:
        print("result:")
        pprint(result)
        print("expected:")
        pprint(expected1)
    assert result == expected1


def test_rules_expansion_idempotent():
    expanded = expand_rules(test1)
    result = expand_rules(expanded)
    if result != expanded:
        print("result:")
        pprint(result)
        print("expected:")
        pprint(expanded)
    assert result == expanded
