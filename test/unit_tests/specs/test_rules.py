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
baz:
  any_os:
    any_version:
        pip: [baz]
  ubuntu: [libbaz]
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
baz:
  any_os:
    any_version:
        pip:
          packages: [baz]
  ubuntu:
    any_version:
      default_installer:
        packages: [libbaz]
""")


def test_rules_expansion():
    result = expand_rules(test1)
    if result != expected1:
        print("result:")
        pprint(result)
        print("expected:")
        pprint(expected1)
    assert result == expected1
