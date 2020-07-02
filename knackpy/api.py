import logging
import math
import typing
import knackpy
from knackpy.exceptions.exceptions import ValidationError
import requests

"""
heavy construction.
todo:
- move app calls to this api
- look through the args passing between funcs

SESSION:
- stores last response

API:
- returns response obj
- app - tries to parse records, stores response, how to inspect response errors? 

"""

MAX_ROWS_PER_PAGE = 1000  # max supported by Knack API


def _url(*, subdomain: str, route: str):
    return f"https://{subdomain}.knack.com/v1{route}"


def _record_route(
    obj: str = None, scene: str = None, view: str = None, record_id: str = ""
):
    """Construct a Knack API route. Reqires either an object key or a scene key
    and a view key.

    Args:
        obj (str, optional): A Knack object key. Defaults to None.
        scene (str, optional): A Knack scene key. Defaults to None.
        view (str, optional): A Knack view key. Defaults to None.
        record_id (str, optional): A knack record ID. Defaults to empty string.

    Raises:
        ValidationError: When an object key or both a scene and view key have
        not been supplied.

    Returns:
        object: `requests` response object.
    """
    if scene and view:
        return f"/pages/{scene}/views/{view}/records"
    elif obj:
        return f"/objects/{obj}/records/{record_id}"

    raise ValidationError(
        "Insufficient knack keys provided. Knack Requsts requires an obj key or a scene and view key"  # noqa
    )


def _headers(app_id: str, api_key: str):
    headers = {
        "X-Knack-Application-Id": app_id,
        "X-Knack-REST-API-KEY": api_key if api_key else "knack",
    }
    return headers


def _request(
    *, method: str, url: str, headers: dict, timeout: int = 30, params: dict = None
):
    session = requests.Session()
    req = requests.Request(method, url, headers=headers, params=params)
    prepped = req.prepare()
    return session.send(prepped, timeout=timeout)


def _continue(total_records, current_records, record_limit):
    if total_records is None:
        return True

    elif current_records < record_limit and total_records > current_records:
        return True

    return False


def _get_paginated_data(
    *,
    app_id: str,
    url: str,
    max_attempts: int,
    record_limit: int,
    rows_per_page: int,
    api_key: str = None,
    timeout: int = None,
    filters: typing.Union[dict, list] = None,
):
    """[summary]

    Args:
        app_id (str): [description]
        url (str): [description]
        max_attempts (int): [description]
        record_limit (int): [description]
        timeout (int): [description]
        rows_per_page (int): [description]
        filters ([type], optional): [description]. Defaults to None.
        api_key (str, optional): [description]. Defaults to None.

    Raises:
        e: [description]

    Returns:
        list: Knack records.
        requests.Response: If HTTPErrors, else None
    """
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

        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            return None, res

        total_records = res.json()[
            "total_records"
        ]  # note that this number could change between requests
        records += res.json()["records"]

        page += 1

    # lazily shaving off any remainder to keep the client happy
    return records[0:record_limit] if record_limit < math.inf else records, None


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
):
    """Get records from a knack object or view. This is the raw stuff with
    incorrect timestamps!
        
    Args:
        app_id (str): [description]
        api_key (str, optional): [description]. Defaults to None.
        obj (str, optional): [description]. Defaults to None.
        scene (str, optional): [description]. Defaults to None.
        view (str, optional): [description]. Defaults to None.
        max_attempts (int, optional): [description]. Defaults to 5.
        record_limit (int, optional): [description]. Defaults to None.
        timeout (int, optional): [description]. Defaults to None.
        filters (dict, optional): [description]. Defaults to None.

    Returns:
        list: Knack records.
        requests.Response: The Requests Response object if it contains an HTTPError, else None
    """
    route = _record_route(obj=obj, scene=scene, view=view)

    url = _url(subdomain="api", route=route)

    headers = _headers(app_id, api_key)

    record_limit = record_limit if record_limit else math.inf

    filters = json.dumps(filters) if filters else None

    rows_per_page = (
        MAX_ROWS_PER_PAGE if record_limit >= MAX_ROWS_PER_PAGE else record_limit
    )

    return _get_paginated_data(
        app_id=app_id,
        api_key=api_key,
        url=url,
        max_attempts=max_attempts,
        record_limit=record_limit,
        rows_per_page=rows_per_page,
        filters=filters,
    )


def metadata(*, app_id: str, timeout: int = 30):
    """Fetch Knack application metadata. You can find your app's metadata at:
    `https://{subdomain}.knack.com/v1/applications/<app_id:str>`.

    Args:
        app_id (str): A Knack application ID.

    Returns:
        dict: A dictionary of Knack application metadata.
    """
    url = _url(subdomain="loader", route=f"/applications/{app_id}")
    res = _request(method="GET", url=url, headers=None)
    res.raise_for_status()
    return res.json()["application"]


def _handle_method(method: str):
    if method == "create":
        return "POST"

    elif method == "update":
        return "PUT"

    elif method == "delete":
        return "DELETE"

    else:
        raise ValidationError(
            f"Unknown method requested: {method}. Choose from `create`, `update`, or `delete`."
        )  # noqa


def record():
    ...


# def record(
#     data: dict,
#     *,
#     app_id: str,
#     method: str,
#     api_key: str,
#     obj: str,
#     timeout: int = 10,
#     max_attempts: int = 5,
# ):
#     print("not implemented: test with real data to understand error")
#     if method != "create" and not data.get("id"):
#         raise ValidationError(
#             "Unable to perform requested method. Data is missing an `id` property."
#         )  # noqa

#     session = _knack_session.KnackSession(
#         app_id, timeout=timeout, max_attempts=max_attempts
#     )
#     route = _record_route(obj=obj)
#     method = _handle_method(method)
#     res = session.request(method, route)
#     breakpoint()
#     return res.json()
