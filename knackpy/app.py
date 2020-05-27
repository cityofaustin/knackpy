import logging
from pprint import pprint as print
import warnings

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

    def _generate_view_lookup(self):
        return {
            view["key"]: {"scene": scene["key"], "name": view["name"]}
            for scene in self.metadata["scenes"]
            for view in scene["views"]
        }

    def _generate_obj_lookup(self):
        return {obj["key"]: {"name": obj["name"]} for obj in self.metadata["objects"]}

    def _route(self, key):
        """
        Get the API route for an view key, and object key, an object name, or a view name.

        If using names instead of keys, the client is responsibile for worrying about namespace conflicts.
        """
        try:
            return self._object_route(key)

        except IndexError:
            pass

        try:
            return self._view_route(key)

        except (IndexError, KeyError):
            raise ValidationError(f"Unknown Knack key supplied: `{key}`")

    def _view_route(self, key):
        try:
            # try to find a matching view key
            scene = self.view_lookup[key]
            return f"/pages/{scene}/views/{key}/records"

        except KeyError:
            pass

        try:
            # try to find a matching view name
            match = [
                (value["scene"], view_key)
                for view_key, value in self.view_lookup.items()
                if value["name"] == key
            ]
            return f"/pages/{match[0][0]}/views/{match[0][1]}/records"

        except IndexError as e:
            raise e

    def _object_route(self, key):
        try:
            # try to find a matching object key
            match = self.obj_lookup[key]
            return f"/objects/{key}/records"
        except KeyError:
            pass

        try:
            # try to find a matching object name
            match = [
                obj_key
                for obj_key, value in self.obj_lookup.items()
                if value["name"] == key
            ]
            return f"/objects/{match[0]}/records"

        except IndexError as e:
            raise e

    def get_data(self, *keys, **kwargs):
        """
        *keys: each arg must be an object or view key string that exists in the app
        **kwargs: supported kwargs are record_limit (type: int) and max_attempts (type: int). others are ignored.
        """
        self.data = {}

        for key in keys:
            route = self._route(key)
            self.data[key] = self.session._get_paginated_data(route, **kwargs)

        return None
