"""Unit tests for rules dict merging."""

import yaml

from pprint import pprint

from xylem.specs.rules import expand_rules
from xylem.sources import merge_rules, verify_rules_dict


_default_installers = {
    'osx': 'homebrew',
    'ubuntu': 'apt',
}


def _do_merge_test(rules_dict_list, expected):
    result = merge_rules(rules_dict_list, _default_installers)
    verify_rules_dict(result, allow_default_installer=False)
    if result != expected:
        print("result:")
        pprint(result)
        print("expected:")
        pprint(expected)
        assert result == expected


def _parse_rules(rules_str):
    rules = expand_rules(yaml.load(rules_str))
    verify_rules_dict(rules)
    return rules


def test_merge_rules():
    """Test merging rules dicts: General tests."""
    rules1 = _parse_rules("""
    baz:
        any_os:
            pip: [baz]
    """)

    rules2 = _parse_rules("""
    foo:
        osx:
            any_version:
                homebrew: [foo]
    bar:
        osx:
            mavericks:
                homebrew: [bar]
    """)

    rules3 = _parse_rules("""
    baz:
        ubuntu:
            raring:
                my-installer: [baz]
            quantal: [baz-2]
    """)

    rules4 = _parse_rules("""
    foo:
        osx:
            any_version:
                macports: [foo]
    bar:
        osx:
            any_version:
                macports: [bar]
                fink: [bar]
    """)

    rules5 = _parse_rules("""
    baz:
        ubuntu: [baz]
    """)

    expected1 = _parse_rules("""
    foo:
        osx:
            any_version:
                homebrew: [foo]
                macports: [foo]
    bar:
        osx:
            mavericks:
                homebrew: [bar]
            any_version:
                macports: [bar]
                fink: [bar]
    baz:
        any_os:
            pip: [baz]
        ubuntu:
            any_version:
                apt: [baz]
            raring:
                my-installer: [baz]
            quantal:
                apt: [baz-2]
    """)

    expected2 = _parse_rules("""
    foo:
        osx:
            any_version:
                homebrew: [foo]
                macports: [foo]
    bar:
        osx:
            mavericks:
                homebrew: [bar]
            any_version:
                macports: [bar]
                fink: [bar]
    baz:
        any_os:
            any_version:
                pip: [baz]
        ubuntu:
            any_version:
                apt: [baz]
            raring:
                my-installer: [baz]
    """)

    _do_merge_test([rules1, rules2, rules3, rules4, rules5], expected1)
    _do_merge_test([rules2, rules3, rules4, rules5, rules1], expected1)
    _do_merge_test([rules3, rules4, rules5, rules1, rules2], expected1)
    _do_merge_test([rules4, rules5, rules1, rules2, rules3], expected2)
    _do_merge_test([rules5, rules1, rules2, rules3, rules4], expected2)


def test_merge_rules_any_os_any_version():
    """Test merging rules dicts: any_os overwrites any_version."""
    rules1 = _parse_rules("""
        foo:
            any_os:
                any_version:
                    bar: [foo]
        """)

    rules2 = _parse_rules("""
        foo:
            ubuntu:
                any_version:
                    bar: [foo-2]
        """)

    expected1 = _parse_rules("""
        foo:
            any_os:
                any_version:
                    bar: [foo]
        """)

    expected2 = _parse_rules("""
        foo:
            any_os:
                any_version:
                    bar: [foo]
            ubuntu:
                any_version:
                    bar: [foo-2]
        """)

    _do_merge_test([rules1, rules2], expected1)
    _do_merge_test([rules2, rules1], expected2)


def test_merge_rules_filters_installers():
    """Test merging rules dicts: unknown os names are fileterd out."""
    rules1 = _parse_rules("""
        foo:
            other_os:
                some_version: [foo]
        """)

    rules2 = _parse_rules("""
        foo:
            any_os:
                bar: [foo]
        bar:
            osx:
                any_version:
                    bar: [bar]
            other_os:
                any_version:
                    bar: [bar]
        baz:
            other_os:
                any_version:
                    bar: [baz]
        """)

    expected = _parse_rules("""
        foo:
            any_os:
                any_version:
                    bar: [foo]
        bar:
            osx:
                any_version:
                    bar: [bar]
        """)

    _do_merge_test([rules2], expand_rules(expected))
    _do_merge_test([rules1, rules2], expand_rules(expected))
