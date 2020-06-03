
from knackpy.config import constants
from knackpy.exceptions.exceptions import ValidationError
from knackpy.utils import formatters, utils


def _set_field_def_views(field_defs, metadata):
    for scene in metadata["scenes"]:
        for view in scene["views"]:
            if view["type"] == "table":
                field_keys = [column["field"]["key"] for column in view["columns"]]

                for key in field_keys:
                    field_defs[key].views.append(view["key"])

            else:
                print("IGNORING", view["type"])

    return field_defs


def generate_field_defs(metadata):
    field_defs = {}

    for obj in metadata["objects"]:
        for field in obj["fields"]:
            # drop reserved word `type` from field def
            field["type_"] = field.pop("type")
            field["name"] = utils.valid_name(field["name"])
            field["object"] = obj["key"]
            field_defs[field["key"]] = FieldDef(**field)
        
    return _set_field_def_views(field_defs, metadata)

class FieldDef:
    """ Knack field defintion wrapper """

    def __repr__(self):
        name = getattr(self, "name", "(no name)")
        return f"<FieldDef [{name}]>"

    def __init__(self, **kwargs):

        for attr in [
            "_id",
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

        self.subfields = constants.FIELD_TYPE_SUBFIELDS.get(self.type_)
        self.views = []

        try:
            self.formatter = getattr(formatters, self.type_)
        except AttributeError:
            self.formatter = getattr(formatters, "default")
