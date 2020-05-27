from knackpy.exceptions.exceptions import ValidationError

import pdb

class Field:
    """ Knack field  wrapper """
    def __repr__(self):
        return f"{self.field_def.name}: {self.value} ({self.field_def.key})"

    def __init__(self, field_def, value, from_raw=False):
        self.field_def = field_def
        self.value = value
        pass

class FieldDef:
    """ Knack field defintion wrapper """
    def __repr__(self):
        name = getattr(self, "name", "(no name)")
        return f"<FieldDef [{name}]>"

    def __init__(self, **kwargs):
        # required properties
        self._id = kwargs.get("_id", None)
        self.key = kwargs.get("key", None)
        self.name = kwargs.get("name", None)
        self.type_ = kwargs.get("type", None)

        # optional properties
        self.conditional = kwargs.get("conditional", None)
        self.default = kwargs.get("default", None)
        self.format = kwargs.get("format", None)
        self.immutable = kwargs.get("immutable", None)
        self.object_key = kwargs.get("object_key", None)
        self.relationship = kwargs.get("relationship", None)
        self.required = kwargs.get("required", None)
        self.rules = kwargs.get("rules", None)
        self.unique = kwargs.get("unique", None)
        self.user = kwargs.get("user", None)
        self.validation = kwargs.get("validation", None)

        self._validate()

    def _validate(self):
        # this should never error, unless Knack changes their API
        REQUIRED_PROPS = ["_id", "key", "name", "type_"]
        errors = [f"'{key}'" for key in REQUIRED_PROPS if not getattr(self, key)]

        if errors:
            raise ValidationError(
                f"Field missing required properties: {{ {', '.join(errors)} }}"
            )
        pass