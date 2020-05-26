from knackpy.config.constants import BASE_URL
from knackpy._request import _request

import pdb 

class App:
    """
    Knack application wrapper. Stores app meta data, tables, fields, etc.
    """
    def __repr__(self):
        return f"<App [id={self.app_id}]>"

    def __init__(self, app_id, timeout=30):
        self.app_id = app_id
        self.timeout = timeout
        self.metadata = self._get_metadata()

    def _get_metadata(self, route=f"/applications"):
        url = f"{route}/{self.app_id}"
        res = _request("get", url, timeout=self.timeout)
        return res.json()["application"]
        