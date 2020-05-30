import json
import logging
import math
import warnings

import requests

from knackpy.exceptions.exceptions import ValidationError

MAX_ROWS_PER_PAGE = 1000  # max supported by Knack API


class KnackSession:
    """ A `Requests` wrapper with Knack helpers """

    def __repr__(self):
        return f"""<KnackSession [id={self.app_id}]>"""

    def __init__(self, app_id, api_key, timeout=None):
        self.app_id = app_id
        self.headers = self._headers(app_id, api_key)
        self.session = requests.Session()
        self.timeout = timeout

    def _headers(self, app_id, api_key):
        # see: https://www.knack.com/developer-documentation/#api-limits
        headers = {
            "X-Knack-Application-Id": app_id,
            "X-Knack-REST-API-KEY": api_key if api_key else "knack",
        }
        return headers

    def _url(self, route):
        subdomain = "loader" if "applications" in route else "api"
        return f"https://{subdomain}.knack.com/v1{route}"

    def request(self, method, route, **kwargs):
        url = self._url(route)
        req = requests.Request(method, url, headers=self.headers, **kwargs)
        prepped = req.prepare()
        res = self.session.send(prepped, timeout=self.timeout)
        res.raise_for_status()
        return res

    def _continue(self, total_records, current_records, record_limit):

        if total_records == None:
            return True

        elif current_records < record_limit and total_records > current_records:
            return True

        return False

    def _get_paginated_data(
        self, route, max_attempts=5, record_limit=None, filters=None
    ):
        # if you have more than 100 billion records, i'm sorry!
        record_limit = record_limit if record_limit else math.inf

        rows_per_page = (
            MAX_ROWS_PER_PAGE if record_limit >= MAX_ROWS_PER_PAGE else record_limit
        )

        filters = json.dumps(filters) if filters else None
        records = []
        total_records = None
        page = 1

        while self._continue(total_records, len(records), record_limit):
            attempts = 0
            params = {"page": page, "rows_per_page": rows_per_page, "filters": filters}

            while True:
                print("**********TRYING")
                try:
                    logging.debug(
                        f"Getting {rows_per_page} records from page {page} from {route}"
                    )
                    res = self.request("GET", route, params=params)

                    total_records = res.json()["total_records"]
                    break

                except requests.exceptions.Timeout as e:
                    warnings.warn(f"Request timeout. Trying again...")
                    if attempts < max_attempts:
                        attempts += 1
                        continue
                    else:
                        raise e

            records += res.json()["records"]

            page += 1

        # lazily shaving off any remainder to keep the client happy
        return records[0:record_limit] if record_limit < math.inf else records
