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
        self.update(self.fields)

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
            return match_fields[0]
        else:
            # try to match by field name
            match_fields = [
                field for key, field in self.fields.items() if field.name == client_key
            ]

        return match_fields[0] if match_fields else None

    def __setitem__(self, key, value):
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
            field = _fields.Field(key, value, field_def, self.timezone)
            fields[field.key] = field

        return fields

    def _handle_record(self):
        record = self._replace_empty_strings(self.data)
        record = self._correct_knack_timestamp(record, self.timezone)
        return record

    def format(self, format_keys: bool = True, format_values: bool = True):
        """Returns the record as a dict.
        Args:
            format_keys (bool, optional): Defaults to True.
            format_values (bool, optional): Defaults to True.

        Returns:
            dict: A dict of the record values with
        """
        record = {}

        for key, field in self.fields.items():
            value = field.format() if format_values else field.value
            key = field.name if format_keys else field.key
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


class Records:
    """
    A wrapper for Knack record data. At initialization, the class is readied to
    yield records from Records.records().

    When Records.records() is called, a generator is returned. With each `yield`
    the generator handles the raw Knack record by updating any empty string
    values to NoneTypes, corrects Knack's "local" timestamps, and applies the
    client-specified formatting.
    """

    def __repr__(self):
        return f"<Records [{len(self.data)} records]>"

    def __init__(
        self, container_key, data, field_defs, timezone,
    ):
        self.container_key = container_key
        self.data = data
        self.timezone = timezone
        self.field_defs = self._filter_field_defs_by_container_key(field_defs)
        # find the identifier field
        self.identifier = [
            field_def.key for field_def in self.field_defs if field_def.identifier
        ][0]

        return None

    def _filter_field_defs_by_container_key(self, field_defs):
        return [
            field_def
            for field_def in field_defs
            if self.container_key == field_def.obj
            or self.container_key in field_def.views
        ]

    def records(self):
        for record in self.data:
            yield Record(record, self.field_defs, self.identifier, self.timezone)
