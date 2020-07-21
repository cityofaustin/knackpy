from _io import BufferedReader
import json
import logging
import math
import random
import time
import typing
import warnings

import requests

from .models import MAX_ROWS_PER_PAGE


def _random_pause():
    """sleep for at least .333 seconds"""
    seconds = random.randrange(3, 10, 1)
    time.sleep(seconds / 10)


def _url(*, route: str, slug: str = None) -> str:
    """Format the API endpoint URL. This does not appear to be documented anywhere,
    but as discussed [here](https://github.com/cityofaustin/knackpy/pull/36), HIPAA
    accounts use a prefixed subdomain that includes their application's slug. E.g.:
    "my_org_name-api.com/v1/records/....".

    It turns out that non-HIPAA accounts can also use this prefix. So we'll just
    support this convention for all apps.

    Args:
        route (str): [description]
        slug (str, optional): [description]. Defaults to None.

    Returns:
        str: [description]
    """
    return (
        f"https://{slug}-api.knack.com/v1{route}"
        if slug
        else f"https://api.knack.com/v1{route}"
    )


def _route(
    *,
    obj: str = None,
    scene: str = None,
    view: str = None,
    record_id: str = "",
    app_id: str = None,
    asset_type: str = None,
) -> str:
    """Construct a Knack API route. Returns routes for:
        - metadata
        - object or view interactions
        - file/image uploads

    Args:
        obj (str, optional): A Knack object key. Defaults to None.
        scene (str, optional): A Knack scene key. Defaults to None.
        view (str, optional): A Knack view key. Defaults to None.
        record_id (str, optional): A knack record ID. Defaults to empty string.
        app_id (str): Knack [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id)  # noqa:E501
            string.
        asset_type (str, optional*): Required for file/image uploads and must be either
            `file` or `image`.

    Raises:
        KeyError: When an object key or both a scene and view key have
        not been supplied.

    Returns:
        `requests.Response`: A `requests` response object.
    """
    if scene and view:
        return f"/pages/{scene}/views/{view}/records"
    elif obj:
        return f"/objects/{obj}/records/{record_id}"
    elif app_id and asset_type:
        return f"/applications/{app_id}/assets/{asset_type}/upload"
    elif app_id and not asset_type:
        return f"/applications/{app_id}"

    raise KeyError(
        "Insufficient knack keys provided. Knack Requests requires an obj key or a scene and view key"  # noqa:E501
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
    files: BufferedReader = None,
) -> requests.Response:
    session = requests.Session()
    req = requests.Request(
        method, url, headers=headers, params=params, json=data, files=files
    )
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
                    _random_pause()
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
    slug: str = None,
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
        slug (str, optional): Your organization's slug (aka, subdomain). As found in
            your app metadata under accounts.slug.
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
    route = _route(obj=obj, scene=scene, view=view)

    url = _url(slug=slug, route=route)

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


def get_metadata(*, app_id: str, slug: str = None, timeout: int = 30) -> dict:
    """Fetch Knack application metadata. You can find your app's metadata at:
    `https://api.knack.com/v1/applications/<app_id:str>`.

    Args:
        app_id (str): A Knack application ID.
        slug (str, optional): Your organization's slug (aka, subdomain). As found in
            your app metadata under accounts/slug.

    Returns:
        dict: A dictionary of Knack application metadata.
    """
    route = _route(app_id=app_id)
    url = _url(slug=slug, route=route)
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
    slug: str = None,
    max_attempts: int = 5,
    timeout: int = 30,
):
    """Create, update, or delete a Knack record.

    Args:
        app_id (str): Knack [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id)  # noqa:E501
            string.
        api_key (str): [Knack API key](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).
        slug (str, optional): Your organization's slug (aka, subdomain). As found in
            your app metadata under accounts/slug.
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
    route = _route(obj=obj, record_id=record_id)
    method = _handle_method(method)
    url = _url(slug=slug, route=route)
    return _request(method=method, url=url, headers=headers, data=data).json()


def upload(
    *,
    app_id: str,
    api_key: str,
    obj: str,
    field: str,
    path: str,
    asset_type: str,
    record_id: str = None,
    slug: str = None,
    max_attempts: int = 5,
    timeout: int = 30,
):
    """Upload a file or image to Knack. This is a two-step process:

    1) Upload file asset to Knack storage
    2) Create/update a record that links to the file in storage

    Knack docs: https://www.knack.com/developer-documentation/#file-image-uploads

    Args:
        app_id (str): Knack [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id)  # noqa:E501
            string.
        api_key (str): [Knack API key](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).
        obj (str): The Knack object key which holds the record data.
        field (str): The knack field key of the field you're uploading into.
        path (str): The path to the file to be uploaded.
        asset_type (str): The type of Knack field you're uploading to. Must be `file` or
            `image`.
        record_id (str, optional): The knack record ID to which the upload will be
            attached. If `None`, will create a new record. Otherwise will update an
            existing record.
        slug (str, optional): Your organization's slug (aka, subdomain). As found in
            your app metadata under accounts/slug.
        max_attempts (int): The maximum number of attempts to make if a request times
            out. Default values that are set in `knackpy.api.request`. Defaults to 5.
        timeout (int, optional): Number of seconds to wait before a Knack API request
            times out. Further reading:
            [Requests docs](https://requests.readthedocs.io/en/master/user/quickstart/).
    """
    headers = _headers(app_id, api_key)
    route = _route(app_id=app_id, asset_type=asset_type)
    url = _url(route=route, slug=slug)
    method = "create" if not record_id else "update"

    with open(path, "rb") as file:
        files = {"files": file}
        res = _request(method="POST", url=url, headers=headers, files=files)

    file_id = res.json()["id"]

    data = {f"{field}": f"{file_id}", "id": record_id}

    return record(
        app_id=app_id, api_key=api_key, method=method, data=data, slug=slug, obj=obj
    )
