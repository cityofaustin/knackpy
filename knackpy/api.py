import json
import logging
import math
import typing
import warnings

import requests

from .models import MAX_ROWS_PER_PAGE


def _url(*, subdomain: str, route: str) -> str:
    return f"https://{subdomain}.knack.com/v1{route}"


def _record_route(
    obj: str = None, scene: str = None, view: str = None, record_id: str = ""
) -> str:
    """Construct a Knack API route. Reqires either an object key or a scene key
    and a view key.

    Args:
        obj (str, optional): A Knack object key. Defaults to None.
        scene (str, optional): A Knack scene key. Defaults to None.
        view (str, optional): A Knack view key. Defaults to None.
        record_id (str, optional): A knack record ID. Defaults to empty string.

    Raises:
        KeyError: When an object key or both a scene and view key have
        not been supplied.

    Returns:
        object: `requests` response object.
    """
    if scene and view:
        return f"/pages/{scene}/views/{view}/records"
    elif obj:
        return f"/objects/{obj}/records/{record_id}"

    raise KeyError(
        "Insufficient knack keys provided. Knack Requests requires an obj key or a scene and view key"  # noqa
    )


def _headers(app_id: str, api_key: str):
    headers = {
        "X-Knack-Application-Id": app_id,
        "X-Knack-REST-API-KEY": api_key if api_key else "knack",
    }
    return headers


def _request(
    *,
    method: str,
    url: str,
    headers: dict,
    timeout: int = 30,
    params: dict = None,
    data: dict = None,
) -> requests.Response:
    session = requests.Session()
    req = requests.Request(method, url, headers=headers, params=params, json=data)
    prepped = req.prepare()
    res = session.send(prepped, timeout=timeout)
    res.raise_for_status()
    return res


def _continue(total_records: int, current_records: int, record_limit: int) -> bool:
    if total_records is None:
        return True

    elif current_records < record_limit and total_records > current_records:
        return True

    return False


def _get_paginated_records(
    *,
    app_id: str,
    url: str,
    max_attempts: int,
    record_limit: int,
    rows_per_page: int,
    api_key: str = None,
    timeout: int = None,
    filters: typing.Union[dict, list] = None,
) -> list:
    headers = _headers(app_id, api_key)
    records = []
    total_records = None
    page = 1

    while _continue(total_records, len(records), record_limit):
        attempts = 0
        params = {"page": page, "rows_per_page": rows_per_page, "filters": filters}

        while True:
            logging.debug(
                f"Getting {rows_per_page} records from page {page} from {url}"
            )

            try:
                res = _request(
                    method="GET",
                    url=url,
                    headers=headers,
                    timeout=timeout,
                    params=params,
                )

            except requests.exceptions.Timeout as e:
                warnings.warn(
                    f"Request timeout on attempt #{attempts}. Trying again..."
                )
                if attempts < max_attempts:
                    attempts += 1
                    continue
                else:
                    raise e
            break

        total_records = res.json()[
            "total_records"
        ]  # note that this number could change between requests
        records += res.json()["records"]

        page += 1

    # lazily shaving off any remainder to keep the client happy
    return records[0:record_limit] if record_limit < math.inf else records


def get(
    *,
    app_id: str,
    api_key: str = None,
    obj: str = None,
    scene: str = None,
    view: str = None,
    record_limit: int = None,
    filters: dict = None,
    max_attempts: int = 5,
    timeout: int = 30,
) -> [list, requests.Response]:
    """Get records from a knack object or view. This is the raw stuff with
    incorrect timestamps!

    Args:
        app_id (str): [description]
        api_key (str, optional): [description]. Defaults to None.
        obj (str, optional): [description]. Defaults to None.
        scene (str, optional): [description]. Defaults to None.
        view (str, optional): [description]. Defaults to None.
        max_attempts (int, optional): [description]. Defaults to 5.
        record_limit (int, optional): [description]. Defaults to None (which is
            handled as infinity).
        timeout (int, optional): [description]. Defaults to 30.
        filters ([list, dict], optional): Knack record filter dict or list. Defaults
            to None.

    Returns:
        list: Knack records.
    """
    route = _record_route(obj=obj, scene=scene, view=view)

    url = _url(subdomain="api", route=route)

    record_limit = record_limit if record_limit else math.inf

    filters = json.dumps(filters) if filters else None

    rows_per_page = (
        MAX_ROWS_PER_PAGE if record_limit >= MAX_ROWS_PER_PAGE else record_limit
    )

    return _get_paginated_records(
        app_id=app_id,
        api_key=api_key,
        url=url,
        max_attempts=max_attempts,
        record_limit=record_limit,
        rows_per_page=rows_per_page,
        filters=filters,
    )


def get_metadata(*, app_id: str, timeout: int = 30) -> dict:
    """Fetch Knack application metadata. You can find your app's metadata at:
    `https://{subdomain}.knack.com/v1/applications/<app_id:str>`.

    Args:
        app_id (str): A Knack application ID.

    Returns:
        dict: A dictionary of Knack application metadata.
    """
    url = _url(subdomain="loader", route=f"/applications/{app_id}")
    return _request(method="GET", url=url, headers=None).json()


def _handle_method(method: str):
    if method == "create":
        return "POST"

    elif method == "update":
        return "PUT"

    elif method == "delete":
        return "DELETE"

    else:
        raise TypeError(
            f"""Unknown record method requested: {method}. Choose from create, update,
            or delete."""
        )


def record(
    *,
    app_id: str,
    api_key: str,
    data: dict,
    method: str,
    obj: str,
    max_attempts: int = 5,
    timeout: int = 30,
):
    """Create, update, or delete a Knack record.

    Args:
        app_id (str): Knack [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id)  # noqa:E501
            string.
        api_key (str): [Knack API key](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).
        data (dict): The Knack record data payload.
        method (str): Choose from `create`, `update`, or `delete`.
        obj (str, optional): The Knack object key which holds the record data.
        max_attempts (int): The maximum number of attempts to make if a request times
            out. Default values that are set in `knackpy.api.request`. Defaults to 5.
        timeout (int, optional): Number of seconds to wait before a Knack API request
            times out. Further reading:
            [Requests docs](https://requests.readthedocs.io/en/master/user/quickstart/).

    Returns:
        dict: The updated or newly created Knack record data, or, if deleting a record: `{"delete": true}`
    """
    record_id = data["id"] if method != "create" else ""
    headers = _headers(app_id, api_key)
    route = _record_route(obj=obj, record_id=record_id)
    method = _handle_method(method)
    url = _url(subdomain="api", route=route)
    return _request(method=method, url=url, headers=headers, data=data).json()
