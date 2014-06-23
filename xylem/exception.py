"""Exception classes for error handling xylem."""

from __future__ import print_function
from __future__ import unicode_literals


class InvalidDataError(Exception):

    """Data is not in valid xylem format."""


class InvalidPluginError(Exception):

    """Plugin loaded from an entry point does not have the right type/data."""


# class RosdepInternalError(Exception):

#     def __init__(self, e, message=None):
#         self.error = e
#         if message is None:
#             self.message = traceback.format_exc()
#         else:
#             self.message = message

#     def __str__(self):
#         return self.message


# class DownloadFailure(Exception):

#     """Failure downloading sources list data for I/O or other reasons."""

#     pass


# class InstallFailed(Exception):

#     def __init__(self, failure=None, failures=None):
#         """
#         One of failure/failures must be set.

#         :param failure: single (installer_key, message) tuple.
#         :param failures: list of (installer_key, message) tuples
#         """
#         if failures is not None:
#             self.failures = failures
#         elif not failure:
#             raise ValueError("failure is None")
#         else:
#             self.failures = [failure]

#     def __str__(self):
#         return '\n'.join(
#             ['%s: %s' % (key, message) for (key, message) in self.failures])
