# -*- coding: utf-8 -*-

"""Unit tests for rules dict merging."""

from __future__ import unicode_literals

from pprint import pprint

from xylem.specs.plugins.rules import expand_rules

from xylem.specs.rules_dict import merge_rules
from xylem.specs.rules_dict import verify_rules_dict

from xylem.util import load_yaml


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
    rules = expand_rules(load_yaml(rules_str))
    verify_rules_dict(rules)
    return rules


def test_merge_rules():
    """Test merging rules dicts: General tests."""
    rules1 = _parse_rules("""
    baß:
        any_os:
            pip: [baß]
    """)

    rules2 = _parse_rules("""
    füü:
        osx:
            any_version:
                homebrew: [füü]
    bar:
        osx:
            mavericks:
                homebrew: [bar]
    """)

    rules3 = _parse_rules("""
    baß:
        ubuntu:
            raring:
                my-installer: [baß]
            quantal: [baß-2]
    """)

    rules4 = _parse_rules("""
    füü:
        osx:
            any_version:
                macports: [füü]
    bar:
        osx:
            any_version:
                macports: [bar]
                fink: [bar]
    """)

    rules5 = _parse_rules("""
    baß:
        ubuntu: [baß]
    """)

    expected1 = _parse_rules("""
    füü:
        osx:
            any_version:
                homebrew: [füü]
                macports: [füü]
    bar:
        osx:
            mavericks:
                homebrew: [bar]
            any_version:
                macports: [bar]
                fink: [bar]
    baß:
        any_os:
            pip: [baß]
        ubuntu:
            any_version:
                apt: [baß]
            raring:
                my-installer: [baß]
            quantal:
                apt: [baß-2]
    """)

    expected2 = _parse_rules("""
    füü:
        osx:
            any_version:
                homebrew: [füü]
                macports: [füü]
    bar:
        osx:
            mavericks:
                homebrew: [bar]
            any_version:
                macports: [bar]
                fink: [bar]
    baß:
        any_os:
            any_version:
                pip: [baß]
        ubuntu:
            any_version:
                apt: [baß]
            raring:
                my-installer: [baß]
    """)

    _do_merge_test([rules1, rules2, rules3, rules4, rules5], expected1)
    _do_merge_test([rules2, rules3, rules4, rules5, rules1], expected1)
    _do_merge_test([rules3, rules4, rules5, rules1, rules2], expected1)
    _do_merge_test([rules4, rules5, rules1, rules2, rules3], expected2)
    _do_merge_test([rules5, rules1, rules2, rules3, rules4], expected2)


def test_merge_rules_any_os_any_version():
    """Test merging rules dicts: any_os overwrites any_version."""
    rules1 = _parse_rules("""
        füü:
            any_os:
                any_version:
                    bar: [füü]
        """)

    rules2 = _parse_rules("""
        füü:
            ubuntu:
                any_version:
                    bar: [füü-2]
        """)

    expected1 = _parse_rules("""
        füü:
            any_os:
                any_version:
                    bar: [füü]
        """)

    expected2 = _parse_rules("""
        füü:
            any_os:
                any_version:
                    bar: [füü]
            ubuntu:
                any_version:
                    bar: [füü-2]
        """)

    _do_merge_test([rules1, rules2], expected1)
    _do_merge_test([rules2, rules1], expected2)


def test_merge_rules_filters_installers():
    """Test merging rules dicts: unknown os names are fileterd out."""
    rules1 = _parse_rules("""
        füü:
            other_os:
                some_version: [füü]
        """)

    rules2 = _parse_rules("""
        füü:
            any_os:
                bar: [füü]
        bar:
            osx:
                any_version:
                    bar: [bar]
            other_os:
                any_version:
                    bar: [bar]
        baß:
            other_os:
                any_version:
                    bar: [baß]
        """)

    expected = _parse_rules("""
        füü:
            any_os:
                any_version:
                    bar: [füü]
        bar:
            osx:
                any_version:
                    bar: [bar]
        """)

    _do_merge_test([rules2], expand_rules(expected))
    _do_merge_test([rules1, rules2], expand_rules(expected))
