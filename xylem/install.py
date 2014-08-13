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

from __future__ import unicode_literals

import subprocess
import six

from xylem.config import ensure_config

from xylem.installers import ensure_installer_context
from xylem.installers import InstallerError

from xylem.resolve import resolve

from xylem.exception import raise_from
from xylem.exception import chain_exception
from xylem.exception import XylemError
from xylem.exception import XylemInternalError

from xylem.log_utils import info
from xylem.log_utils import info_v
from xylem.log_utils import error

from xylem.util import remove_duplicates

from xylem.terminal_color import fmt


class InstallError(XylemError):

    """Exception for failed installation of packages."""


# TODO: Docstrings with terminology: `resolutions` -> list of resolution
#       objects; `resolution_tuple` -> (inst-name, resolutions);
#       `resolved` -> list of resolution tuples


def install(xylem_keys,
            all_keys=False,
            interactive=True,
            reinstall=False,
            simulate=False,
            continue_on_error=False,
            fix_prerequisites=False,
            config=None,
            database=None,
            sources_context=None,
            installer_context=None):
    #  1. Prepare config and contexts and load database
    config = ensure_config(config)
    installer_context = ensure_installer_context(installer_context, config)

    #  2. Resolve keys
    results, resolve_errors = resolve(xylem_keys,
                                      all_keys=all_keys,
                                      config=config,
                                      database=database,
                                      sources_context=sources_context,
                                      installer_context=installer_context)

    resolved = _squash_resolutions(res_tuple for _, res_tuple in results)

    #  3. check general prerequisites for all installers
    check_general_prerequisites(_installer_names(resolved),
                                installer_context,
                                fix_unsatisfied=fix_prerequisites,
                                interactive=interactive)

    #  4. Determine uninstalled resolutions
    if not reinstall:
        resolved, uninstalled_errors = filter_uninstalled(
            resolved, installer_context)
        # TODO: figure out what exactly to do with these errors... For
        #       now print them here
        for err in uninstalled_errors:
            error(exc_to_str(uninstalled_errors))

    if uninstalled_errors and not continue_on_error:
        return resolve_errors, []

    #  5. check prerequisites all resolutions to be installed
    check_install_prerequisites(_map_resolutions(resolved),
                                installer_context,
                                fix_unsatisfied=fix_prerequisites,
                                interactive=interactive)

    #  6. Install resolved items
    install_errors = install_resolved(resolved,
                                      installer_context,
                                      interactive=interactive,
                                      reinstall=reinstall,
                                      simulate=simulate,
                                      continue_on_error=continue_on_error)

    return resolve_errors, install_errors


def _installer_names(resolved):
    return remove_duplicates(name for name, _ in resolved)


def _map_resolutions(resolved):
    result = {}
    for installer_name, resolutions in resolved:
        if installer_name not in result:
            result[installer_name] = []
        result[installer_name].extend(resolutions)
    return result


def _squash_resolutions(resolved):
    squashed = []
    previous_installer_name = None
    for installer_name, resolutions in resolved:
        if previous_installer_name != installer_name:
            squashed.append((installer_name, []))
            previous_installer_name = installer_name
        squashed[-1][1].extend(resolutions)
    return squashed


def check_general_prerequisites(installer_names,
                                installer_context,
                                fix_unsatisfied,
                                interactive):
    os_tuple = installer_context.get_os_tuple()
    for installer_name in installer_names:
        installer = installer_context.lookup_installer(installer_name)
        if installer is None:
            raise XylemInternalError("did not find resolved installer '{}'".
                                     format(installer_name))
        installer.check_general_prerequisites(
            os_tuple,
            fix_unsatisfied=fix_unsatisfied,
            interactive=interactive)


def check_install_prerequisites(resolutions_map,
                                installer_context,
                                fix_unsatisfied,
                                interactive):
    os_tuple = installer_context.get_os_tuple()
    for installer_name, resolutions in six.iteritems(resolutions_map):
        installer = installer_context.lookup_installer(installer_name)
        if installer is None:
            raise XylemInternalError("did not find resolved installer '{}'".
                                     format(installer_name))
        installer.check_install_prerequisites(
            resolutions,
            os_tuple,
            fix_unsatisfied=fix_unsatisfied,
            interactive=interactive)


def filter_uninstalled(resolved, installer_context):
    errors = []
    uninstalled = []
    for installer_name, resolutions in resolved:
        installer = installer_context.lookup_installer(installer_name)
        if installer is None:
            raise XylemInternalError("did not find resolved installer '{}'".
                                     format(installer_name))
        try:
            resolutions = installer.filter_uninstalled(resolutions)
        except InstallerError as e:  # TODO: does this here make sense?
            errors.append(chain_exception(
                InstallError, "installer '{}' failed to determine "
                "uninstalled resolutions out of {}".
                format(installer_name, resolutions), e))
        except Exception as e:
            raise_from(
                XylemInternalError, "unexpected error in installer '{}' "
                "while trying to determine uninstalled resolutions out of {}".
                format(installer_name, resolutions), e)
        # only create a tuple if there is something to do
        if resolutions:
            uninstalled.append((installer_name, resolutions))
    return uninstalled, errors


def install_resolved(resolved,
                     installer_context,
                     interactive=True,
                     reinstall=False,
                     simulate=False,
                     continue_on_error=False):

    # Squash (again, in case some tuples have been filtered out)
    resolved = _squash_resolutions(resolved)

    all_errors = []
    for installer_name, resolutions in resolved:
        errors = install_resolutions(
            installer_name,
            resolutions,
            installer_context,
            simulate=simulate,
            interactive=interactive,
            reinstall=reinstall,
            continue_on_error=continue_on_error)
        if errors and not continue_on_error:
            return errors
        all_errors.extend(errors)
    return all_errors


def install_resolutions(installer_name,
                        resolutions,
                        installer_context,
                        interactive=True,
                        reinstall=False,
                        simulate=False,
                        continue_on_error=False):
    installer = installer_context.lookup_installer(installer_name)
    if installer is None:
        raise XylemInternalError("did not find resolved installer '{}'".
                                 format(installer_name))

    errors = []
    try:
        commands = installer.get_install_commands(resolutions,
                                                  interactive=interactive,
                                                  reinstall=reinstall)
    except InstallerError as e:  # TODO: does InstallerError here make sense?
        errors.append(chain_exception(
            InstallError, "installer '{}' failed to compose install commands "
            "for resolutions {} with options `interactive={}` and "
            "`reinstall={}`".
            format(installer_name, resolutions, interactive, reinstall), e))
    except Exception as e:
        raise_from(
            XylemInternalError, "unexpected error in installer '{}' while "
            "composing install commands for resolutions {} with options "
            "`interactive={}` and `reinstall={}`".
            format(installer_name, resolutions, interactive, reinstall), e)

    if not commands:
        info_v("# [%s] no packages to install" % installer_name)
        return errors

    # 1. when simulating, only print commands to screen
    if simulate:
        print("# [%s] installation commands:" % installer_name)
        for cmd in commands:
            info('  ' + ' '.join(cmd))
        return errors

    # 2. else, run each install command set and collect errors
    for cmd in commands:
        info(fmt("@!executing command: %s@|" % ' '.join(cmd)))
        exitcode = subprocess.call(cmd)
        info_v(fmt("@!command return code: %s@|" % exitcode))
        if exitcode != 0:
            errors.append(InstallError(
                "command `{}` for installer '{}' failed with return code {}".
                format(' '.join(cmd), installer, exitcode)))
            if not continue_on_error:
                return errors

    # 3. test installation of each resolution item
    for item in resolutions:
        try:
            if not installer.is_installed(item):
                errors.append(InstallError(
                    "failed to detect successful installation of '{}' "
                    "resolution `{}`".format(installer_name, item)))
        except InstallerError as e:  # TODO: does this here make sense?
            errors.append(chain_exception(
                InstallError, "installer '{}' failed to determine if `{}` "
                "was successfully installed or not".
                format(installer_name, item), e))
        except Exception as e:
            raise_from(
                XylemInternalError, "unexpected error in installer '{}' while "
                "checking successful installation of `{}`".
                format(installer_name, item), e)

    # 4. return list of failures
    if errors:
        info_v("# [%s] errors during installation" % installer_name)
    else:
        info_v("# [%s] successfully installed" % installer_name)
    return errors
