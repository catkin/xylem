
from __future__ import unicode_literals

from .sources import SourcesContext
from .sources import RulesDatabase
from .installers import InstallerContext


def resolve(xylem_key, prefix=None, os_override=None):

    sources_context = SourcesContext(prefix=prefix)

    database = RulesDatabase(sources_context)
    database.load_from_cache()

    installer_context = InstallerContext()
    if os_override:
        installer_context.set_os_override(os_override[0], os_override[1])

    return database.lookup(xylem_key, installer_context)
