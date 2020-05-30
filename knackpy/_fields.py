from datetime import datetime, timezone
import logging
import pdb

import pytz

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
            mills_timestamp = value.get("unix_timestamp")
        except AttributeError:
            return None

        # create naive datetime data instance
        dt = datetime.fromtimestamp(mills_timestamp / 1000)
        # make it timezone-aware
        dt = dt.replace(tzinfo=timezone.utc)
        # return ISO-formatted str
        return dt.isoformat()

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

    @staticmethod
    def correct_knack_timestamp(knack_date_time_dict, timezone):
        """
        Receive a knack_date_time_dict (type: dict) and and pytz timezone and
        return same dict with a (naive) unix milliseconds timestamp value as
        `unix_timestamp`.

        You may be wondering why timezone settings are concern, given that Knackpy, like the
        Knack API, returns timestamp values as Unix timestamps in millesconds (thus, there is
        no timezone encoding at all). However, the Knack API confusingly returns millisecond
        timestamps in your localized timezone!

        For example, if you inspect a timezone value in Knack, e.g., 1578254700000, this value
        represents Sunday, January 5, 2020 8:05:00 PM **local time**.
        """
        try:
            mills_timestamp = knack_date_time_dict.get("unix_timestamp")
        except AttributeError:
            # knack_date_time_dict is not a dict, so it's almost definitely an empty
            # string (which Knack uses instead of `null`)
            return knack_date_time_dict

        timestamp = mills_timestamp / 1000
        # Don't use datetime.utcfromtimestamp()! this will assume the input timestamp is in local (system) time
        # If you try to pass our timezone to the tz parameter here, it will have no affect. Ask Guido why??
        dt_utc = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        # All we've done so far is create a datetime object from our timestamp
        # now we have to remove the timezone info that we supplied
        dt_naive = dt_utc.replace(tzinfo=None)
        # Now we localize (i.e., translate) the datetime object to our local time
        # you cannot use datetime.replace() here, because it does not account for
        # daylight savings time. I know, this is completely insane. 
        dt_local = timezone.localize(dt_naive)
        # Now we can convert our datetime object back to a timestamp
        unix_timestamp = dt_local.timestamp()
        # And add milliseconds
        knack_date_time_dict["unix_timestamp"] = int(unix_timestamp * 1000)
        return knack_date_time_dict
