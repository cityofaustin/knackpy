import csv
import warnings

from knackpy.utils.utils import _valid_name


class Records:
    def __init__(self, data, field_defs):
        self.data = data
        self.field_defs = field_defs

    def get(self, key, format_keys=False, format_values=False):
        return self._record_generator(
            self.data[key], self.field_defs, format_keys, format_values
        )

    def keys(self):
        return self.data.keys()

    def _record_generator(self, data, field_defs, format_keys, format_values):
        for record in data:
            record = self._handle_record(record, format_keys, format_values)
            yield record

    def _handle_record(self, record, format_keys, format_values):
        raw_keys = [key for key in record.keys() if "raw" in key]

        handled_record = {}

        for key, value in record.items():

            if f"{key}_raw" in raw_keys:
                # skip a key that also has a raw key
                continue

            # proxy the raw key as the key
            key = key.replace("_raw", "")

            field_def = self.field_defs[key]

            key = self._handle_key(field_def, format_keys)

            handled_record[key] = self._handle_field(value, field_def, format_values)

        return handled_record

    def _handle_field(self, value, field_def, format_values):
        return value if not format_values else field_def.formatter(value)

    def _handle_key(self, field_def, format_keys):
        if field_def.key == "id" or not format_keys:
            return field_def.key

        return _valid_name(field_def.name)

    def to_csv(
        self, *keys, path="", delimiter=",", format_keys=False, format_values=False
    ):
        keys = keys if keys else list(self.keys())

        for key in keys:
            fieldnames = self._get_fieldnames(key, format_keys)

            if not fieldnames:
                warnings.warn(f"No records found in '{key}'")
                continue

            records = self.get(
                key, format_keys=format_keys, format_values=format_values
            )

            fname = f"{key}.csv"

            with open(fname, "w") as fout:
                writer = csv.DictWriter(
                    fout, fieldnames=fieldnames, delimiter=delimiter
                )
                writer.writeheader()
                for record in records:
                    writer.writerow(record)

    def _get_fieldnames(self, key, format_keys):
        records = self.get(key, format_keys)
        for record in records:
            return record.keys()
