from collections.abc import MutableMapping

from . import utils
from . import fields as _fields

# class Record(MutableMapping):
class Record:
    def __repr__(self):
        identifier_value = self.data[self.identifier]
        identifier_value = identifier_value if identifier_value else ("undefined")
        return f"<Record '{identifier_value}'>"

    def __init__(self, data, field_defs, identifier, timezone):
        self.data = data
        self.field_defs = field_defs
        self.identifier = identifier
        self.timezone = timezone
        self.raw = self._handle_record()
        self.fields = self._handle_fields()

    def _handle_fields(self):
        fields = []

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
            fields.append(field)

        return fields

    def _handle_record(self):
        record = self._replace_empty_strings(self.data)
        record = self._correct_knack_timestamp(record, self.timezone)
        return record

    def format(self, format_labels=True, format_values=True):
        record = {}

        for field in self.fields:
            formatted = field.format(
                format_labels=format_labels, format_values=format_values
            )
            record.update(formatted)

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
        try:
            self.identifier = [
                field_def.key for field_def in self.field_defs if field_def.identifier
            ][0]
        except IndexError:
            # it seems that the object will not have an identifer in the
            # metadata if it has not been manually set by the user knack
            # presumably just uses the first field that was created with the
            # object. we'll use the id
            self.identifier = "id"
        return None

    def _filter_field_defs_by_container_key(self, field_defs):
        return [
            field_def
            for field_def in field_defs
            if self.container_key == field_def.object
            or self.container_key in field_def.views
        ]

    def records(self):
        for record in self.data:
            yield Record(record, self.field_defs, self.identifier, self.timezone)
