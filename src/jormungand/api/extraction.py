import collections

from yapsy import IPlugin

__author__ = 'adam.jorgensen.za@gmail.com'


class ExtractedDataItem(dict):
    """
    Overrides the dict class to allow metadata to be added to DataItem dicts by setting attributes on the item. If an
    ExtractedDataItem instance is instantiated using an instance of ExtractedDataItem then the attributes set on the
    input item are copied over to the new item.
    """
    def __init__(self, seq={}, **kwargs):
        self.source = None
        super(ExtractedDataItem, self).__init__(seq, **kwargs)
        # If input sequence is an instance of ExtractedDataItem or one of its descendants then copy its custom attributes
        if isinstance(seq, ExtractedDataItem):
            for key, value in vars(seq).items():
                setattr(self, key, value)

    def update(self, E=None, **F):
        """
        Overrides the standard dict update method to support recursive updating.

        Based on http://stackoverflow.com/a/14048316 with a modification to support updating of list values.
        """
        def update(d, u):
            for k, v in u.iteritems():
                if isinstance(v, collections.Mapping):
                    r = update(d.get(k, {}), v)
                    d[k] = r
                elif isinstance(v, collections.MutableSequence):
                    for i in xrange(0, len(v)):
                        r = update(d[k][i], v[i])
                        d[k][i] = r
                else:
                    d[k] = u[k]
            return d
        update(self, E)
        update(self, F)


class ExtractionPluginInterface(IPlugin.IPlugin):
    """
    Defines an interface for plugins that extract data from a source
    """

    def can_extract(self, source, data_model_name, data_model):
        """
        Determines whether the plugin can extract data for given combination of source and data model.

        Source will be an instance of urlparse.ParseResult

        Returns a bool.
        """
        return False

    def extract(self, source, data_model_name, data_model, data_item_template_generator):
        """
        Extract data from a given combination of source and data model.

        Source will be an instance of urlparse.ParseResult

        Returns a list of (UID value, ExtractedDataItem instance) tuples
        """
        return []

