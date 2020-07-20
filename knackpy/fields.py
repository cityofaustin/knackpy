from knackpy.models import FIELD_SETTINGS
from . import utils, formatters


def get_id_field_args():
    """TODO
    - id field is a global field def. weird, right?
    - field_defs should be immutable for this reason
    """
    return {"key": "id", "name": "id", "type": "id", "obj": None}


def set_field_def_views(key: str, scenes: list):
    """
    Update FieldDef's `views` property to include a list of all view keys that use this
    field.

    TODO: make side effect of FieldDef...and document
    """
    views = []
    for scene in scenes:
        for view in scene["views"]:
            if view["type"] == "table":

                # must ignore "link" columns, etc
                field_keys = [
                    column["field"]["key"]
                    for column in view["columns"]
                    if column.get("field")
                ]

                if key in field_keys:
                    views.append(view["key"])

                # associate the id field every view
                elif key == "id":
                    views.append(view["key"])

            else:
                # todo: should we handle non-table views?
                continue

    return views


class FieldDef:
    """ Knack field defintion wrapper """

    def __repr__(self):
        name = getattr(self, "name", "(no name)")
        return f"<FieldDef '{name}'>"

    def __init__(self, **kwargs):
        for attr in [
            # required definition attrs
            "key",
            "name",
            "type",
            "obj",
        ]:
            try:
                setattr(self, attr, kwargs[attr])
            except KeyError:
                raise KeyError(
                    f"FieldDef missing required FieldDef attribute: '{attr}'"
                )

        self.identifier = kwargs["identifier"] if kwargs.get("identifier") else False
        self.views = []
        self.settings = FIELD_SETTINGS.get(self.type)
        self.subfields = self.settings.get("subfields") if self.settings else None
        self.use_knack_format = (
            self.settings.get("use_knack_format") if self.settings else False
        )

        try:
            self.formatter = getattr(formatters, self.type)
        except AttributeError:
            self.formatter = getattr(formatters, "default")


def field_defs_from_metadata(metadata: dict):
    """Generate a list of FieldDef's from Knack metadata. Note the
    "set_field_def_views()" side effect, which assigns to prop "views" a list of view
    keys which use the field.

    Args:
        metadata (dict): Knack application metadata dict.

    Returns:
        list: A list of FieldDef instances.
    """
    field_defs = []

    for obj in metadata["objects"]:
        id_field_args = get_id_field_args()
        id_field_args["obj"] = obj["key"]

        field_defs.append(FieldDef(**id_field_args))

        for field in obj["fields"]:
            field["name"] = utils.valid_name(field["name"])
            # the object is also available at field["object_key"], but
            # this is not always available
            field["obj"] = obj["key"]

            try:
                if field["key"] == obj["identifier"]:
                    field["identifier"] = True
                else:
                    field["identifier"] = False

            except KeyError:
                # built-in "Accounts" does not have an identifier
                # also identifier may only be present if set manually in the builder?
                field["identifier"] = False

            field_defs.append(FieldDef(**field))

    for field_def in field_defs:
        field_def.views = set_field_def_views(field_def.key, metadata["scenes"])

    return field_defs


class Field(object):
    """A container for a single column of Knack data. This is the lowest-level
    container in the API. The hieracrchy being: App > Records > Record > Field.
    Typically you would not construct this class directly, but instead an App, which
    will generate Fields via App.records().

    More specifically, the API is designed so that you would typically interface with a
    Field instance through the records.Record class. That class operates on Fields by
    returning their values through Record[<field name>] or Record[<field key>].

    But it's fine to work directly with fields:
        - field.value: the unformatted input value
        - field.formatted: the formatted value
        - field.key: the knack field key
        - field.name: the knack field name

    Args:
        field_def (knackpy.fields.FieldDef): A knackpy FieldDef class object
        value (object): Anything, really.
        timezone ([pytz.timezone]): A pytz timezone object.
        knack_formatted_value (str, optional): There a fiew fields where it's easier to
            use knack's formatted value as a starting point, rather than the raw value.
            E.g. timer and name. In those cases, we  assign that value here and pass it
            on to the self.formatter() function for further formatting.
    """

    def __init__(
        self, field_def: FieldDef, value: object, timezone, knack_formatted_value=None
    ):
        self.key = field_def.key
        self.name = field_def.name
        self.raw = value
        self.field_def = field_def
        self.timezone = timezone
        self.knack_formatted_value = knack_formatted_value
        self.formatted = self._format()

    def __repr__(self):
        return f"<Field {{'{self.key}': '{self.formatted}'}}>"

    def __contains__(self, item):
        if item in self.raw:
            return True

    def _format(self):
        """
        Knack applies it's own standard formatting to values, which are always
        available at the non-raw key. Knack includes the raw key in the dict when
        formatting is applied, allowing access to the unformatted data.

        Generally, the Knack formatting, where it exists, is fine. However there are
        cases where we want to apply our own formatters, such datestamps, (where the
        formatted value does not include a timezone offset).

        And there are other cases where we want to apply additional formatting to the
        knack-formatted value, e.g. Timers.

        See also: models.py, formatters.py.
        """
        kwargs = self._set_formatter_kwargs()

        try:
            input_value = (
                self.knack_formatted_value if self.knack_formatted_value else self.raw
            )
            return self.field_def.formatter(input_value, **kwargs)
        except AttributeError:
            # thrown when value is None
            return self.raw

    def _set_formatter_kwargs(self):
        kwargs = {}

        if self.field_def.type == "date_time":
            kwargs["timezone"] = self.timezone

        return kwargs
