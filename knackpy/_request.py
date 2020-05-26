import requests
from knackpy.config.constants import BASE_URL

def _request(method, route, **kwargs):
    url = f"{BASE_URL}{route}"
    res = requests.request(method, url, **kwargs)
    res.raise_for_status()
    return res
    