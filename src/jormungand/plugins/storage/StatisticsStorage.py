import os

from jormungand.api import StoragePluginInterface

__author__ = 'adam.jorgensen.za@gmail.com'


class StatisticsStoragePlugin(StoragePluginInterface):
    """
    A simple Storage Plugin
    """

    def __init__(self, output_path='.'):
        """
        A custom output path prefix may be specific for the data files generated
        """
        super(StatisticsStoragePlugin, self).__init__()
        self.output_path = output_path

    def can_store(self, data_model_name, data_model):
        """
        The Statistics Storage Plugin can store Statistics for any Data Model
        """
        return True

    def store(self, data_items, data_model_name, data_model):
        """
        Stores Statistics about the Data Items for the associated Data Model
        """
        sources = {}
        uids = {}
        valid = 0
        valid_uids = {}
        validation_errors = {}
        validated_by = {}
        processing_errors = {}
        processed_by = {}
        value_sort = lambda (key, value): value
        for uid, data_item in data_items:
            # Generate Statistics
            # UID Statistics
            uids.setdefault(uid, 0)
            uids[uid] += 1
            # Source Statistics
            source = getattr(data_item, 'source', 'unknown')
            source_count = sources.setdefault(source, 0)
            sources[source] = source_count + 1
            # Post-Processing Statistics
            for processor in getattr(data_item, 'processed_by', ['nothing']):
                processed_by.setdefault(processor, 0)
                processed_by[processor] += 1
            for processing_error in getattr(data_item, 'processing_errors', ['none']):
                processing_errors.setdefault(processing_error, 0)
                processing_errors[processing_error] += 1
            # Validation Statistics
            if getattr(data_item, 'valid', True):
                valid += 1
                valid_uids.setdefault(uid, True)
            for validator in getattr(data_item, 'validated_by', ['nothing']):
                validated_by.setdefault(validator, 0)
                validated_by[validator] += 1
            for validation_error in getattr(data_item, 'validation_errors', ['none']):
                validation_errors.setdefault(validation_error, 0)
                validation_errors[validation_error] += 1
        # Store Statistics
        with open(os.path.join(self.output_path, '%s.statistics.txt' % data_model_name), 'wb') as output:
            output.write('Statistics for %s:\n\n' % data_model_name)
            output.write('Totals:\n')
            output.write('Total data items: %d\n' % len(data_items))
            output.write('Total valid data items: %d\n\n' % valid)
            output.write('Total unique data_item UIDS: %d\n' % len(uids))
            output.write('Total valid unique data_item UIDS: %d\n\n' % len(valid_uids))
            output.write('Sources:\n\n')
            sources = sorted(sources.items(), reverse=True, key=value_sort)
            for source, source_count in sources:
                output.write('Source %s: %s Data Items\n' % (source, source_count))
            output.write('\nValidators:\n')
            validated_by = sorted(validated_by.items(), reverse=True, key=value_sort)
            for validator, validator_count in validated_by:
                output.write('%s Validated %d Data Items\n' % (validator, validator_count))
            output.write('\nValidation Errors:\n')
            validation_errors = sorted(validation_errors.items(), reverse=True, key=value_sort)
            for validation_error, validation_error_count in validation_errors:
                output.write('%d "%s" Validation Errors\n' % (validation_error_count, validation_error))
            output.write('\nPost-Processors:\n')
            processed_by = sorted(processed_by.items(), reverse=True, key=value_sort)
            for processor, processor_count in processed_by:
                output.write('%s Post-Processed %d Data Items\n' % (processor, processor_count))
            output.write('\nPost-Processing Errors:\n')
            processing_errors = sorted(processing_errors.items(), reverse=True, key=value_sort)
            for processor, processor_error_count in processing_errors:
                output.write('%d "%s" Post-Processing Errors\n' % (processor_error_count, processor))
        return True

