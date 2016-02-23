import logging
from contextlib import contextmanager
from hashlib import md5

from datetime import datetime, date, time, timedelta
from jormungand.api.datamodel import FieldDefinition, generate_field_value
from jormungand.api import StoragePluginInterface
from simplejson import dumps, JSONEncoder
from sqlalchemy import Column, String, Integer, DateTime, LargeBinary, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from types import NoneType

__author__ = 'aj@spinglab.co'

RecordBase = declarative_base()


def get_scoped_session(engine):
    """ Returns a context manager that yields a session

    """
    @contextmanager
    def session_scope():
        session = sessionmaker(engine)()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    return session_scope()


class StorageRecord(RecordBase):
    """
    SQLALchemy Record class defining the structure of the table used to store Extracted data
    """
    __tablename__ = 'storage'

    data_model = Column(LargeBinary)
    data_model_name = Column(String, primary_key=True)
    uid = Column(String, primary_key=True)
    version = Column(Integer, primary_key=True, autoincrement=False)
    created = Column(DateTime, default=datetime.now)
    data_item = Column(LargeBinary)
    data_item_metadata = Column(LargeBinary)
    checksum = Column(String(length=32))


class SQLAlchemyFlatJSONEncoder(JSONEncoder):
    """
    A custom JSONEncoder that is capable of handling the FieldDefinition classes included within the Data Model
    """

    def __init__(self, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, sort_keys=False,
                 indent=4, separators=(',', ':'), encoding='utf-8', default=None, use_decimal=True,
                 namedtuple_as_object=True, tuple_as_array=True, bigint_as_string=False, item_sort_key=None,
                 for_json=False, ignore_nan=False):
        """
        Init is overridden to specify indent
        """
        super(SQLAlchemyFlatJSONEncoder, self).__init__(skipkeys, ensure_ascii, check_circular, allow_nan, sort_keys,
                                                        indent, separators, encoding, default, use_decimal,
                                                        namedtuple_as_object, tuple_as_array, bigint_as_string,
                                                        item_sort_key, for_json, ignore_nan)

    def default(self, o):
        """
        Custom default implementation that handles FieldDefinition and datetime instances
        """
        if isinstance(o, FieldDefinition):
            return {
                '__class__': 'FieldDefinition',
                'type': o.type.__name__ if o is not NoneType else 'NoneType',
                'default_value': generate_field_value(o),
                'required': o.required,
                'unique': o.unique

            }
        if isinstance(o, (datetime, date, time)):
            return {
                '__class__': o.__class__.__name__,
                'value': o.isoformat()
            }
        if isinstance(o, timedelta):
            return {
                '__class__': 'timedelta',
                'value': {
                    key: getattr(o, key) for key in ('days', 'seconds', 'microseconds', 'milliseconds', 'minutes', 'hours', 'weeks')
                }
            }
        return super(SQLAlchemyFlatJSONEncoder, self).default(o)


class SQLAlchemyFlatJSONStoragePlugin(StoragePluginInterface):
    """
    The SQLAlchemyFlatJSONStoragePlugin provides a means of storing generic data in a database using SQLAlchemy.

    Data is converted to JSON format and stored in BLOBs, along with additional useful information that should
    allow for the stored data to be re-used and accessed easily enough.
    """

    def __init__(self, rdbms_url='sqlite:///SQLAlchemyFlatStoragePlugin.db', sqlalchemy_loglevel=None):
        super(self, SQLAlchemyFlatJSONStoragePlugin).__init__()
        # Init SQLAlchemy
        self.engine = create_engine(rdbms_url)
        if sqlalchemy_loglevel:
            logging.getLogger('sqlalchemy.engine').setLevel(sqlalchemy_loglevel)
        RecordBase.metadata.create_all(self.engine)

    def can_store(self, data_model_name, data_model):
        return True

    def store(self, data_items, data_model_name, data_model):
        with get_scoped_session(self.engine) as session:
            data_model = dumps(data_model, cls=SQLAlchemyFlatJSONEncoder)
            uid_version_checksums = {
                (uid, version): checksum for uid, version, checksum in session
                    .query(StorageRecord.uid, StorageRecord.version, StorageRecord.checksum)
                    .filter(StorageRecord.data_model_name == data_model_name)
            }
            current_versions = {
                uid: (version, uid_version_checksums.get((uid, version))) for uid, version in session
                    .query(StorageRecord.uid, func.max(StorageRecord.version))
                    .filter(StorageRecord.data_model_name == data_model_name)
                    .group_by(StorageRecord.uid)
            }
            for uid, data_item in data_items:
                uid, data_item, data_item_metadata = \
                    [dumps(item, cls=SQLAlchemyFlatJSONEncoder) for item in (uid, data_item, vars(data_item))]
                checksum = md5('#'.join([data_model, data_item, data_item_metadata])).hexdigest()
                current_version, current_version_checksum = current_versions.get(uid, (0, None))
                if checksum == current_version_checksum:
                    continue
                current_versions[uid] = (current_version + 1, checksum)
                session.add(StorageRecord(data_model=data_model, data_model_name=data_model_name, uid=uid,
                                          version=current_version + 1, data_item=data_item, checksum=checksum,
                                          data_item_metadata=data_item_metadata))
        return super(SQLAlchemyFlatJSONStoragePlugin, self).store(data_items, data_model_name, data_model)


