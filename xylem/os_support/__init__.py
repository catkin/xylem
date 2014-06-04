"""Module to manage OS plugins and their use for OS detection."""

from .impl import OSSupport, UnsupportedOSError

__all__ = ["OSSupport", "UnsupportedOSError"]
