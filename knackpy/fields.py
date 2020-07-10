from collections.abc import Container

from knackpy.models import FIELD_SETTINGS
from . import utils, formatters


def set_field_def_views(field_defs, metadata):
    """
    Update FieldDef's `views` property to include a list of all view keys that use
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

    return field_defs


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
        )  # noqa:E501

        try:
            self.formatter = getattr(formatters, self.type)
        except AttributeError:
            self.formatter = getattr(formatters, "default")


class Field(Container):
    def __init__(self, key, value, field_def, timezone):
        self.key = key
        self.name = field_def.name
        self.value = value
        self.field_def = field_def
        self.timezone = timezone

    def __repr__(self):
        return f"{self.value}"

    def __contains__(self, item):
        if item in self.value:
            return True

    def format(self):
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
        kwargs = self._set_formatter_kwargs()

        try:
            return self.field_def.formatter(self.value, **kwargs)
        except AttributeError:
            # thrown when value is None
            return self.value

    def _set_formatter_kwargs(self):
        # TODO: these should probably be field_def properties set from config
        kwargs = {}

        if self.field_def.type == "date_time":
            kwargs["timezone"] = self.timezone

        return kwargs
