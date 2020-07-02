import logging
import warnings

from knackpy import _knack_session
from knackpy.exceptions.exceptions import ValidationError

import pdb


def _route(obj=None, scene=None, view=None):
    """Construct a Knack API route. Reqires either an object key or a scene key
    and a view key.


    Args:
        obj (str, optional): A Knack object key. Defaults to None.
        scene (str, optional): A Knack scene key. Defaults to None.
        view (str, optional): A Knack view key. Defaults to None.

    Raises:
        ValidationError: When an object key or both a scene and view key have
        not been supplied.

    Returns:
        object: `requests` response object.
    """
    if scene and view:
        return f"/pages/{scene}/views/{view}/records"
    elif obj:
        return f"/objects/{obj}/records"

    raise ValidationError(
        f"Insufficient knack keys provided. Knack Requsts requires an obj key or a scene and view key"
    )


def get(app_id: str, **kwargs):
    """Get records from a knack object or view. This is the raw stuff with
    incorrect timestamps!

    supported kwargs:
        - api_key (str)
        - max_attempts (int)
        - record_limit (int)
        - filters (dict)
        - timeout (int)
        - format_keys
        - format_values

    Returns:
        list: List of Knack record objects.
    """
    obj = kwargs.pop("obj", None)
    scene = kwargs.pop("scene", None)
    view = kwargs.pop("view", None)
    route = _route(obj=obj, scene=scene, view=view)
    session = _knack_session.KnackSession(app_id, **kwargs)
    return session._get_paginated_data(route, **kwargs)


def metadata(app_id: str, **kwargs):
    """Fetch Knack application metadata. You can find your app's metadata at:
    `https://{subdomain}.knack.com/v1/applications`.

    Args:
        app_id (str): A Knack application ID.

    Returns:
        dict: A dictionary of Knack application metadata.
    """
    endpoint = f"/applications/{app_id}"
    session = _knack_session.KnackSession(app_id, **kwargs)
    res = session.request("get", endpoint)
    return res.json()["application"]
    

def create():
    ...


def update():
    ...


def delete():
    ...
