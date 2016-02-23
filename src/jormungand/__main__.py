import logging
import sys
from argparse import ArgumentParser
from urlparse import urlparse

import os

from . import JormungandPluginManager

__author__ = 'adam.jorgensen.za@gmail.com'


def jormungand(config_file=None, plugin_roots=[], sources=[], logging=logging):
    """ Entry-point into the Extraction Process """
    #TODO: Refactor into separate functions or, possibly, a class in the extraction module
    # Init Plugin Manager and Plugins
    logging.info('Initialising Jormungand Plugin Manager')
    plugin_manager = JormungandPluginManager(config_file)
    plugin_manager.extendPluginPlaces([os.path.abspath(plugin_root)
                                       for plugin_root in plugin_roots])
    plugin_manager.collectPlugins()
    for plugin_info in plugin_manager.getAllPlugins():
        plugin_manager.activatePluginByName(plugin_info.name)
    # Load Data Models
    logging.info('Loading Data Models')
    data_models = {}
    data_template_generators = {}
    for plugin_info in plugin_manager.getPluginsOfCategory('DataModel'):
        model_name = plugin_info.plugin_object.get_data_model_name()
        data_models[model_name] = plugin_info.plugin_object.get_data_model()
        data_template_generators[model_name] = plugin_info.plugin_object.get_data_template_generator()
        logging.info('Loaded Data Model %s' % model_name)
    # Obtain a full list of sources
    logging.info('Generating list of sources to process')
    inputs = []
    for source in sources:
        original_source_value = source
        source = urlparse(source, allow_fragments=True)
        if source.scheme in ('', 'file'):
            if os.path.isdir(source.path):
                for directory, subdirectories, files in os.walk(source.path):
                    for file in files:
                        file_path = os.path.join(directory, file)
                        result = urlparse(file_path)
                        setattr(result, 'uri', file_path)
                        inputs.append(result)
            elif os.path.isfile(source.path):
                setattr(source, 'uri', original_source_value)
                inputs.append(source)
            else:
                logging.warn("Provided source {} is neither file, nor "
                            "directory! Check that the file exists."
                            .format(source))
        else:
            setattr(source, 'uri', original_source_value)
            inputs.append(source)
    logging.info('Finalized list of sources to process: %s' % ', '.join([input.uri for input in inputs]))
    #TODO: A fair bit of repeated code here, refactor
    # Extract data from input files
    logging.info('Extracting data')
    extracted_data = {data_model_name: [] for data_model_name in data_models}
    for plugin_info in plugin_manager.getPluginsOfCategory('Extraction'):
        plugin = plugin_info.plugin_object
        for data_model_name, data_model in data_models.items():
            for input in inputs:
                if plugin.can_extract(input, data_model_name, data_model):
                    logging.info('Extracting data from {} using Data Model {} '
                                 'and Extraction plugin {} '.format(input.uri, data_model_name, plugin))
                    extracted_data[data_model_name].extend(
                        plugin.extract(input, data_model_name, data_model, data_template_generators[data_model_name]))
    # Post-Process
    logging.info('Post-Processing Extracted Data')
    for plugin_info in plugin_manager.getPluginsOfCategory('PostProcessing'):
        plugin = plugin_info.plugin_object
        for data_model_name, data_model in data_models.items():
            if plugin.can_process(data_model_name, data_model):
                logging.info('Post-Processing Data Model {} using '
                             'Post-Processing plugin {}'.format(data_model_name, plugin))
                extracted_data[data_model_name] = plugin.process(extracted_data[data_model_name], data_model_name, data_model)
    # Validation
    logging.info('Validating Extracted Data')
    for plugin_info in plugin_manager.getPluginsOfCategory('Validation'):
        plugin = plugin_info.plugin_object
        for data_model_name, data_model in data_models.items():
            if plugin.can_validate(data_model_name, data_model):
                logging.info('Validating Data Model {} using Validation '
                             'plugin {}'.format(data_model_name, plugin))
                extracted_data[data_model_name] = plugin.validate(extracted_data[data_model_name], data_model_name, data_model)
    # Storage
    logging.info('Storing Extracted Data')
    for plugin_info in plugin_manager.getPluginsOfCategory('Storage'):
        plugin = plugin_info.plugin_object
        for data_model_name, data_model in data_models.items():
            if plugin.can_store(data_model_name, data_model):
                logging.info('Storing items of Data Model {} using Storage '
                             'plugin {}'.format(data_model_name, plugin))
                plugin.store(extracted_data[data_model_name], data_model_name, data_model)


def main():
    # Ensure directory of extraction script is on the path
    sys.path.append(os.path.dirname(__file__))
    # Configure CLI parser
    parser = ArgumentParser(description='Extract data from input sources into '
                                        'a datastore, optionally performing '
                                        'post-processing and validation.')
    parser.add_argument('-c', '--config', default=None)
    parser.add_argument('-p', '--pluginroots', dest='plugin_roots', default=[], nargs='*', )
    parser.add_argument('-s', '--source', dest='sources', default=[], nargs='*')
    parser.add_argument('--loglevel', default='INFO')
    parser.add_argument('--logfile', default=None)
    args = parser.parse_args()
    # Configure Logging
    logging.basicConfig(level=args.loglevel)
    logger = logging.getLogger('JORMUNGAND')
    if args.logfile:
        logger.addHandler(logging.FileHandler(args.logfile))
    jormungand(args.config, args.plugin_roots, args.sources, logger)


if __name__ == '__main__':
    main()


