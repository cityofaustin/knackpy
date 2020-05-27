import logging
from pprint import pprint as print
import warnings

from knackpy._request import KnackSession
from knackpy.utils._humanize_bytes import _humanize_bytes
from knackpy.exceptions.exceptions import ValidationError


import pdb 

class App:
    """
    Knack application wrapper. Stores app meta data, tables, fields, etc.
    """
    def __repr__(self):
        info_str = ", ".join([f"{value} {key}" for key, value in self.info.items()])
        return f"""<App [{self.metadata["name"]}]> ({info_str})"""

    def __init__(self, app_id, api_key=None, timeout=30):

        if not api_key:
            warnings.warn("No API key has been supplied. Only public views will be accessible.")

        self.app_id = app_id
        self.api_key = api_key
        self.timeout = timeout
        self.session = KnackSession(self.app_id, self.api_key, timeout=timeout)
        """
        Responses are accumualted at `self.responses` during the life of the instance. You might
        want to inspect these for some reason. E.g., you're developing a new version of Knackpy ;)
        """
        self.responses = []
        self.metadata = self._get_metadata()
        self.view_lookup = self._generate_view_lookup()
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
        self.responses.append(res)
        return res.json()["application"]
    
    def _generate_view_lookup(self):
        return { view["key"]: { "scene": scene["key"] } for scene in self.metadata["scenes"] for view in scene["views"]}

    def _validate_key(self, key):
        obj_keys = [obj["key"] for obj in self.metadata["objects"]]
        view_keys = list(self.view_lookup.keys())

        if key in obj_keys:
            return {"key": key, "type": "object"}

        if key in view_keys:
            return {"key": key, "type": "view", "scene": self.view_lookup[key]["scene"]}
    
        raise ValidationError(f"Unknown Knack key supplied. `{key}` not in {{ {', '.join([key for key in obj_keys + view_keys]) } }}")

    def _route(self, key_dict):
        if key_dict["type"] == "object":
            return f"/objects/{key_dict['key']}/records"
        else:
            return f"/pages/{key_dict['scene']}/views/{key_dict['key']}/records"

    def get_data(self, *keys, **kwargs):
        """
        *keys: each arg must be an object or view key string that exists in the app
        **kwargs: supported kwargs are rows_per_page, page_limit, and max_attempts. others
            are ignored.
        """
        todos = [self._validate_key(key) for key in keys]
        data = {}

        for key_dict in todos:
            key = key_dict["key"]
            data[key] = []
            route = self._route(key_dict)
            responses = self.session._paginated(route, **kwargs)
            
            for res in responses:
                data[key] += res.json()["records"]

        self.data_raw = data
        return None
        
        
