import csv
import warnings

from knackpy.utils import utils

class Records:
    """
    A wrapper for Knack record data. At initialization, the class is readied to yield
    records from Records.records().

    When Records.records() is called, a generator is returned. With each `yield` the
    generator handles the raw Knack record by updating any empty string values to NoneTypes,
    corrects Knack's "local" timestamps, and applies the client-specified formatting.
    """
    def __repr__(self):
        return f"<Records [{len(self.field_defs)} fields]>"

    def __init__(self, container_key, data, field_defs, timezone, format_values=False, format_keys=False):
        self.container_key = container_key
        self.data = data
        self.timezone = timezone
        self.format_keys = format_keys
        self.format_values = format_values

        self.field_defs = self._filter_field_defs_by_container_key(field_defs)
        return None

    def _filter_field_defs_by_container_key(self, field_defs):
        return [
            field_def
            for field_ley, field_def in field_defs.items()
            if self.container_key == field_def.object or self.container_key in field_def.views
        ]

    def records(self):
        for record in self.data:
            record = self.handle_record(record)
            yield record

    def handle_record(self, record):
        record = self._replace_empty_strings(record)

        record = self._correct_knack_timestamp(record, self.timezone)
        
        if not (self.format_keys or self.format_values):
            return record

        elif self.format_keys and not self.format_values:
            record = self._proxy_raw_keys(record)
            return {field_def.name: record[field_def.key] for field_def in self.field_defs}

        formatted_record = {}

        for field_def in self.field_defs:
                 
            value = self._handle_value(record, field_def)

            key = field_def.name

            if not field_def.subfields:
                formatted_record.update({key: value})
                continue

            subfield_dict = self._handle_subfields(key, value, field_def.subfields)
            formatted_record.update(subfield_dict)

        return formatted_record

    def _proxy_raw_keys(self, record):
        for key in [key for key in record.keys() if f"_raw" in key]:
            record[key.replace("_raw", "")] = record[key]
        return record

    def _handle_value(self, record, field_def):
        """
        Knack applies it's own standard formatting to values, which are always
        available at the non-raw key. Knack includes the raw key in the dict
        when formatting is applied, allowing access to the unformatted data.

        Generally, the Knack formatting, where it exists, is fine.
        However there are cases where we want to apply our own formatters, 
        such datestamps, (where the formatted value does not include a timezone
        offset), or address fields, where we want to parse out the lat/lon
        properties as subfields.

        And there are still more cases, where we want to apply additional
        formatting to the knack-formatted value, e.g. Timers.
        """

        if field_def.use_knack_format:
            return self._format_value(record.get(field_def.key), field_def)

        value = record.get(f"{field_def.key}_raw")
        return self._format_value(value, field_def)

    def _handle_subfields(self, key, value, subfields):
        try:
            return {f"{key}_{subfield}": value.get(subfield) for subfield in subfields}

        except AttributeError:
            return {key: value}

        except TypeError:
            import pdb; pdb.set_trace()

    def _replace_empty_strings(self, record):
        return {key: None if val == "" else val for key, val in record.items()}

    def _format_value(self, value, field_def):
        kwargs = self._set_formatter_kwargs(field_def)
        
        try:
            return field_def.formatter(value, **kwargs)
        except AttributeError:
            # thrown when value is None
            return value

    def _set_formatter_kwargs(self, field_def):
        kwargs = {}

        if field_def.type_ == "date_time":
            kwargs["timezone"] = self.timezone

        return kwargs

    def _correct_knack_timestamp(self, record, timezone):
        # see note in knackpy.utils.utils.correct_knack_timestamp
        for key, val in record.items():
            try:
                val["unix_timestamp"] = utils.correct_knack_timestamp(val["unix_timestamp"], timezone)
                record[key] = val
            except (KeyError, TypeError):
                pass

        return record

    def to_csv(
        self,
        *obj_or_view_keys,
        path="",
        delimiter=",",
        format_keys=False,
        format_values=False,
    ):
        print("NOT RE-IMPLEMTED!")
        pass
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
