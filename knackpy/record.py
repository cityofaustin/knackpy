from collections.abc import MutableMapping

from . import utils
from . import fields as _fields


class Record(MutableMapping):
    """A dict-like object for storing record data."""

    def __init__(self, data, field_defs, identifier, timezone):
        self.data = data
        self.field_defs = field_defs
        self.identifier = identifier
        self.timezone = timezone
        self.raw = self._handle_record()
        self.fields = self._handle_fields()
        self.immutable = False
        self.update(self.fields)
        # we restrict re-assignment of field values after init
        # see the __setitem__ docstring
        self.immutable = True

    def __repr__(self):
        identifier_value = self.data[self.identifier]
        # if the identifier field has no value, use the record ID
        identifier_value = identifier_value if identifier_value else self.data["id"]
        return f"<Record '{identifier_value}'>"

    def __getitem__(self, client_key):
        """Return the field whose key or name matches the client-provided value.

        Args:
            client_key (str): A field key (e.g., "field_99") or field name.

        Returns:
            object: The field's value (dict, list, str, int, whatever Knack has in
            store for you.)
        """
        # first, try to match by field key
        # yes, there are better ways: https://stackoverflow.com/questions/2361426/get-the-first-item-from-an-iterable-that-matches-a-condition/2361899  # noqa
        match_fields = [
            field for key, field in self.fields.items() if field.key == client_key
        ]
        if match_fields:
            # there can be only one
            return match_fields[0].value
        else:
            # try to match by field name
            match_fields = [
                field for key, field in self.fields.items() if field.name == client_key
            ]
        if match_fields:
            # there can be only one
            return match_fields[0].value

        raise KeyError(client_key)

    def __setitem__(self, key, value):
        """Bad things will happen if you re-assign record values to anything other
        than a field class. This is not immediately obvious, because you can assign
        values to the record without issue, but some operations will fail after
        assignment of a non-Field value. e.g., .format() and dict().

        All that to say, we set immutable = True after init, and further attempts to
        __setitem__ will raise a TypeError.

        Raises:
            TypeError: 'Record' object does not support item assignment.
        """
        if self.immutable:
            raise TypeError("'Record' object does not support item assignment")

        self.fields[key] = value

    def __delitem__(self, key):
        del self.fields[key]

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def items(self):
        return self.fields.items()

    def keys(self):
        return [key for key in self.fields.keys()]

    def values(self):
        return [value for key, value in self.fields.items()]

    def names(self):
        return [field.name for key, field in self.fields.items()]

    def _handle_fields(self):
        fields = {}

        for field_def in self.field_defs:
            key = field_def.key
            key_raw = f"{key}_raw"
            # we want to handle the raw data, except for a few types as defined by the
            # "use_knack_format" property in models.py. raw values may not be present
            # if the field is empty
            value = (
                self.raw[key_raw]
                if not field_def.use_knack_format and self.raw[key] is not None
                else self.raw[key]
            )
            field = _fields.Field(field_def, value, self.timezone)
            fields[field.key] = field

        return fields

    def _handle_record(self):
        record = self._replace_empty_strings(self.data)
        record = self._correct_knack_timestamp(record, self.timezone)
        return record

    def format(self, keys: bool = True, values: bool = True):
        """Returns the record as a dict.
        Args:
            keys (bool, optional): If keys should be formatted.
            values (bool, optional): If values should be formatted.

        Returns:
            dict: A dict of the record values with formatted (aka, humaized) keys
            and/or values.
        """
        record = {}

        for key, field in self.fields.items():
            value = field.format() if values else field.value
            key = field.name if keys else field.key
            record.update({key: value})

        return record

    def _replace_empty_strings(self, record):
        return {key: None if val == "" else val for key, val in record.items()}

    def _correct_knack_timestamp(self, record, timezone):
        # see note in knackpy.utils.correct_knack_timestamp
        for key, val in record.items():
            try:
                val["unix_timestamp"] = utils.correct_knack_timestamp(
                    val["unix_timestamp"], timezone
                )
                record[key] = val
            except (KeyError, TypeError):
                pass

        return record
