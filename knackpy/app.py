import logging
import warnings

import pytz

from knackpy._fields import FieldDef
from knackpy._records import Records
from knackpy._knack_session import KnackSession
from knackpy.utils.utils import _humanize_bytes
from knackpy.utils.timezones import TZ_NAMES
from knackpy.exceptions.exceptions import ValidationError

import pdb


class App:
    """
    Knack application wrapper. This thing does it all, folks!
    """
    def __repr__(self):
        return f"""<App [{self.metadata["name"]}]>"""

    def __init__(self, app_id, metadata=None, api_key=None, timeout=30, tz_info=None):

        if not api_key:
            warnings.warn(
                "No API key has been supplied. Only public views will be accessible."
            )

        self.app_id = app_id
        self.api_key = api_key
        self.timeout = timeout
        
        self.session = KnackSession(self.app_id, self.api_key, timeout=timeout)
        self.metadata = self._get_metadata() if not metadata else metadata
        self.timezone = self._set_timezone(tz_info)
        self.field_defs = self._generate_field_defs()
        logging.debug(self)

    def info(self):
        total_obj = len(self.metadata.get("objects"))
        total_scenes = len(self.metadata.get("scenes"))
        total_records = self.metadata.get("counts").get("total_entries")
        total_size = _humanize_bytes(self.metadata.get("counts").get("asset_size"))

        return {
            "objects": total_obj,
            "scenes": total_scenes,
            "records": total_records,
            "size": total_size,
        }

    def _get_metadata(self, route=f"/applications"):
        route = f"{route}/{self.app_id}"
        res = self.session.request("get", route)
        return res.json()["application"]

    def _set_timezone(self, tz_info):
        """
        Knack stores timezone information in the app metadata, but it does not use IANA
        timezone database names. Instead it uses the descriptive names that are common,
        and apparently are standardized somewhere. E.g., Knack uses "Eastern Time
        (US & Canada)" instead of "US/Eastern".

        I'm sure these descriptive names are standardized somewhere, and I did not bother
        to munge the IANA timezone DB to figure it out, so I created the `TZ_NAMES` index
        in `knackpy.utils.timezones` by copying a table from the internets.
        
        As such, we can't be certain it contain all of the timezone names that knack uses in
        its metadata. So, this method will attempt to lookup the Knack metadata timezone
        in the TZ_NAMES index, and raise an error of it fails.

        Alternatively, the client can override the Knack timezone description by including
        an IANA-compliant timezone name (e.g., "US/Central")by passing the `tzinfo` kwarg
        when constructing the `App` innstance.

        See also, note in knackpy._fields.real_unix_timestamp_mills() about why we
        need valid timezone info to handle Knack records.
        """
        if tz_info:
             return pytz.timezone(TZ_NAMES[tz_info])
        try:
            tz_name = self.metadata["settings"]["timezone"]
            tz_info = [v for tz in TZ_NAMES for k, v in tz.items() if tz_name.upper() == k.upper()]
            return pytz.timezone(tz_info[0])
        
        except (pytz.exceptions.UnknownTimeZoneError, IndexError) as e:
            pass
        
        raise ValidationError("""
                Unknown timezone supplied. `tzinfo` should formatted as a timezone string
                compliant to the IANA timezone database.
                See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
            """)

    def _generate_field_defs(self):
        lookup = {}
        fields = [field for obj in self.metadata["objects"] for field in obj["fields"]]
        for field in fields:
            lookup[field["key"]] = FieldDef(**field)

        lookup["id"] = self._id_field_def()

        return lookup

    def _id_field_def(self):
        return FieldDef(_id="id", key="id", name="id", type="id")

    def _route(self, route_props):
        if route_props.get("scene"):
            return f"/pages/{route_props['scene']}/views/{route_props['key']}/records"
        else:
            return f"/objects/{route_props['key']}/records"

    def _get_route_props(self, user_key):
        route_props = {"key": None, "scene": None}

        for scene in self.metadata["scenes"]:
            for view in scene["views"]:
                if view["key"] == user_key:
                    route_props["key"] = user_key
                    route_props["scene"] = scene["key"]
                    return route_props

                elif view["name"] == user_key:
                    route_props["key"] = view["key"]
                    route_props["scene"] = scene["key"]
                    return route_props

        for obj in self.metadata["objects"]:
            if obj["key"] == user_key:
                route_props["key"] = user_key
                return route_props

            elif obj["name"] == user_key:
                route_props["key"] = obj["key"]
                return route_props

        raise ValidationError(f"Unknown Knack key supplied: `{knack_key}`")

    def get(self, *keys, **kwargs):
        """
        *keys: each arg must be an object or view key string that exists in the app
        **kwargs: supported kwargs are record_limit (type: int), max_attempts (type: int),
        and filters (type: dict). others are ignored.
        """
        self.data = {}

        for user_key in keys:
            route_props = self._get_route_props(user_key)
            
            try:
                kwargs["filters"] = kwargs["filters"].get(route_props["key"])
            except AttributeError:
                pass

            route = self._route(route_props)
            self.data[user_key] = self.session._get_paginated_data(route, **kwargs)

        self.generate_records()

    def generate_records(self):
        """
        Note this method is public to support the use case of BYO data.
        """
        self.records = Records(self.data, self.field_defs, self.timezone)

