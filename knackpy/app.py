import collections
import logging
import warnings

import pytz

from knackpy._fields import FieldDef
from knackpy._records import RecordCollection
from knackpy._knack_session import KnackSession
from knackpy.utils import utils
from knackpy.utils.timezones import TZ_NAMES
from knackpy.exceptions.exceptions import ValidationError

import pdb


class App:
    """
    Knack application wrapper. This thing does it all, folks!
    """

    def __repr__(self):
        return f"""<App [{self.metadata["name"]}]>"""

    def __init__(self, app_id, metadata=None, api_key=None, timeout=30, tzinfo=None):

        if not api_key:
            warnings.warn(
                "No API key has been supplied. Only public views will be accessible."
            )

        self.app_id = app_id
        self.api_key = api_key
        self.timeout = timeout

        self.session = KnackSession(self.app_id, self.api_key, timeout=timeout)
        self.metadata = self._get_metadata() if not metadata else metadata
        self.tz = self._set_timezone(tzinfo)
        self.field_defs = self._generate_field_defs()
        self._set_field_def_views()
        self.container_index = self._generate_container_index()
        logging.debug(self)


    def info(self):
        total_obj = len(self.metadata.get("objects"))
        total_scenes = len(self.metadata.get("scenes"))
        total_records = self.metadata.get("counts").get("total_entries")
        total_size = utils._humanize_bytes(
            self.metadata.get("counts").get("asset_size")
        )

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

    def _set_timezone(self, tzinfo):
        """
        Knack stores timezone information in the app metadata, but it does not use IANA
        timezone database names. Instead it uses common descriptive names E.g., Knack uses
        "Eastern Time (US & Canada)" instead of "US/Eastern".

        I'm sure these descriptive names are standardized somewhere, and I did not bother
        to munge the IANA timezone DB to figure it out, so I created the `TZ_NAMES` index
        in `knackpy.utils.timezones` by copying a table from the internets.
        
        As such, we can't be certain our index contains all of the timezone names that knack
        uses in its metadata. So, this method will attempt to lookup the Knack metadata
        timezone in our TZ_NAMES index, and raise an error of it fails.

        Alternatively, the client can override the Knack timezone description by including
        an IANA-compliant timezone name (e.g., "US/Central")by passing the `tzinfo` kwarg
        when constructing the `App` innstance.

        See also, note in knackpy._fields.real_unix_timestamp_mills() about why we
        need valid timezone info to handle Knack records.
        """
        if tzinfo:
            return pytz.timezone(tzinfo)
        try:
            tz_name = self.metadata["settings"]["timezone"]
            tzinfo = [
                v
                for tz in TZ_NAMES
                for k, v in tz.items()
                if tz_name.upper() == k.upper()
            ]
            return pytz.timezone(tzinfo[0])

        except (pytz.exceptions.UnknownTimeZoneError, IndexError) as e:
            pass

        raise ValidationError(
            """
                Unknown timezone supplied. `tzinfo` should formatted as a timezone string
                compliant to the IANA timezone database.
                See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
            """
        )

    def _set_field_def_views(self):

        for scene in self.metadata["scenes"]:
            for view in scene["views"]:
                if view["type"] == "table":
                    field_keys = [column["field"]["key"] for column in view["columns"]]

                    for key in field_keys:
                        self.field_defs[key].views.append(view["key"])

                else:
                    print("IGNORING", view["type"])

    def _generate_field_defs(self):
        lookup = {}

        for obj in self.metadata["objects"]:
            for field in obj["fields"]:
                # drop reserved word `type` from field def
                field["type_"] = field.pop("type")
                field["name"] = utils._valid_name(field["name"])
                field["object"] = obj["key"]
                lookup[field["key"]] = FieldDef(**field)

        return lookup

    def _route(self, container):
        if container.get("scene"):
            return f"/pages/{container['scene']}/views/{container['key']}/records"
        else:
            return f"/objects/{container['key']}/records"

    def _generate_container_index(self):
        """
        Returns a dict of knack object keys, object names, view keys, and view names,
        that serves as lookup for finding Knack app record containers (objects or views)
        by name or key.

        Note that namespace conflicts are highlighly likely, especially with views.
        If an app has multiple views with the same name, the index will only have
        one reference to either (which ever name was processed last, below).

        If an app has object names that conflict with view names, the object names
        will take prioirty, and the lookup with have no entry for the view of this
        name.

        As such, the best practice is to use keys (object_xx or view_xx) as much 
        as possible, especially when fetching data from views.

        TODO: might be a good use case collections.ChainMap or Python v3.8's
        dataclasses: "https://docs.python.org/3/library/dataclasses.html"
        """
        
        container_index = {"_conflicts": []}
        Container = collections.namedtuple("Container",  "key name scene type_")
        
        for obj in self.metadata["objects"]:
            container = Container(key=obj["key"], scene=None, name=obj["name"], type_="object")
            # add both `name` and `key` identiefiers to index
            # if name already exists in index, add it to `_conflicts` instead.
            container_index[container.key] = container
            
            if container.name in container_index:
                container_index.conflicts.append(container)
            else:
                container_index[container.name] = container    
                    
        for scene in self.metadata["scenes"]:
            for view in scene["views"]:
                container = Container(key=view["key"], scene=scene["key"], name=view["name"], type_="view")
                # add both `name` and `key` identiefiers to index
                # if name already exists in index, add it to `_conflicts` instead.
                container_index[container.key] = container

            if container.name in container_index:
                container_index.conflicts.append(container)
            else:
                container_index[container.name] = container  

        return container_index

    def _get_route_props(self, client_key):
        try:
            return self.client_index[key]
        except KeyError:
            raise ValidationError(f"Unknown Knack key supplied: `{knack_key}`")

    def get(self, *client_keys, **kwargs):
        """
        *client_keys: each arg must be an object or view key or name string that  exists
            in the app
        **kwargs: supported kwargs are record_limit (type: int), max_attempts (type: int),
            and filters (type: dict). others are ignored.
        """
        self.data = {}

        for client_key in keys:
            container = self.container_index[client_key]

            try:
                kwargs["filters"] = kwargs["filters"].get(container.key)
            except AttributeError:
                pass

            route = self._route(container)
            self.data[container.key] = self.session._get_paginated_data(
                route, **kwargs
            )

        self.generate_records()

    def generate_records(self):
        """
        Note this method is public to support the use case of BYO data.
        """
        self.records = RecordCollection(
            self.data, self.container_index, self.field_defs, self.tz
        )
