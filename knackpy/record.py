from collections.abc import MutableMapping
from typing import Union

from . import utils
from . import fields as _fields
from .models import FIELD_SETTINGS


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
        identifier_value = (
            self.data[self.identifier] if self.identifier else self.data["id"]
        )
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
            return match_fields[0].raw
        else:
            # try to match by field name
            match_fields = [
                field for key, field in self.fields.items() if field.name == client_key
            ]
        if match_fields:
            # there can be only one
            return match_fields[0].raw

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
            # store the raw data if available
            value = self.raw[key_raw] if self.raw.get(key_raw) else self.raw[key]

            # there are a fiew fields where it's easier to just use knack's formatted
            # value. E.g. timer and name. in those cases, we want to store knack's
            # formatted value so that we can reference it when we assign a value to
            # Field.formatted.
            try:
                use_knack_format = FIELD_SETTINGS[field_def.type]["use_knack_format"]
            except KeyError:
                use_knack_format = False

            knack_formatted_value = self.raw[key] if use_knack_format else None

            field = _fields.Field(
                field_def,
                value,
                self.timezone,
                knack_formatted_value=knack_formatted_value,
            )

            fields[field.key] = field

        return fields

    def _handle_record(self):
        record = self._replace_empty_strings(self.data)
        record = self._correct_knack_timestamp(record, self.timezone)
        return record

    def format(self, keys: Union[list, bool] = True, values: Union[list, bool] = True):
        """Returns the record as a dict.
        Args:
            keys (bool or list, optional): If the keys should be formatted, or a list
                of field keys specifying the keys to be formatted.
            values (bool or list, optional): If values should be formatted, or a list
                of field keys specifying the values to be formatted

        Returns:
            dict: A dict of the record values with formatted (aka, humaized) keys
            and/or values.
        """
        record = {}

        for key, field in self.fields.items():
            try:
                # try to see if key is contained by list keys
                key = field.name if key in keys else key
            except TypeError:
                # assume keys is a bool
                key = field.name if keys else key
            try:
                # try to see if value is contained by list values
                value = field.formatted if key in values else field.raw
            except TypeError:
                # assume values is a bool
                value = field.formatted if values else field.raw

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
