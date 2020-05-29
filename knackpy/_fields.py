import logging
from knackpy.exceptions.exceptions import ValidationError

import pdb


class Formatter:
    def __init__(self, type_):
        try:
            self.formatter = getattr(self, type_)

        except AttributeError:
            self.formatter = self.default

    def default(self, value):
        """ Handles types:
        - auto_increment
        - average
        - boolean
        - concatenation
        - connection
        - count
        - currency
        - file
        - id  x
        - multiple_choice  x
        - name  x
        - number 
        - password
        - rating
        - rich_text
        - short_text  x
        - signature
        - sum
        - timer  x
        - user_roles
        """
        return None if value == "" else value

    def email(self, value):
        try:
            return value.get("email")

        except AttributeError:
            return None

    def link(self, value):
        try:
            return value.get("url")

        except AttributeError:
            return None

    def phone(self, value):
        try:
            return value.get("full")
        except AttributeError:
            return None

    def image(self, value):
        # somtimes a dict, sometimes a str
        try:
            return value["url"]
        except TypeError:
            return value
        except AttributeError:
            return None

    def date_time(self, value):
        try:
            return value.get("iso_timestamp")
        except AttributeError:
            return None

    def connection(self, value):
        try:
            vals = [val["identifier"] for val in value]
            return vals if vals else None

        except AttributeError:
            return None


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
        self.formatter = Formatter(self.type_).formatter

    def _validate(self):
        REQUIRED_PROPS = ["_id", "key", "name", "type_"]
        errors = [f"'{key}'" for key in REQUIRED_PROPS if not getattr(self, key)]

        if errors:
            # this should never happen unless Knack changes their API
            raise ValidationError(
                f"Field missing required properties: {{ {', '.join(errors)} }}"
            )
        pass
