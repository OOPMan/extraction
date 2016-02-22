from copy import deepcopy

import datetime
from types import NoneType
from yapsy import IPlugin

__author__ = 'adam.jorgensen.za@gmail.com'

FIELD_TYPES = {
    v.__name__ if v is not NoneType else 'NoneType': v
    for v in (NoneType, str, unicode, int, float, bool, list, dict,
              datetime.datetime, datetime.date, datetime.time,
              datetime.timedelta)
}


class FieldDefinition(object):
    """
    Defines a class that is used to provide basic definitions of fields on a
    Data Model.
    """

    def __init__(self, type=str, default_value=None, required=False, unique=False):
        if type not in FIELD_TYPES.values():
            raise Exception('%s not an allowed type' % type)
        if required and not isinstance(default_value, type):
            raise Exception('Value is required but default_value %s is not an '
                            'instance of %s' % (default_value, type))
        self.type = type
        self.default_value = default_value
        self.required = required
        self.unique = unique


def generate_field_value(field_definition):
    """
    Given a FieldDefinition instance, attempts to generate a value for it based
    on its .default_value and .type attrs
    """
    try:
        if isinstance(field_definition.default_value, field_definition.type):
            return field_definition.default_value
        return field_definition.type()
    except:
        return None


def generate_data_template(data_model):
    """
    Given a list of (field, FieldDefinition/list/dict) tuples Data Model
    dictionary, attempts to generate a template data dict.
    """
    template = {}
    for field, field_definition in data_model:
        if isinstance(field_definition, FieldDefinition):
            template[field] = generate_field_value(field_definition)
        elif isinstance(field_definition, list):
            template[field] = [
                generate_field_value(field_definition)
                if isinstance(field_definition, FieldDefinition)
                else generate_data_template(field_definition.items())
                for field_definition in field_definition]
        elif isinstance(field_definition, dict):
            template[field] = [generate_data_template(field_definition.items())]
    return template


class DataModelPluginInterface(IPlugin.IPlugin):
    """
    Defines an interface for plugins that define data models. Data Models are
    used to unify the flow of data within the plugin-based Extraction system,
    allowing plugins to easily determine what data they can and can not process.

    Data Models are also used to generated template dict instances of the data
    associated with a Data Model and provide simple information about the
    fields associated with the Data Model that can be used by other plugins
    produced output data that complies on a basic level with the strictures of
    the Data Model.
    """

    def get_data_model_name(self):
        """
        Returns the name of the Data Model. Should be unique.
        """
        return 'modelname'

    def get_data_model(self):
        """
        Returns the Data Model. The Data Model is a dict mapping
        field name -> FieldDefinition instance.

        Fields within the Data Model that map to multiple values can be indicated
        by mapping field name -> array containing a FieldDefinition instance.

        Fields within the Data Model that map to multiple objects can be
        indicated by mapping field name -> array containing a dict. The data
        within this dict must conform to the previous rules.
        """
        return {
            'key_field': FieldDefinition(unique=True),
            'int_field': FieldDefinition(int, required=False),
            'nested_object': {
                'str_field': FieldDefinition(default_value='Yes')
            },
            'nested_array': [FieldDefinition(str)],
            'nested_array_of_objects': [{
                'int_field': FieldDefinition(int, 0),
                'str_field': FieldDefinition()
            }]
        }

    def get_data_template_generator(self):
        """
        Uses the Data Model to generate a function that can be called to
        generate template dict instance of the Data Model.
        """
        data_template = generate_data_template(self.get_data_model().items())
        return lambda: deepcopy(data_template)


