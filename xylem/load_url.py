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

"""Helper to download content from url."""

from __future__ import unicode_literals

import socket
import time
from six.moves.urllib.error import HTTPError
from six.moves.urllib.error import URLError
from six.moves.urllib.request import urlopen
import cgi

from .text_utils import to_str
from xylem.exception import raise_from
from xylem.exception import XylemError


class DownloadFailure(XylemError):

    """Failure downloading data for I/O or other reasons."""


def load_url(url, retry=2, retry_period=1, timeout=10):
    """Load a given url with retries, retry_periods, and timeouts.

    :param str url: URL to load and return contents of
    :param int retry: number of times to retry the url on 503 or timeout
    :param float retry_period: time to wait between retries in seconds
    :param float timeout: timeout for opening the URL in seconds
    :retunrs: loaded data as string
    :rtype: str
    :raises DownloadFailure: if loading fails even after retries
    """
    retry = max(retry, 0)  # negative retry count causes infinite loop
    while True:
        try:
            req = urlopen(url, timeout=timeout)
        except HTTPError as e:
            if e.code == 503 and retry:
                retry -= 1
                time.sleep(retry_period)
            else:
                raise_from(DownloadFailure, "Failed to load url '{0}'.".
                           format(url), e)
        except URLError as e:
            if isinstance(e.reason, socket.timeout) and retry:
                retry -= 1
                time.sleep(retry_period)
            else:
                raise_from(DownloadFailure, "Failed to load url '{0}'.".
                           format(url), e)
        else:
            break
    _, params = cgi.parse_header(req.headers.get('Content-Type', ''))
    encoding = params.get('charset', 'utf-8')
    data = req.read()
    return to_str(data, encoding=encoding)
