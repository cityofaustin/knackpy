from knackpy.config import constants
from knackpy.exceptions.exceptions import ValidationError
from knackpy.utils import formatters, utils


def set_field_def_views(field_defs, metadata):
    """
    Update FieldDef's  `views` property to include a list of all view keys that use
    this field.
    """
    for scene in metadata["scenes"]:
        for view in scene["views"]:
            if view["type"] == "table":
                field_keys = [column["field"]["key"] for column in view["columns"]]

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
                raise ValidationError(
                    f"FieldDef missing required FieldDef attribute: '{attr}'"
                )

        self.identifier = kwargs["identifier"] if kwargs.get("identifier") else False

        self.views = []

        settings = constants.FIELD_SETTINGS.get(self.type_)

        self.subfields = settings.get("subfields") if settings else None

        self.use_knack_format = settings.get("use_knack_format") if settings else False

        try:
            self.formatter = getattr(formatters, self.type_)
        except AttributeError:
            self.formatter = getattr(formatters, "default")
