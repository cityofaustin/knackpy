class Records:
    def __init__(self, data, field_defs):
        self.data = data
        self.field_defs = field_defs

    def get(self, key, _format=False):
        return self._record_generator(self.data[key], self.field_defs, _format)

    def keys(self):
        return self.data.keys()

    def _record_generator(self, data, field_defs, _format):
        for record in data:
            record = self._handle_record(record, _format)
            yield record

    def _handle_record(self, record, _format):
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

            if _format:
                key = field_def.name

            handled_record[key] = self._handle_field(value, field_def, _format)

        return handled_record

    def _handle_field(self, value, field_def, _format):
        return value if not _format else field_def.formatter(value)
