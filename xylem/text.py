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
        return obj.decode(encoding=encoding, errors=errors)
    else:
        # TODO: possibly add some error handling here if needed
        return six.text_type(obj, encoding=encoding, errors=errors)


def to_bytes(obj, encoding='utf-8', errors='replace'):
    """Helper for converting to encoded byte-strings in py2 and py3."""
    if isinstance(obj, six.text_type):
        return obj.encode(encoding=encoding, errors=errors)
    if isinstance(obj, six.binary_type):
        return obj
    else:
        # TODO: possible add some error handling here if needed
        return six.binary_type(obj, encoding=encoding, errors=errors)
