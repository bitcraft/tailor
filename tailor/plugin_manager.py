# -*- coding: utf-8 -*-
"""
forked.modified from yapsy, leif theden, 2015


original license below:


Yapsy is provided under the BSD-2 clause license (see text below),
with the following two exceptions:

- the "yapsy" icons in artwork/ is licensed under the Creative Commons
  Attribution-Share Alike 3.0 by Thibauld Nion (see
  artwork/LICENSE.txt)

- the compat.py file is licensed under the ISC License by Kenneth
  Reitz (see yapsy/compat.py).


--------------------
BSD 2-clause license
--------------------

Copyright (c) 2007-2015, Thibauld Nion

All rights reserved.


Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
"""
import sys
import os
import imp

from yapsy import log
from yapsy import NormalizePluginNameForModuleName
from yapsy.IPlugin import IPlugin
from yapsy.IPluginLocator import IPluginLocator
from yapsy.PluginFileLocator import PluginFileAnalyzerWithInfoFile
from yapsy.PluginFileLocator import PluginFileLocator


class PluginManager:
    """
    Manage several plugins by ordering them in categories.

    The mechanism for searching and loading the plugins is already
    implemented in this class so that it can be used directly (hence
    it can be considered as a bit more than a mere interface)

    The file describing a plugin must be written in the syntax
    compatible with Python's ConfigParser module as in the
    `Plugin Info File Format`_
    """

    def __init__(self,
                 categories_filter=None,
                 directories_list=None,
                 plugin_info_ext=None,
                 plugin_locator=None):
        """
        Initialize the mapping of the categories and set the list of
        directories where plugins may be. This can also be set by
        direct call the methods:

        - ``setCategoriesFilter`` for ``categories_filter``
        - ``setPluginPlaces`` for ``directories_list``
        - ``setPluginInfoExtension`` for ``plugin_info_ext``

        You may look at these function's documentation for the meaning
        of each corresponding arguments.
        """
        # as a good practice we don't use mutable objects as default
        # values (these objects would become like static variables)
        # for function/method arguments, but rather use None.
        if categories_filter is None:
            categories_filter = {"Default": IPlugin}
        self.setCategoriesFilter(categories_filter)
        plugin_locator = self._locatorDecide(plugin_info_ext, plugin_locator)
        # plugin_locator could be either a dict defining strategies, or directly
        # an IPluginLocator object
        self.setPluginLocator(plugin_locator, directories_list)

    def _locatorDecide(self, plugin_info_ext, plugin_locator):
        """
        For backward compatibility, we kept the *plugin_info_ext* argument.
        Thus we may use it if provided. Returns the (possibly modified)
        *plugin_locator*.
        """
        specific_info_ext = plugin_info_ext is not None
        specific_locator = plugin_locator is not None
        if not specific_info_ext and not specific_locator:
            # use the default behavior
            res = PluginFileLocator()
        elif not specific_info_ext and specific_locator:
            # plugin_info_ext not used
            res = plugin_locator
        elif not specific_locator and specific_info_ext:
            # plugin_locator not used, and plugin_info_ext provided
            # -> compatibility mode
            res = PluginFileLocator()
            res.setAnalyzers(
                [PluginFileAnalyzerWithInfoFile("info_ext", plugin_info_ext)])
        elif specific_info_ext and specific_locator:
            # both provided... issue a warning that tells "plugin_info_ext"
            # will be ignored
            msg = ("Two incompatible arguments (%s) provided:",
                   "'plugin_info_ext' and 'plugin_locator'). Ignoring",
                   "'plugin_info_ext'.")
            raise ValueError(" ".join(msg) % self.__class__.__name__)
        return res

    def setCategoriesFilter(self, categories_filter):
        """
        Set the categories of plugins to be looked for as well as the
        way to recognise them.

        The ``categories_filter`` first defines the various categories
        in which the plugins will be stored via its keys and it also
        defines the interface tha has to be inherited by the actual
        plugin class belonging to each category.
        """
        self.categories_interfaces = categories_filter.copy()
        # prepare the mapping from categories to plugin lists
        self.category_mapping = {}
        # also maps the plugin info files (useful to avoid loading
        # twice the same plugin...)
        self._category_file_mapping = {}
        for categ in categories_filter:
            self.category_mapping[categ] = []
            self._category_file_mapping[categ] = []

    def setPluginLocator(self, plugin_locator, dir_list=None, picls=None):
        """
        Sets the strategy used to locate the basic information.

        See ``IPluginLocator`` for the policy that plugin_locator must enforce.
        """
        if isinstance(plugin_locator, IPluginLocator):
            self._plugin_locator = plugin_locator
            if dir_list is not None:
                self._plugin_locator.updatePluginPlaces(dir_list)
            if picls is not None:
                self.setPluginInfoClass(picls)
        else:
            raise TypeError(
                "Unexpected format for plugin_locator ('%s' is not an instance of IPluginLocator)" % plugin_locator)

    def getPluginLocator(self):
        """
        Grant direct access to the plugin locator.
        """
        return self._plugin_locator

    def get_categories(self):
        """
        Return the list of all categories.
        """
        return list(self.category_mapping.keys())

    def removePluginFromCategory(self, plugin, category_name):
        """
        Remove a plugin from the category where it's assumed to belong.
        """
        self.category_mapping[category_name].remove(plugin)

    def appendPluginToCategory(self, plugin, category_name):
        """
        Append a new plugin to the given category.
        """
        self.category_mapping[category_name].append(plugin)

    def getPluginsOfCategory(self, category_name):
        """
        Return the list of all plugins belonging to a category.
        """
        return self.category_mapping[category_name][:]

    def getAllPlugins(self):
        """
        Return the list of all plugins (belonging to all categories).
        """
        allPlugins = set()
        for pluginsOfOneCategory in list(self.category_mapping.values()):
            allPlugins.update(pluginsOfOneCategory)
        return list(allPlugins)

    def getPluginCandidates(self):
        """
        Return the list of possible plugins.

        Each possible plugin (ie a candidate) is described by a 3-uple:
        (info file path, python file path, plugin info instance)

        .. warning: locatePlugins must be called before !
        """
        if not hasattr(self, '_candidates'):
            raise RuntimeError(
                "locatePlugins must be called before getPluginCandidates")
        return self._candidates[:]

    def removePluginCandidate(self, candidateTuple):
        """
        Remove a given candidate from the list of plugins that should be loaded.

        The candidate must be represented by the same tuple described
        in ``getPluginCandidates``.

        .. warning: locatePlugins must be called before !
        """
        if not hasattr(self, '_candidates'):
            raise ValueError(
                "locatePlugins must be called before removePluginCandidate")
        self._candidates.remove(candidateTuple)

    def appendPluginCandidate(self, candidateTuple):
        """
        Append a new candidate to the list of plugins that should be loaded.

        The candidate must be represented by the same tuple described
        in ``getPluginCandidates``.

        .. warning: locatePlugins must be called before !
        """
        if not hasattr(self, '_candidates'):
            raise ValueError(
                "locatePlugins must be called before removePluginCandidate")
        self._candidates.append(candidateTuple)

    def locatePlugins(self):
        """
        Convenience method (actually call the IPluginLocator method)
        """
        self._candidates, npc = self.getPluginLocator().locatePlugins()

    def loadPlugins(self, callback=None):
        """
        Load the candidate plugins that have been identified through a
        previous call to locatePlugins.  For each plugin candidate
        look for its category, load it and store it in the appropriate
        slot of the ``category_mapping``.

        If a callback function is specified, call it before every load
        attempt.  The ``plugin_info`` instance is passed as an argument to
        the callback.
        """
        # 		print "%s.loadPlugins" % self.__class__
        if not hasattr(self, '_candidates'):
            raise ValueError("locatePlugins must be called before loadPlugins")

        processed_plugins = []
        for candidate_infofile, candidate_filepath, plugin_info in self._candidates:
            # make sure to attribute a unique module name to the one
            # that is about to be loaded
            plugin_module_name_template = NormalizePluginNameForModuleName(
                "yapsy_loaded_plugin_" + plugin_info.name) + "_%d"
            for plugin_name_suffix in range(len(sys.modules)):
                plugin_module_name = plugin_module_name_template % plugin_name_suffix
                if plugin_module_name not in sys.modules:
                    break

            # tolerance on the presence (or not) of the py extensions
            if candidate_filepath.endswith(".py"):
                candidate_filepath = candidate_filepath[:-3]
            # if a callback exists, call it before attempting to load
            # the plugin so that a message can be displayed to the
            # user
            if callback is not None:
                callback(plugin_info)
            # cover the case when the __init__ of a package has been
            # explicitely indicated
            if "__init__" in os.path.basename(candidate_filepath):
                candidate_filepath = os.path.dirname(candidate_filepath)
            try:
                # use imp to correctly load the plugin as a module
                if os.path.isdir(candidate_filepath):
                    candidate_module = imp.load_module(plugin_module_name, None,
                                                       candidate_filepath,
                                                       ("py", "r",
                                                        imp.PKG_DIRECTORY))
                else:
                    with open(candidate_filepath + ".py", "r") as plugin_file:
                        candidate_module = imp.load_module(plugin_module_name,
                                                           plugin_file,
                                                           candidate_filepath + ".py",
                                                           ("py", "r",
                                                            imp.PY_SOURCE))
            except Exception:
                exc_info = sys.exc_info()
                log.error("Unable to import plugin: %s" % candidate_filepath,
                          exc_info=exc_info)
                plugin_info.error = exc_info
                processed_plugins.append(plugin_info)
                continue
            processed_plugins.append(plugin_info)
            if "__init__" in os.path.basename(candidate_filepath):
                sys.path.remove(plugin_info.path)
            # now try to find and initialise the first subclass of the correct plugin interface
            for element in (getattr(candidate_module, name) for name in
                            dir(candidate_module)):
                plugin_info_reference = None
                for category_name in self.categories_interfaces:
                    try:
                        is_correct_subclass = issubclass(element,
                                                         self.categories_interfaces[
                                                             category_name])
                    except Exception:
                        continue
                    if is_correct_subclass and element is not \
                            self.categories_interfaces[category_name]:
                        current_category = category_name
                        if candidate_infofile not in \
                                self._category_file_mapping[current_category]:
                            # we found a new plugin: initialise it and search for the next one
                            if not plugin_info_reference:
                                try:
                                    plugin_info.plugin_object = self.instanciateElement(
                                        element)
                                    plugin_info_reference = plugin_info
                                except Exception:
                                    exc_info = sys.exc_info()
                                    log.error(
                                        "Unable to create plugin object: %s" % candidate_filepath,
                                        exc_info=exc_info)
                                    plugin_info.error = exc_info
                                    break # If it didn't work once it wont again
                            plugin_info.categories.append(current_category)
                            self.category_mapping[current_category].append(
                                plugin_info_reference)
                            self._category_file_mapping[
                                current_category].append(candidate_infofile)
        # Remove candidates list since we don't need them any more and
        # don't need to take up the space
        delattr(self, '_candidates')
        return processed_plugins

    def instanciateElement(self, element):
        """
        Override this method to customize how plugins are instanciated
        """
        return element()

    def collect_plugins(self):
        """
        Walk through the plugins' places and look for plugins.  Then
        for each plugin candidate look for its category, load it and
        stores it in the appropriate slot of the category_mapping.
        """
        self.locatePlugins()
        self.loadPlugins()

    def getPluginByName(self, name, category="Default"):
        """
        Get the plugin correspoding to a given category and name
        """
        if category in self.category_mapping:
            for item in self.category_mapping[category]:
                if item.name == name:
                    return item
        return None

    def activatePluginByName(self, name, category="Default"):
        """
        Activate a plugin corresponding to a given category + name.
        """
        pta_item = self.getPluginByName(name, category)
        if pta_item is not None:
            plugin_to_activate = pta_item.plugin_object
            if plugin_to_activate is not None:
                log.debug("Activating plugin: %s.%s" % (category, name))
                plugin_to_activate.activate()
                return plugin_to_activate
        return None

    def deactivatePluginByName(self, name, category="Default"):
        """
        Desactivate a plugin corresponding to a given category + name.
        """
        if category in self.category_mapping:
            plugin_to_deactivate = None
            for item in self.category_mapping[category]:
                if item.name == name:
                    plugin_to_deactivate = item.plugin_object
                    break
            if plugin_to_deactivate is not None:
                log.debug("Deactivating plugin: %s.%s" % (category, name))
                plugin_to_deactivate.deactivate()
                return plugin_to_deactivate
        return None
