"""Module to manage OS plugins and their use for OS detection."""
from __future__ import unicode_literals

from .impl import OS, OSSupport, UnsupportedOSError

__all__ = ["OS", "OSSupport", "UnsupportedOSError"]
