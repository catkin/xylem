"""Utility module for dealing with unicode/str/bytes in a uniform way.

This has been inspired by parts of the ``kitchen`` package, which is not
py3 compatible to date.
"""

from __future__ import unicode_literals

import six


text_type = six.text_type


def to_str(obj, encoding='utf-8', errors='replace'):
    """Helper for converting to (unicode) text in py2 and py3."""
    if isinstance(obj, six.text_type):
        return obj
    elif isinstance(obj, six.binary_type):
        return obj.decode(encoding, errors)
    elif isinstance(obj, type):
        return to_str(obj.__name__)
    else:
        value = None
        if six.PY2:
            try:
                value = obj.__unicode__()
            except (AttributeError, UnicodeError, TypeError):
                pass
        if value is None:
            try:
                value = str(obj)
            except UnicodeError:
                try:
                    value = obj.__str__()
                except (AttributeError, UnicodeError):
                    value = ''
        if not isinstance(value, six.text_type):
            value = six.text_type(value, encoding, errors)
        return value


def to_bytes(obj, encoding='utf-8', errors='replace'):
    """Helper for converting to encoded byte-strings in py2 and py3."""
    if isinstance(obj, six.text_type):
        return obj.encode(encoding, errors)
    if isinstance(obj, six.binary_type):
        return obj
    else:
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = obj.__str__()
            except (AttributeError, UnicodeError):
                value = ''
                if six.PY2:
                    try:
                        value = obj.__unicode__()
                    except (AttributeError, UnicodeError):
                        pass
        if isinstance(value, six.text_type):
            value = value.encode(encoding, errors)
        return value
