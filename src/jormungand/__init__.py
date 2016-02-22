import json
import logging
import sys

import os
from yapsy import PluginManager

from api import *

__author__ = 'adam.jorgensen.za@gmail.com'


class JormungandPluginManager(PluginManager.PluginManager):
    """
    Extends the standard Yapsy PluginManager to provided extended functionality:
    * JSON Configuration File
    * Explicit sorting of plugins
    * Optional Configuration parameters for specific plugins during __init__
    """

    def __init__(self,
                 json_config_file=None,
                 categories_filter={
                    'DataModel': DataModelPluginInterface,
                    'Extraction': ExtractionPluginInterface,
                    'PostProcessing': PostProcessingPluginInterface,
                    'Validation': ValidationPluginInterface,
                    'Storage': StoragePluginInterface},
                 directories_list=None,
                 plugin_info_ext="jormungand.plugin"):
        super(JormungandPluginManager, self).__init__(categories_filter, directories_list, plugin_info_ext)
        self.json_config = json.load(open(os.path.abspath(json_config_file), 'rb')) if json_config_file else {}
        if self.json_config.get('plugin_roots'):
            for path in self.json_config.get('plugin_roots'):
                if not path.startswith(os.sep):
                    self.json_config['plugin_roots'].remove(path)
                    self.json_config['plugin_roots'].append(os.sep.join([os.path.dirname(os.path.abspath(json_config_file)), path]))
        self.extendPluginPlaces(self.json_config.get('plugin_roots', []))

    def extendPluginPlaces(self, directories_list):
        """ Extend the current list of plugin locations with new entries """
        self.plugins_places.extend(directories_list)

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
        if not hasattr(self, '_candidates'):
            raise ValueError("locatePlugins must be called before loadPlugins")

        for path in self.plugins_places:
            sys.path.append(path)

        for candidate_infofile, candidate_filepath, plugin_info in self._candidates:
            # if a callback exists, call it before attempting to load
            # the plugin so that a message can be displayed to the
            # user
            if callback is not None:
                callback(plugin_info)
            # now execute the file and get its content into a
            # specific dictionnary
            candidate_globals = {"__file__": candidate_filepath + ".py"}
            if "__init__" in os.path.basename(candidate_filepath):
                sys.path.append(plugin_info.path)
            try:
                candidateMainFile = open(candidate_filepath + ".py", "r")
                exec candidateMainFile in candidate_globals
                # exec (candidateMainFile, candidate_globals)
            except Exception, e:
                logging.error("Unable to execute the code in plugin: %s" % candidate_filepath)
                logging.error("\t The following problem occured: %s %s " % (os.linesep, e))
                if "__init__" in os.path.basename(candidate_filepath):
                    sys.path.remove(plugin_info.path)
                continue

            if "__init__" in os.path.basename(candidate_filepath):
                sys.path.remove(plugin_info.path)
            # now try to find and initialise the first subclass of the correct plugin interface
            for element in candidate_globals.itervalues():
                current_category = None
                for category_name in self.categories_interfaces:
                    try:
                        is_correct_subclass = issubclass(element, self.categories_interfaces[category_name])
                    except:
                        continue
                    if is_correct_subclass:
                        if element is not self.categories_interfaces[category_name]:
                            current_category = category_name
                            break
                if current_category is not None:
                    if plugin_info.name in self.json_config.get('excluded_plugins', {}).get(current_category, []):
                        break
                    if not (candidate_infofile in self._category_file_mapping[current_category]):
                        # we found a new plugin: initialise it and search for the next one
                        plugin_constructer_args = self.json_config.get('plugin_config', {}).get(current_category, {}).get(plugin_info.name, {})
                        if isinstance(plugin_constructer_args, list):
                            plugin_info.plugin_object = element(*plugin_constructer_args)
                        elif isinstance(plugin_constructer_args, dict):
                            plugin_info.plugin_object = element(**plugin_constructer_args)
                        else:
                            plugin_info.plugin_object = element()
                        plugin_info.category = current_category
                        self.category_mapping[current_category].append(plugin_info)
                        self._category_file_mapping[current_category].append(candidate_infofile)
                        current_category = None
                    break

        # Remove candidates list since we don't need them any more and
        # don't need to take up the space
        delattr(self, '_candidates')

        # Sort Plugins
        for category_name, plugin_infos in self.category_mapping.items():
            plugin_names = self.json_config.get('plugin_order', {}).get(category_name, [])
            plugin_rankings = {plugin_name: plugin_ranking for plugin_name, plugin_ranking in zip(plugin_names, range(0, len(plugin_names)))}
            plugin_infos.sort(key=lambda plugin_info: plugin_rankings.get(plugin_info.name, len(plugin_names)+1))
