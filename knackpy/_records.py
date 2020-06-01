import csv
import warnings

from knackpy.utils import utils


class RecordCollection:
    """
    A wrapper for record "containers" (objects or views) that provides
    a client interface for `get`-ing records by container name or key.
    """

    def __init__(self, data, container_index, field_defs, tz):
        self.container_index = container_index
        self.index = {
            container_key: Records(container_key, data[container_key], field_defs, tz)
            for container_key in data.keys()
        }

    def get(self, client_key, format_keys=False, format_values=False):
        # enables client to fetch by Knack key or name
        key = self.container_index[client_key].key

        return self.index.get(key).get(
            format_keys=format_keys, format_values=format_values
        )

    def keys(self):
        return self.index.keys()


class Records:
    """
    A wrapper for Knack record data. At initialization, the class is readied
    to handle calls from `get` method.

    The knackpy `App` API is designed such that it's expected that a `Record` 
    instance is proxied via `get` request to a `RecordCollection`, but you can
    work with this class directly if you'd like to utilize record handlers/formatters.

    When a container key or name is provided through `get`, a generator (`_record_generator()`)
    is returned, which processes each record as it is iterated upon, yielding the record
    according to the client-specified key and value formatting.
    """
    def __repr__(self):
        return f"<Records [{len(self.field_defs)} fields]>"

    def __init__(self, container_key, data, field_defs, tz):
        self.container_key = container_key
        self.data = data
        self.field_defs = self._filter_field_defs_by_container_key(
            field_defs, container_key
        )
        self.tz = tz

    def _filter_field_defs_by_container_key(self, field_defs, container_key):
        return [
            field_def
            for field_ley, field_def in field_defs.items()
            if container_key == field_def.object or container_key in field_def.views
        ]

    def get(self, format_keys=False, format_values=False):
        """
        Note that the state of self.format_keys/values is set
        every time `Records.get()` is called.
        """
        self.format_keys = format_keys
        self.format_values = format_values
        return self._record_generator()

    def _record_generator(self):
        for record in self.data:
            record = self._handle_record(record)
            yield record

    def _handle_record(self, record):
        # todo: don't actually subfield everyyyything
        handled_record = {"id": record["id"]}

        record = self._make_raw(record)

        for field_def in self.field_defs:
            key = field_def.key
            value = self._handle_value(record[key], field_def)
            formatted_key = self._handle_key(field_def)
            record_entry = (
                {formatted_key: value}
                if not self.format_values
                else self._formatted_record_entry(formatted_key, value)
            )
            handled_record.update(record_entry)

        return handled_record

    def _formatted_record_entry(self, key, value):
        try:
            return {f"{key}_{k}": v for k, v in value.items()}

        except AttributeError:
            return {key: value}

    def _make_raw(self, record):
        """
        A Knack record contains a mix of "raw" and not-raw keys. A single record may have
        a raw and not raw key for the same field. When a raw key is present, we want to
        ignore the not raw key (e.g., `field_11` and `field_11_raw`). The not raw key
        contains value which may be  marked-up by by Knack app formatting configuration.
        These are messy, and do not contain import attributes such as the unix timestamp,
        etc. So we want to ignore not raw-keys.
        """

        # identify "redundant" not-raw keys that have a raw key in the record
        for key in [key for key in record.keys() if f"_raw" in key]:
            # replace the not-raw key values with their raw values and drop raw_key
            non_raw_key = key.replace("_raw", "")
            record[non_raw_key] = record[key]

        return record

    def _handle_value(self, value, field_def):
        if value == "":
            # Knack JSON supplies strings instead of `null`. Replace these with NoneTypes
            return None

        value = self._correct_knack_timestamp(value, self.tz)
        kwargs = self._set_formatter_kwargs(field_def)

        return value if not self.format_values else field_def.formatter(value, **kwargs)

    def _set_formatter_kwargs(self, field_def):
        kwargs = {}

        if field_def.type_ == "date_time":
            kwargs["tz"] = self.tz

        return kwargs

    def _correct_knack_timestamp(self, value, tz):
        # see note in knackpy.utils.utils.correct_knack_timestamp
        try:
            value["unix_timestamp"] = utils.correct_knack_timestamp(
                value["unix_timestamp"], tz
            )
        except (KeyError, TypeError):
            pass
        return value

    def _handle_key(self, field_def):
        return field_def.key if not self.format_keys else field_def.name

    def to_csv(
        self,
        *obj_or_view_keys,
        path="",
        delimiter=",",
        format_keys=False,
        format_values=False,
    ):
        obj_or_view_keys = obj_or_view_keys if obj_or_view_keys else list(self.keys())

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
