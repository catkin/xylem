# -*- coding: utf-8 -*-

# TODO: Add module docstring, explaining the structure of (expanded)
# rules dicts, including terminology (rules dict, os dict, version dict,
# installer dict, installer rule), keywords (any_os, any_version,
# default_installer), and merging algorithm of rules files. See
# specs/rules.py docstring and https://github.com/catkin/xylem/issues/9

from __future__ import unicode_literals

import re
import numbers
import six

from xylem.util import raise_from
from xylem.util import text


def verify_rules_dict(rules_dict, allow_default_installer=True):
    """Verify that an expanded rules dict has valid structure.

    :param dict rules_dict: dictionary mapping xylem keys to os dicts
    :param bool allow_default_installer: indicates if
        'default_installer' installer name is allowed
    :raises ValueError: if rules dict does not have valid structure
    """
    if not isinstance(rules_dict, dict):
        raise ValueError("Expected rules dict of type 'dict', but got '{0}'.".
                         format(type(rules_dict)))
    for xylem_key, os_dict in rules_dict.items():
        try:
            verify_xylem_key(xylem_key)
        except ValueError as e:
            raise_from(ValueError, "Expected rules dict to have xylem keys as "
                       "keys.", e)
        try:
            verify_os_dict(os_dict)
        except ValueError as e:
            raise_from(ValueError, "Expected rules dict to have valid os "
                       "dicts as values, but got error for key '{0}'.".
                       format(xylem_key), e)
            raise


def verify_os_dict(os_dict, allow_default_installer=True):
    """Verify that an expanded os dict has valid structure.

    :param dict os_dict: dictionary mapping os names to version dicts
    :param bool allow_default_installer: indicates if
        'default_installer' installer name is allowed
    :raises ValueError: if os dict does not have valid structure
    """
    if not isinstance(os_dict, dict):
        raise ValueError("Expected os dict of type 'dict', but got '{0}'.".
                         format(type(os_dict)))
    for os_name, version_dict in os_dict.items():
        try:
            verify_os_name(os_name)
        except ValueError as e:
            raise_from(ValueError, "Expected os dict to have os names as "
                       "keys.", e)
        try:
            def_inst = allow_default_installer and os_name != 'any_os'
            verify_version_dict(version_dict, allow_default_installer=def_inst)
        except ValueError as e:
            raise_from(ValueError, "Expected os dict to have valid version "
                       "dicts as values, but got error for os '{0}'.".
                       format(os_name), e)


def verify_version_dict(version_dict, allow_default_installer=True):
    """Verify that an expanded version dict has valid structure.

    :param dict version_dict: dictionary mapping os versions to
        installer dicts
    :param bool allow_default_installer: indicates if
        'default_installer' installer name is allowed
    :raises ValueError: if version dict does not have valid structure
    """
    if not isinstance(version_dict, dict):
        raise ValueError("Expected version dict of type 'dict', but got "
                         "'{0}'.".format(type(version_dict)))
    for os_version, installer_dict in version_dict.items():
        try:
            verify_os_version(os_version)
        except ValueError as e:
            raise_from(ValueError, "Expected version dict to have os versions "
                       "as keys.", e)
        try:
            verify_installer_dict(installer_dict, allow_default_installer)
        except ValueError as e:
            raise_from(ValueError, "Expected version dict to have valid "
                       "installer dicts as values, but got error for version "
                       "'{0}'.".format(os_version), e)


def verify_installer_dict(installer_dict, allow_default_installer=True):
    """Verify that an expanded installer dict has valid structure.

    :param dict installer_dict: dictionary mapping installer names to
        installer rules
    :param bool allow_default_installer: indicates if
        'default_installer' installer name is allowed
    :raises ValueError: if installer dict does not have valid structure
    """
    if not isinstance(installer_dict, dict):
        raise ValueError("Expected installer dict of type 'dict', but got "
                         "'{0}'.".format(type(installer_dict)))
    for installer_name, installer_rule in installer_dict.items():
        if not allow_default_installer:
            if installer_name == 'default_installer':
                raise ValueError("Default installer is not allowed here.")
        try:
            verify_installer_name(installer_name)
        except ValueError as e:
            raise_from(ValueError, "Expected installer dict to have installer "
                       "names as keys.", e)
        try:
            verify_installer_rule(installer_rule)
        except ValueError as e:
            raise_from(ValueError, "Expected installer dict to have installer "
                       "rules as values, but got error for installer '{0}.".
                       format(installer_name), e)


def verify_installer_rule(installer_rule):
    """Verify that an expanded installer rule has valid structure.

    :param dict installer_rule: dictionary describing an installer command
    :raises ValueError: if installer rule does not have valid structure
    """
    if not isinstance(installer_rule, dict):
        raise ValueError("Expected installer rule of type 'dict', but got "
                         "'{0}'.".format(type(installer_rule)))
    for key, value in installer_rule.items():
        if not isinstance(key, text):
            raise ValueError("Expected installer rule to have keys of text"
                             " type, but got '{0}'.".format(type(key)))
        # The contents of the installer rule is specific to the
        # according installer plugin, but we check for a few common keys here
        if key == "packages":
            if not isinstance(value, list):
                raise ValueError(
                    "Expected 'packages' entry of installer rule to be of "
                    "type 'list', but got '{0}'".format(type(value)))
        if key == "depends":
            if not isinstance(value, list):
                raise ValueError(
                    "Expected 'depends' entry of installer rule to be of "
                    "type 'list', but got '{0}'".format(type(value)))
            try:
                for xylem_key in value:
                    verify_xylem_key(xylem_key)
            except ValueError as e:
                raise_from(ValueError, "Expected 'depends' entry of installer "
                           "rule to be list of xylem keys.", e)
        if key == "priority":
            try:
                verify_installer_priority(value)
            except ValueError as e:
                raise_from(ValueError, "Expected 'priority' entry of "
                           "installer rule to be installer priority.", e)


def verify_xylem_key(xylem_key):
    """Verify validity of a xylem key.

    :raises ValueError: if ``xylem_key`` is not valid
    """
    _verify_rules_dict_identifier(xylem_key, "xylem key")


def verify_os_name(os_name):
    """Verify validity of a os name.

    :raises ValueError: if ``os_name`` is not valid
    """
    _verify_rules_dict_identifier(os_name, "os name", ["any_os"])


def verify_os_version(os_version):
    """Verify validity of a os version.

    :raises ValueError: if ``os_version`` is not valid
    """
    _verify_rules_dict_identifier(os_version, "os version", ["any_version"])


def verify_installer_name(installer_name):
    """Verify validity of a installer name.

    :raises ValueError: if ``installer_name`` is not valid
    """
    _verify_rules_dict_identifier(
        installer_name, "installer name", ["default_installer"])


def _verify_rules_dict_identifier(identifier, kind, allow_keywords=[]):
    """Helper function to verify validity of identifiers used in rules dicts.

    :param str identifier: the identifier to be validated
    :param str kind: kind of identifier for error messages
    :param list(str) allow_keywords: list of keywords that are allowed
        for this identifier
    :raises ValueError: if ``identifier`` is not valid
    """
    rules_dict_keywords = {'any_os', 'any_version', 'default_installer'}
    if not isinstance(identifier, text):
        raise ValueError("Expected {0} to be text type, but got '{1}'".
                         format(kind, type(identifier)))
    if identifier in rules_dict_keywords - set(allow_keywords):
        raise ValueError("{0} is disallowed keyword '{1}'.".
                         format(kind, identifier))
    if not re.match('(?u)^[\w.’+-]+$', identifier):
        raise ValueError(
            "{0} '{1}' has disallowed characters. Allowed are: alphanumeric, "
            "dash, dot, underscore.".format(kind, identifier))


def verify_installer_priority(priority):
    """Verify validity of an installer priority.

    :raises ValueError: if ``priority`` is not a real number
    """
    if not isinstance(priority, numbers.Real):
        raise ValueError("Expected installer priority to be a real number, "
                         "but got '{0}'.".format(priority))


def merge_rules(rules_dict_list, default_installers):
    """Merge list of rules dicts into one.

    The rules dicts are merged such that the entries in the front of
    ``rules_dict_list`` take precedence. It is assumed that all
    rules dicts are fully expanded and have valid structure.

    The rules dicts are deep copied up to the installer rules, which are
    themselves not deep copied. Therefore, the resulting rules dict
    shares structure with the input rules dicts (namely the installer
    rules themselves).

    The os's in the rules dicts are filtered such that only os names
    that appear as keys of ``default_installers`` appear in the merged
    rules dict.

    'default_installer' installer names are replaced according to
    ``default_installers``.

    :param dict rules_dict_list: list of expanded rules dicts
    :param dict default_installers: dict mapping os names to default
        installer names
    :returns: merged rules dict
    """
    combined_rules = {}
    # an invariant for the following loop is that in the combined rules,
    # os names have already been filtered, and 'default_installer' keys
    # have been replaced.
    # TODO: note this invariant in the called functions as well
    for rules in reversed(rules_dict_list):
        for xylem_key, new_os_dict in rules.items():
            if xylem_key not in combined_rules:
                combined_os_dict = copy_os_dict(
                    new_os_dict, default_installers)
                if combined_os_dict:
                    combined_rules[xylem_key] = combined_os_dict
            else:
                merge_os_dict(
                    new_os_dict, combined_rules[xylem_key], default_installers)
    return combined_rules


def merge_os_dict(new_os_dict, combined_os_dict, default_installers):
    """Merge os dict into an existing one."""
    # first, check for any_os in new_os_dict, since other entries in the
    # new_os_dict overwrite the any_os entry, but the any_os entry
    # overrides existing entries in combined_os_dict
    if "any_os" in new_os_dict:
        new_version_dict = new_os_dict["any_os"]
        new_installer_dict = new_version_dict["any_version"]
        for installer in new_installer_dict.keys():
            # remove any existing rules for installer, as
            # they are overridden by 'any_os'
            installer = replace_default_installer(installer, None)
            remove_rule_for_all_os(combined_os_dict, installer)
        if "any_os" in combined_os_dict:
            merge_installer_dict(
                new_installer_dict,
                combined_os_dict["any_os"]["any_version"],
                None)
        else:
            combined_os_dict["any_os"] = copy_version_dict(
                new_version_dict, None)
    for os, new_version_dict in new_os_dict.items():
        if os not in default_installers:
            continue
        if os not in combined_os_dict:
            combined_os_dict[os] = copy_version_dict(
                new_version_dict, default_installers[os])
        else:
            merge_version_dict(
                new_version_dict, combined_os_dict[os], default_installers[os])


def merge_version_dict(new_version_dict, combined_version_dict,
                       default_installer):
    """Merge version dict into an existing one."""
    # first, check for any_version in new_version_dict, since other
    # entries in new_version_dict override the any_version entry, but
    # the any_version entry overrides existing entries in
    # combined_version_dict
    if "any_version" in new_version_dict:
        new_installer_dict = new_version_dict["any_version"]
        for installer in new_installer_dict.keys():
            installer = replace_default_installer(installer, default_installer)
            remove_rule_for_all_versions(combined_version_dict, installer)
        if "any_version" in combined_version_dict:
            merge_installer_dict(
                new_installer_dict, combined_version_dict["any_version"], None)
        else:
            combined_version_dict["any_version"] = copy_installer_dict(
                new_installer_dict, default_installer)
    for version, new_installer_dict in new_version_dict.items():
        if version not in combined_version_dict:
            combined_version_dict[version] = copy_installer_dict(
                new_installer_dict, default_installer)
        else:
            merge_installer_dict(
                new_installer_dict, combined_version_dict[version],
                default_installer)


def merge_installer_dict(new_installer_dict, combined_installer_dict,
                         default_installer):
    """Merge installer dict into an existing one."""
    for installer_name, installer_rule in new_installer_dict.items():
        installer_name = replace_default_installer(
            installer_name, default_installer)
        combined_installer_dict[installer_name] = installer_rule


def copy_os_dict(os_dict, default_installers):
    """Deep copy os dict up to the installer rules.

    The installer rules themselves are not deep-copied.

    The os's in the os dicts are filtered such that only os names
    that appear as keys of ``default_installers`` appear in the merged
    rules dict.

    'default_installer' installer names are replaced according to
    ``default_installers``.

    :param dict default_installers: dict mapping os names to default
        installer names
    """
    result = {}
    for os, version_dict in os_dict.items():
        if os == 'any_os':
            result[os] = copy_version_dict(
                version_dict, None)
        elif os in default_installers:
            result[os] = copy_version_dict(
                version_dict, default_installers[os])
    return result


def copy_version_dict(version_dict, default_installer):
    """Deep copy version dict up to the installer rules.

    The installer rules themselves are not deep-copied.

    'default_installer' installer names are replaced according to
    ``default_installer``.

    :param str default_installer: name of the default installer for this
        os
    """
    result = {}
    for version, installer_dict in version_dict.items():
        result[version] = copy_installer_dict(
            installer_dict, default_installer)
    return result


def copy_installer_dict(installer_dict, default_installer):
    """Copy installer dict.

    The installer rules themselves are not deep-copied.

    'default_installer' installer names are replaced according to
    ``default_installer``.

    :param str default_installer: name of the default installer
    """
    result = {}
    for installer_name, installer_rule in installer_dict.items():
        installer_name = replace_default_installer(
            installer_name, default_installer)
        result[installer_name] = installer_rule
    return result


def replace_default_installer(installer_name, default_installer_name):
    """Replace the default installer keyword.

    :returns: ``default_installer_name`` if ``installer_name`` is
        'default_installer', else ``installer_name``
    :raises ValueError: if ``default_installer_name`` is None and
        ``installer_name`` is ``default_installer``
    """
    if installer_name == 'default_installer':
        if default_installer_name:
            return default_installer_name
        else:
            raise ValueError(
                "Trying to replace default installer where default installer "
                "is not allowed")
    else:
        return installer_name


def remove_rule_for_all_os(os_dict, installer_name):
    """Remove rules for ``installer_name`` from os dict.

    All rules for installer ``installer_name`` are removed from
    ``os_dict`` for a specific os entries, i.e. except for the rules in
    ``any_os`` entries.

    :param dict os_dict: os dict to be manipulated
    :param str installer_name: name of installer to be removed
    """
    for os_name, version_dict in list(six.iteritems(os_dict)):
        if os_name == "any_os":
            continue
        remove_rule_for_all_versions(
            version_dict, installer_name, retain_any_version=False)
        if not version_dict:
            del os_dict[os_name]


def remove_rule_for_all_versions(
        version_dict, installer_name, retain_any_version=True):
    """Remove rules for ``installer_name`` from version dict.

    All rules for installer ``installer_name`` are removed from
    ``version_dict`` for all specific versions, i.e. except for the
    rules in ``any_version`` entries (if ``retain_any_version`` is
    True).

    :param dict os_dict: os dict to be manipulated
    :param str installer_name: name of installer to be removed
    """
    for version, installer_dict in list(six.iteritems(version_dict)):
        if retain_any_version and version == "any_version":
            continue
        if installer_name in installer_dict:
            del installer_dict[installer_name]
        if not installer_dict:
            del version_dict[version]
