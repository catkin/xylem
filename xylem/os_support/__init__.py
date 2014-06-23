"""Module to manage OS plugins and their use for OS detection."""
from __future__ import unicode_literals

from .impl import OSSupport, UnsupportedOSError

__all__ = ["OSSupport", "UnsupportedOSError"]
