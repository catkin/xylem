# Copyright 2014 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Exception classes for error handling xylem."""


from __future__ import unicode_literals


# TODO: Do we keep _all_ exceptions here or just the ones that are used
# by multiple submodules?


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


class DownloadFailure(Exception):

    """Failure downloading data for I/O or other reasons."""

    pass


class InstallerNotAvailable(Exception):

    """Failure indicating a installer is not installed."""

    pass


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
