from datetime import datetime, timezone
import logging
import pdb

from knackpy.exceptions.exceptions import ValidationError


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
        return value

    def email(self, value):
        return value.get("email")

    def link(self, value):
        return value.get("url")

    def phone(self, value):
        return value.get("full")

    def image(self, value):
        # somtimes a dict, sometimes a str
        try:
            return value["url"]
        except TypeError:
            return value

    @staticmethod
    def date_time(value, tz=None):
        mills_timestamp = value.get("unix_timestamp")
        timestamp = mills_timestamp / 1000
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.astimezone(tz).isoformat()

    def connection(self, value):
        vals = [val["identifier"] for val in value]
        return vals if vals else None

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

    @staticmethod
    def correct_knack_timestamp(mills_timestamp, tz):
        """
        Receive a knack mills timestamp (type: int) and and pytz timezone and
        return a (naive) unix milliseconds timestamp int.

        You may be wondering why timezone settings are concern, given that Knackpy, like the
        Knack API, returns timestamp values as Unix timestamps in millesconds (thus, there is
        no timezone encoding at all). However, the Knack API confusingly returns millisecond
        timestamps in your localized timezone!

        For example, if you inspect a timezone value in Knack, e.g., 1578254700000, this value
        represents Sunday, January 5, 2020 8:05:00 PM **local time**.
        """
        timestamp = mills_timestamp / 1000
        # Don't use datetime.utcfromtimestamp()! this will assume the input timestamp is in local (system) time
        # If you try to pass our timezone to the tz parameter here, it will have no affect. Ask Guido why??
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        # All we've done so far is create a datetime object from our timestamp
        # now we have to remove the timezone info that we supplied
        dt_naive = dt_utc.replace(tzinfo=None)
        # Now we localize (i.e., translate) the datetime object to our local time
        # you cannot use datetime.replace() here, because it does not account for
        # daylight savings time. I know, this is completely insane. 
        dt_local = tz.localize(dt_naive)
        # Now we can convert our datetime object back to a timestamp
        unix_timestamp = dt_local.timestamp()
        # And add milliseconds
        return int(unix_timestamp * 1000)
