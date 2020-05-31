from knackpy.exceptions.exceptions import ValidationError
from knackpy.utils import formatters

class FieldDef:
    """ Knack field defintion wrapper """
    def __repr__(self):
        name = getattr(self, "name", "(no name)")
        return f"<FieldDef [{name}]>"

    def __init__(self, **kwargs):
        # required properties
        for prop in ["_id","key","name","type"]:
            try:
                setattr(self, prop.replace("type", "type_"), kwargs[prop])

            except KeyError:
                raise ValidationError(f"FieldDef missing required property: '{prop}'")


        try:
            self.formatter = getattr(formatters, self.type_)
        except AttributeError:
            self.formatter = getattr(formatters, "default")
