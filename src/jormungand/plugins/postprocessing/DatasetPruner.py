import logging
from random import randint

from jormungand.api import PostProcessingPluginInterface

logging = logging.getLogger('JORMUNGAND')

__author__ = 'adam.jorgensen.za@gmail.com'


class DatasetPrunerPlugin(PostProcessingPluginInterface):
    """
    This plugin is intended for use during testing. It allows one to reduce the size of the dataset following Extraction
    """

    def __init__(self, maximum_items=None):
        """
        Keyword arguments:
        maximum_items -- Specifies the maximum number of items to emit (defaults to None, indicating no pruning)
        """
        super(self, DatasetPrunerPlugin).__init__()
        self.maximum_items = maximum_items

    def can_process(self, data_model_name, data_model):
        """
        This plugin can be used with any Data Model
        """
        return True

    def process(self, data_items, data_model_name, data_model):
        """
        Prune the data set
        """
        if self.maximum_items is None:
            return data_items
        ticker = min(len(data_items), self.maximum_items)
        maximum = ticker - 1
        processed_items = []
        while ticker > 0:
            processed_items.append(data_items.pop(randint(0, maximum)))
            maximum -= 1
            ticker -= 1
        return processed_items
