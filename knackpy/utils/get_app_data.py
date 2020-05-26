import requests

def get_app_data(app_id, timeout=30):
    """
    Get Knack app metadata JSON
    """
    endpoint = "https://loader.knack.com/v1/applications/{}".format(app_id)
    res = requests.get(endpoint, timeout=timeout)
    res.raise_for_status()
    return res.json()["application"]