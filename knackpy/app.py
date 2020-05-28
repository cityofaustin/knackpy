import logging
import warnings

from knackpy._fields import FieldDef, Field
from knackpy._records import RecordCollection, Record
from knackpy._knack_session import KnackSession
from knackpy.utils._humanize_bytes import _humanize_bytes
from knackpy.exceptions.exceptions import ValidationError

import pdb


class App:
    """
    Knack application wrapper. This thing does it all, folks!
    """
    def __repr__(self):
        info_str = ", ".join([f"{value} {key}" for key, value in self.info.items()])
        return f"""<App [{self.metadata["name"]}]> ({info_str})"""

    def __init__(self, app_id, api_key=None, timeout=30):

        if not api_key:
            warnings.warn(
                "No API key has been supplied. Only public views will be accessible."
            )

        self.app_id = app_id
        self.api_key = api_key
        self.timeout = timeout
        self.session = KnackSession(self.app_id, self.api_key, timeout=timeout)
        self.metadata = self._get_metadata()
        self.field_defs = self._generate_field_lookup()
        self.view_lookup = self._generate_view_lookup()
        self.obj_lookup = self._generate_obj_lookup()
        self.info = self._parse_app_info()
        logging.debug(self)

    def _parse_app_info(self):
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

    def _generate_field_lookup(self):
        lookup = {}
        fields = [field for obj in self.metadata["objects"] for field in obj["fields"]]
        for field in fields:
            lookup[field["key"]] = FieldDef(**field)

        lookup["id"] = self._id_field_def()

        return lookup

    def _id_field_def(self):
        return FieldDef(_id="id", key="id", name="id", type="id")

    def _generate_view_lookup(self):
        return {
            view["key"]: {"key": view["key"], "scene": scene["key"], "name": view["name"]}
            for scene in self.metadata["scenes"]
            for view in scene["views"]
        }

    def _generate_obj_lookup(self):
        return {
            obj["key"]: {"key": obj["key"], "name": obj["name"] } for obj in self.metadata["objects"]
        }

    def _route(self, key_props):
        if "object" in key_props["key"]:
            return f"/objects/{key_props['key']}/records"

        else:
            return f"/pages/{key_props['scene']}/views/{key_props['key']}/records"


    def _generate_key_props(self, knack_key):
        
        try:
            # try to find a matching view key
            return self.view_lookup[knack_key]

        except KeyError:
            pass

        try:
            # try to find a matching view name
            for key, value in self.view_lookup.items():
                if value["name"] == knack_key:
                    return self.view_lookup[key]

            raise KeyError
        
        except KeyError:
            pass

        try:
            # try to find a matching object key
            return self.obj_lookup[knack_key]

        except KeyError as e:
            pass

        try:
            # try to find a matching object name
            for key, value in self.obj_lookup.items():
                if value["name"] == knack_key:
                    return self.obj_lookup[key]

            raise KeyError

        except KeyError:
            
            raise ValidationError(
                f"Unknown Knack key supplied: `{knack_key}`"
            )


    def get_data(self, *keys, **kwargs):
        """
        *keys: each arg must be an object or view key string that exists in the app
        **kwargs: supported kwargs are record_limit (type: int) and max_attempts (type: int). others are ignored.
        """
        key_props = [self._generate_key_props(key) for key in keys]
        self.records = RecordCollection()
        self.records.key_props = key_props
        self.records.generate_key_lookup(key_props)

        for key_prop in key_props:
            route = self._route(key_prop)
            data = self.session._get_paginated_data(route, **kwargs)
            self.records[key_prop["key"]] = self._handle_data(data)

        return None


    def _handle_data(self, data):
        records =  []
        for record in data:
            record = Record(record, self.field_defs)
            records.append(record)

        return records
    