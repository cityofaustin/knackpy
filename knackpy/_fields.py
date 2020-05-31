from knackpy.exceptions.exceptions import ValidationError
from knackpy.utils import formatters, utils

class FieldDef:
    """ Knack field defintion wrapper """
    def __repr__(self):
        name = getattr(self, "name", "(no name)")
        return f"<FieldDef [{name}]>"

    def __init__(self, **kwargs):

        for attr in ["_id","key","name","type_", "object"]: # required definition attrs
            try:
                setattr(self, attr, kwargs[attr])
            except KeyError:
                raise ValidationError(f"FieldDef missing required FieldDef attribute: '{attr}'")

        self.views = []

        try:
            self.formatter = getattr(formatters, self.type_)
        except AttributeError:
            self.formatter = getattr(formatters, "default")
