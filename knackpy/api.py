import logging
import warnings

from knackpy import _knack_session
from knackpy.exceptions.exceptions import ValidationError

import pdb


def _route(obj=None, scene=None, view=None):
    if scene and view:
        return f"/pages/{scene}/views/{view}/records"
    elif obj:
        return f"/objects/{obj}/records"

    raise ValidationError(
        f"Insufficient knack keys provided. Knack Requsts requires an obj key or a scene and view key"
    )


def get(app_id, **kwargs):
    """
    Get records from a knack object or view. This is the raw stuff with incorrect timestamps!

    required kwargs:
        obj (str): the knack object key, e.g. `object_1`
        --or--
        scene (str): the knack scene key, e.g., `scene_1`
        view (str): the knack view key, e.g., `view_1`

    optional kwargs:
        - api_key (str)
        - max_attempts (int)
        - record_limit (int)
        - filters (dict)
        - timeout (int)
        - format_keys
        - format_values
    """
    obj = kwargs.pop("obj", None)
    scene = kwargs.pop("scene", None)
    view = kwargs.pop("view", None)
    route = _route(obj=obj, scene=scene, view=view)
    session = _knack_session.KnackSession(app_id, **kwargs)
    return session._get_paginated_data(route, **kwargs)


def create():
    pass


def update():
    pass


def delete():
    pass
