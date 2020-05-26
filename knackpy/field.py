import pdb

data = {
    "key": "field_9",
    "label": "Text Formula simple",
    "required": False,
    "type_": "concatenation"
}

class Field:
    """ Knack field wrapper """
    def __repr__(self):
        label = getattr(self, "label", "(no label)")
        return f"<Field [{label}]>"

    def __init__(self, key=None, label=None, type_=None, required=False):
        self.key = key
        self.label = label
        self.required = required
        self.type = type_

        pass

bob = Field(**data)

pdb.set_trace()