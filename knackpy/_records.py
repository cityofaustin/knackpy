class Records:
    """
    Knack record data proxy getter.
    """
    def __repr__(self):
        return f"""<Records [{len(self.data)} objects/views])"""

    def __init__(self, key_props):
        self.data = {}
        self.keys = self._generate_key_lookup(key_props)

    def _generate_key_lookup(self, key_props):

        keys = {}

        for key_prop in key_props:
            keys[key_prop["name"]] = key_prop["key"]
            keys[key_prop["key"]] = key_prop["key"]

        return keys

    def _record_generator(self, records):
        for record in records:
            yield record

    def get(self, key):
        try:
            records = self.data[self.keys[key]]
            return self._record_generator(records)
        except KeyError:
            raise KeyError(f"Invalid object or view key: {key}. No records found.")