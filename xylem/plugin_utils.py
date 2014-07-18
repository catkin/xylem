"""Helpers for loading plugin definitions."""

from __future__ import unicode_literals

import pkg_resources
import abc
import six

from .util import raise_from
from .text_utils import text_type
from .text_utils import to_str
from .exception import InvalidPluginError
from .log_utils import warning
from .log_utils import error


class PluginBase(six.with_metaclass(abc.ABCMeta, object)):

    """Abstract base class for all plugin classes.

    Plugin classes must define the ``name`` property. This name is used
    in other parts of the system. For example for installer plugins the
    installer name ``"apt"`` is used in rules definitions. The name of
    plugin classes is distinct from the plugin name from the plugin
    definition. The latter is only used to refer to the plugin
    definitions themselves and (de-)activate specific plugins. All
    loaded plugins of one kind are unique by the plugin class name.
    """

    @abc.abstractproperty
    def name(self):
        """Name of the plugin object."""
        return


def verify_plugin_name(name):
    """Verify name from plugin definition.

    :raises ValueError: if name is invalid
    """
    if not isinstance(name, text_type):
        raise ValueError(
            "Expected string as plugin name, got '{0}' of type '{1}'.".
            format(name, to_str(type(name))))


def verify_plugin_description(decription):
    """Verify decription from plugin definition.

    :raises ValueError: if decription is invalid
    """
    if not isinstance(decription, text_type):
        raise ValueError(
            "Expected string as plugin decription, got '{0}' of type '{1}'.".
            format(decription, to_str(type(decription))))


def verify_plugin_class(class_, base_class):
    """Verify class from plugin definition.

    :raises ValueError: if class is invalid
    """
    if not issubclass(base_class, PluginBase):
        raise ValueError(
            "Plugin base class '{0}' does not implement ABC PluginBase.".
            format(to_str(base_class)))
    if not issubclass(class_, base_class):
        raise ValueError(
            "Expected plugin class '{1}' to be subclass of '{0}'.".
            format(to_str(class_), to_str(base_class)))


def verify_plugin_definition(definition, kind, base_class):
    """Verify plugin definition.

    :param dict definition: definition of plugin as loaded from entry point
    :param str kind: kind of plugin (e.g. "installer")
    :param type base_class: (abstract) base class plugins must derive from
    :raises InvalidPluginError: if plugin definition is invalid
    """
    try:
        verify_plugin_name(definition['plugin_name'])
        verify_plugin_description(definition['description'])
        verify_plugin_class(definition[kind], base_class)
    except (TypeError, KeyError, ValueError) as e:
        raise_from(InvalidPluginError, "The following definition of {0} "
                   "plugin is invalid:\n{1}".format(kind, definition), e)


def get_plugin_list(kind, base_class, group):
    """Load plugins form entry points.

    Load the plugins of given ``kind`` from entry points ``group``,
    instantiating objects and ignoring duplicates. The entry points must
    be valid plugin definitions (see :func:`verify_plugin_definition`).
    The list of plugins is free of duplicates by plugin class name (not
    plugin name).

    :param str kind: kind of plugin (e.g. "installer")
    :param base_class: (abstract) base class plugins (must implement
        PluginBase)
    :param group: entry point group to load plugins from
    :return: list of the loaded and instantiated plugin classes
    :rtype: `list`
    """
    plugin_list = []
    name_set = set()
    for entry_point in pkg_resources.iter_entry_points(group=group):
        definition = entry_point.load()
        try:
            verify_plugin_definition(definition, kind, base_class)
        except InvalidPluginError as e:
            # TODO: somehow decide when to reraise and when to display error
            error("Skipping {0} plugin. Failed to load from '{1}' entry point "
                  "with name '{2}':\n{3}".format(
                      kind, group, entry_point.name, e))
            continue
        plugin_class = definition[kind]
        plugin_obj = plugin_class()
        obj_name = plugin_obj.name
        if obj_name in name_set:
            warning("Ignoring {0} plugin '{1}' with duplicate name '{1}'".
                    format(kind, definition['plugin_name'], obj_name))
        else:
            name_set.add(obj_name)
            plugin_list.append(plugin_obj)
    return plugin_list
