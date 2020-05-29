import logging
import warnings

from knackpy._fields import FieldDef
from knackpy._records import Records
from knackpy._knack_session import KnackSession
from knackpy.utils.utils import _humanize_bytes
from knackpy.exceptions.exceptions import ValidationError

import pdb


class App:
    """
    Knack application wrapper. This thing does it all, folks!
    """
    def __repr__(self):
        return f"""<App [{self.metadata["name"]}]>"""

    def __init__(self, app_id, metadata=None, api_key=None, timeout=30):

        if not api_key:
            warnings.warn(
                "No API key has been supplied. Only public views will be accessible."
            )

        self.app_id = app_id
        self.api_key = api_key
        self.timeout = timeout
        self.session = KnackSession(self.app_id, self.api_key, timeout=timeout)
        self.metadata = self._get_metadata() if not metadata else metadata
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
        **kwargs: supported kwargs are record_limit (type: int) and max_attempts (type: int). others are ignored.
        """
        self.data = {}

        for user_key in keys:
            route_props = self._get_route_props(user_key)
            route = self._route(route_props)
            self.data[user_key] = self.session._get_paginated_data(route, **kwargs)

        self.generate_records()

    def generate_records(self):
        """
        Note this method is public to support the use case of BYO data.
        """
        self.records = Records(self.data, self.field_defs)

