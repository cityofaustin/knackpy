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

            try:
                field_def = self.field_defs[key]
            except KeyError:
                continue

            if format_keys:
                key = field_def.name

            handled_record[key] = self._handle_field(value, field_def, format_values)

        return handled_record

    def _handle_field(self, value, field_def, format_values):
        return value if not format_values else field_def.formatter(value)
