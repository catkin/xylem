
from __future__ import unicode_literals

from .sources import SourcesContext
from .sources import RulesDatabase
from .installers import InstallerContext
from .specs.rules import compact_installer_dict


def lookup(xylem_key, prefix=None, os_override=None, compact=False):

    sources_context = SourcesContext(prefix=prefix)

    database = RulesDatabase(sources_context)
    database.load_from_cache()

    if isinstance(os_override, InstallerContext):
        ic = os_override
    else:
        ic = InstallerContext(os_override=os_override)

    installer_dict = database.lookup(xylem_key, ic)

    if compact:
        default_installer_name = ic.get_default_installer_name()
        compacted = compact_installer_dict(installer_dict,
                                           default_installer_name)

    return compacted
