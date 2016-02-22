from yapsy import IPlugin

from extraction import ExtractedDataItem

__author__ = 'adam.jorgensen.za@gmail.com'


class PostProcessedDataItem(ExtractedDataItem):
    """
    Overrides the ExtractedDataItem class to provide an indication that an
    ExtractedDataItem instance has undergone post-processing.
    """
    def __init__(self, seq=None, **kwargs):
        self.processed_by = []
        self.processing_errors = []
        super(PostProcessedDataItem, self).__init__(seq, **kwargs)


class PostProcessingPluginInterface(IPlugin.IPlugin):
    """
    Defines an interface for a plugin that processes data extracted from a source and transforms it in some fashion.
    """

    def can_process(self, data_model_name, data_model):
        """
        Determines whether the plugin can process data associated with a given data model. Returns a bool.
        """
        return False

    def process(self, data_items, data_model_name, data_model):
        """
        For a given data model, processes a list of (UID value, ExtractedDataItem instance) tuples and transforms each
        ExtractedDataItem instance into a PostProcessedDataItem instance.

        Returns a list of (UID value, PostProcessedDataItem instance) tuples.
        """
        return []

