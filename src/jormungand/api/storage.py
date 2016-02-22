from yapsy import IPlugin

__author__ = 'adam.jorgensen.za@gmail.com'


class StoragePluginInterface(IPlugin.IPlugin):
    """
    Defines an interface for a plugin that stores data extracted from a source
    """

    def can_store(self, data_model_name, data_model):
        """
        Determines whether the plugin can store data associated with a given data model. Returns a bool.
        """
        return False

    def store(self, data_items, data_model_name, data_model):
        """
        For a given data model, receives an input list of (UID value, ExtractedDataItem instance) tuples and
        attempts to store them.

        Returns a boolean value indicating success or failure.
        """
        return False
