import pprint
from knackpy._fields import Field

pp = pprint.PrettyPrinter(indent=4, depth=2)

class Record:
    def __repr__(self):
        separator = f" {self.index} ".center(26, "-")
        fields = f"".join(f"\n{str(field)}" for field in self.fields)
        return f"\n{separator}{fields}"
        
    def __init__(self, data, field_defs, index=None):
        self.index = index
        self.field_defs = field_defs
        self.fields = self._handle_data(data)
        

    def _handle_data(self, data):
        raw_keys = [key for key in data.keys() if "raw" in key]

        fields = []

        for key, value in data.items():

            if f"{key}_raw" in raw_keys:
                # skip a key that also has a raw key
                continue

            # proxy the raw key as the key
            key = key.replace("_raw", "")
            field_def = self.field_defs[key]
            fields.append(Field(field_def, value))

        return fields


class Records:
    """
    Knack record data proxy getter.
    """
    def __repr__(self):
        return f"""<Records [{len(self.data)} objects/views])"""

    def __init__(self, key_props, field_defs):
        self.field_defs = field_defs
        self.keys = self._generate_key_lookup(key_props)
        self.data = {}

    def _generate_key_lookup(self, key_props):

        keys = {}

        for key_prop in key_props:
            keys[key_prop["name"]] = key_prop["key"]
            keys[key_prop["key"]] = key_prop["key"]

        return keys

    def _record_generator(self, records):
        i = -1
        for record in records:
            i += 1
            yield Record(record, self.field_defs, index=i)

    def get(self, key):
        try:
            records = self.data[self.keys[key]]
            return self._record_generator(records)
        except KeyError:
            raise KeyError(f"Invalid object or view key: {key}. No records found.")