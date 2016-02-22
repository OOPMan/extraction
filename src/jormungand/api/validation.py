from yapsy import IPlugin

from postprocessing import PostProcessedDataItem

__author__ = 'adam.jorgensen.za@gmail.com'


class ValidatedDataItem(PostProcessedDataItem):
    """
    Overrides the PostProcessedDataItem class to provide an indication that a
    PostProcessedDataItem instance has undergone validation
    """
    def __init__(self, seq=None, **kwargs):
        self.valid = True
        self.validation_errors = []
        self.validated_by = []
        super(ValidatedDataItem, self).__init__(seq, **kwargs)


class ValidationPluginInterface(IPlugin.IPlugin):
    """
    Defines an interface for a plugin that validates the processed data items
    """

    def can_validate(self, data_model_name, data_model):
        """
        Determines whether the plugin can validate data associated with a given data model. Returns a bool.
        """
        return False

    def validate(self, data_items, data_model_name, data_model):
        """
        For a given data model, processes a list of (UID value, ExtractedDataItem instance) tuples and validates
        each ExtractedDataItem instance, transforming it into a ValidatedDataItem instance in the process.

        Returns a list of (UID value, ValidatedDataItem instance) tuples.
        """
        return []
