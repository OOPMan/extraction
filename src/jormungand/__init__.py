import sys
import imp
import os
from yapsy import PluginManager, NormalizePluginNameForModuleName, log
from yaml import safe_load

from jormungand.api import *

__author__ = 'adam.jorgensen.za@gmail.com'


class JormungandPluginManager(PluginManager.PluginManager):
    """
    Extends the standard Yapsy PluginManager to provided extended functionality:
    * YAML Configuration File
    * Explicit sorting of plugins
    * Optional Configuration parameters for specific plugins during __init__
    """

    __default_categories_filter = {
        'DataModel': DataModelPluginInterface,
        'Extraction': ExtractionPluginInterface,
        'PostProcessing': PostProcessingPluginInterface,
        'Validation': ValidationPluginInterface,
        'Storage': StoragePluginInterface
    }

    def __init__(self,
                 config_file=None,
                 categories_filter=__default_categories_filter,
                 directories_list=None,
                 plugin_info_ext="jormungand.plugin"):
        super(JormungandPluginManager, self).__init__(categories_filter, directories_list, plugin_info_ext)
        config_file_path = os.path.abspath(config_file)
        self.config = safe_load(open(config_file_path, 'rb')) if config_file else {}
        if self.config.get('plugin_roots'):
            plugin_roots = [
                path if path.startswith(os.sep)
                else os.sep.join([config_file_path, path])
                for path in self.config['plugin_roots']
                if isinstance(path, (str, unicode))
            ]
            self.getPluginLocator().plugins_places.extend(plugin_roots)

    def loadPlugins(self, callback=None):
        if not hasattr(self, '_candidates'):
            raise ValueError("locatePlugins must be called before loadPlugins")

        sys.path.extend(self.getPluginLocator().plugins_places)

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
            # explicitly indicated
            if "__init__" in os.path.basename(candidate_filepath):
                candidate_filepath = os.path.dirname(candidate_filepath)
            try:
                # use imp to correctly load the plugin as a module
                if os.path.isdir(candidate_filepath):
                    candidate_module = imp.load_module(plugin_module_name, None,
                                                       candidate_filepath, (
                                                           "py", "r",
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
            for element in (getattr(candidate_module, name) for name in dir(candidate_module)):
                plugin_info_reference = None
                for category_name in self.categories_interfaces:
                    try:
                        is_correct_subclass = issubclass(element, self.categories_interfaces[category_name])
                    except Exception:
                        continue
                    if is_correct_subclass and element is not self.categories_interfaces[category_name]:
                        current_category = category_name
                        if candidate_infofile not in self._category_file_mapping[current_category]:
                            # we found a new plugin: initialise it and search for the next one
                            plugins = self.config.get('plugins', {})
                            plugin_mode = plugins.get('mode', 'blacklist')
                            if plugin_mode == 'whitelist' and plugin_info.name not in plugins.get(current_category, []):
                                break
                            elif plugin_mode == 'blacklist' and plugin_info.name in plugins.get(current_category, []):
                                break
                            if not plugin_info_reference:
                                try:
                                    plugin_constructer_args = self.config.get('plugin_config', {}).get(current_category, {}).get(plugin_info.name, {})
                                    if isinstance(plugin_constructer_args, (list, set)):
                                        plugin_info.plugin_object = element(*plugin_constructer_args)
                                    elif isinstance(plugin_constructer_args, dict):
                                        plugin_info.plugin_object = element(**plugin_constructer_args)
                                    else:
                                        plugin_info.plugin_object = element()
                                        plugin_info_reference = plugin_info
                                except Exception:
                                    exc_info = sys.exc_info()
                                    log.error("Unable to create plugin object: {}".format(candidate_filepath), exc_info=exc_info)
                                    plugin_info.error = exc_info
                                    break  # If it didn't work once it wont again
                            plugin_info.categories.append(current_category)
                            self.category_mapping[current_category].append(
                                    plugin_info_reference)
                            self._category_file_mapping[
                                current_category].append(candidate_infofile)
        # Remove candidates list since we don't need them any more and
        # don't need to take up the space
        delattr(self, '_candidates')

        # Sort Plugins
        for category_name, plugin_infos in self.category_mapping.items():
            plugin_names = self.config.get('plugin_order', {}).get(category_name, [])
            plugin_rankings = {
                plugin_name: plugin_ranking
                for plugin_name, plugin_ranking
                in zip(plugin_names, range(0, len(plugin_names)))
            }
            plugin_infos.sort(key=lambda plugin_info: plugin_rankings.get(plugin_info.name, len(plugin_names)+1))

        return processed_plugins

    def instanciateElement(self, element):
        raise NotImplementedError

