import logging
from json import loads

from datetime import timedelta
from dateutil import parser
from jormungand.api.extraction import ExtractionPluginInterface, ExtractedDataItem
from jormungand.api.datamodel import FieldDefinition, FIELD_TYPES
from jormungand.plugins.storage.SQLAlchemyFlatStorage import StorageRecord, get_scoped_session
from sqlalchemy import create_engine, func, and_

__author__ = 'adam.jorgensen.za@gmail.com'


def parse_object(o):
    """
    Custom Object Parsing function used during JSON decoding to handle FieldDefinitions and date, time, datetime and timedelta values
    """
    if not o.get('__class__'):
        return o
    if o['__class__'] == 'FieldDefinition':
        return FieldDefinition(type=FIELD_TYPES[o['type']], default_value=o['default_value'], required=o['required'], unique=o['unique'])
    if o['__class__'] in ('datetime', 'date', 'time'):
        return parser.parse(o['value'])
    if o['__class__'] in ('timedelta'):
        return timedelta(**o['value'])
    return o


class SQLAlchemyFlatStorageSourcePlugin(ExtractionPluginInterface):
    """
    The SQLAlchemyFlatStorageSource provides a means of extracting data that was stored using the
    SQLAlchemyFlatStorage plugin.
    """

    def __init__(self, sqlalchemy_loglevel=None, latest_versions_only=True):
        super(self, SQLAlchemyFlatStorageSourcePlugin).__init__()
        self.latest_versions_only = latest_versions_only
        if sqlalchemy_loglevel:
            logging.getLogger('sqlalchemy.engine').setLevel(sqlalchemy_loglevel)

    def can_extract(self, source, data_model_name, data_model):
        """
        Returns true if the source URL can be transformed into a SQLAlchemy engine instance using create_engine
        """
        try:
            with get_scoped_session(create_engine(source.uri)) as session:
                return session.query(StorageRecord).filter(StorageRecord.data_model_name == data_model_name).count() > 0
        except Exception, e:
            return False
        return True

    def extract(self, source, data_model_name, data_model, data_item_template):
        extracted_data = []
        with get_scoped_session(create_engine(source.uri)) as session:
            if not self.latest_versions_only:
                query = session.query(StorageRecord).filter(StorageRecord.data_model_name == data_model_name)
            else:
                subquery = session.query(StorageRecord.uid, func.max(StorageRecord.version).label('version'))\
                                  .filter(StorageRecord.data_model_name == data_model_name)\
                                  .group_by(StorageRecord.uid)\
                                  .subquery()
                query = session.query(StorageRecord).join(subquery, and_(
                    subquery.c.uid == StorageRecord.uid,
                    subquery.c.version == StorageRecord.version
                ))
            for record in query:
                data_item = ExtractedDataItem(loads(record.data_item, object_hook=parse_object))
                for key, value in loads(record.data_item_metadata, object_hook=parse_object).items():
                    setattr(data_item, key, value)
                data_item.version = record.version
                data_item.created = record.created
                data_item.checksum = record.checksum
                data_item.data_model = loads(record.data_model)
                extracted_data.append((loads(record.uid, object_hook=parse_object), data_item))
        return extracted_data


