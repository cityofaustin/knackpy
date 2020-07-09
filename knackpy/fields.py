import collections
from knackpy.models import FIELD_SETTINGS
from . import utils, formatters


def set_field_def_views(field_defs, metadata):
    """
    Update FieldDef's  `views` property to include a list of all view keys that use
    this field.
    """
    for scene in metadata["scenes"]:
        for view in scene["views"]:
            if view["type"] == "table":
                # must ignore "link" columns, etc
                field_keys = [
                    column["field"]["key"]
                    for column in view["columns"]
                    if column.get("field")
                ]

                for key in field_keys:
                    field_defs[key].views.append(view["key"])
            else:
                # todo: should we handle non-table views?
                continue

    return field_defs


def generate_field_defs(metadata):
    field_defs = {}

    for obj in metadata["objects"]:
        for field in obj["fields"]:
            # drop reserved word `type` from knack field def
            field["type_"] = field.pop("type")
            field["name"] = utils.valid_name(field["name"])
            field["object"] = obj["key"]

            try:
                if field["key"] == obj["identifier"]:
                    field["identifier"] = True
                else:
                    field["identifier"] = False

            except KeyError:
                # built-in "Accounts" does not have an identifier
                field["identifier"] = False

            field_defs[field["key"]] = FieldDef(**field)

    return field_defs


class FieldDef:
    """ Knack field defintion wrapper """

    def __repr__(self):
        name = getattr(self, "name", "(no name)")
        return f"<FieldDef '{name}'>"

    def __init__(self, **kwargs):

        for attr in [
            "key",
            "name",
            "type_",
            "object",
        ]:  # required definition attrs
            try:
                setattr(self, attr, kwargs[attr])
            except KeyError:
                raise KeyError(
                    f"FieldDef missing required FieldDef attribute: '{attr}'"
                )

        self.identifier = kwargs["identifier"] if kwargs.get("identifier") else False

        self.views = []

        settings = FIELD_SETTINGS.get(self.type_)

        self.subfields = settings.get("subfields") if settings else None

        self.use_knack_format = settings.get("use_knack_format") if settings else False

        try:
            self.formatter = getattr(formatters, self.type_)
        except AttributeError:
            self.formatter = getattr(formatters, "default")


class Field(collections.abc.Container):
    def __init__(self, key, data, field_def, timezone):
        self.key = key
        self.data = data
        self.field_def = field_def
        self.timezone = timezone

    def __repr__(self):
        if type(self.data) in [int, float]:
            value_repr = self.data
        else:
            value_repr = f"'{self.data}'"
        return f"<Field {{'{self.key}': {value_repr}}}>"

    def __contains__(self, item):
        if item in self.data:
            return True

    def format(self, format_labels=True, format_values=True):
        """
        Knack applies it's own standard formatting to values, which are always
        available at the non-raw key. Knack includes the raw key in the dict
        when formatting is applied, allowing access to the unformatted data.

        Generally, the Knack formatting, where it exists, is fine. However there
        are cases where we want to apply our own formatters, such datestamps,
        (where the formatted value does not include a timezone offset), or
        address fields, where we want to parse out the lat/lon properties as
        subfields.

        And there are still more cases, where we want to apply additional
        formatting to the knack-formatted value, e.g. Timers.

        See also: models.py, formatters.py.
        """
        value = self._format_value() if format_values else self.data
        key = self.field_def.name if format_labels else self.field_def.key
        return {key: value}

    def _format_value(self):
        kwargs = self._set_formatter_kwargs()

        try:
            return self.field_def.formatter(self.data, **kwargs)
        except AttributeError:
            # thrown when value is None
            return self.data

    def _set_formatter_kwargs(self):
        # TODO: these should probably be field_def properties set from config
        kwargs = {}

        if self.field_def.type_ == "date_time":
            kwargs["timezone"] = self.timezone

        return kwargs
