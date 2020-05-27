import logging

import requests

from knackpy.exceptions.exceptions import ValidationError


class KnackSession:
    """ A `Requests` wrapper with Knack helpers """
    def __repr__(self):
        info_str = ", ".join([f"{value} {key}" for key, value in self.info.items()])
        return f"""<KnackSession [id={self.app_id}]>"""

    def __init__(self, app_id, api_key, timeout=None):
        self.app_id = app_id
        self.headers = self._headers(app_id, api_key)
        self.session = self._session()
        self.timeout = timeout

    def _headers(self, app_id, api_key):
        # see: https://www.knack.com/developer-documentation/#api-limits
        headers = {
            "X-Knack-Application-Id": app_id,
            "X-Knack-REST-API-KEY": api_key if api_key else "knack",
        }
        return headers

    def _session(self):
        s = requests.Session()
        return s

    def _url(self, route):
        subdomain = "loader" if "applications" in route else "api"
        return f"https://{subdomain}.knack.com/v1{route}" 

    def request(self, method, route):
        url = self._url(route)
        req = requests.Request(method, url, headers=self.headers)
        prepped = req.prepare()        
        res = self.session.send(prepped, timeout=self.timeout)
        res.raise_for_status()
        return res

    def _paginated(self, route, max_attempts=5, page_limit=10, rows_per_page=1000):
        try:
            max_attempts, page_limit, rows_per_page = int(max_attempts), int(page_limit), int(rows_per_page)
        
        except ValueError as e:
            raise ValueError("Invalid parameter value(s) supplied to `max_attempts`, `page_limit` or `rows_per_page`")

        responses = []
        total_pages = None
        page = 1
        
        while page:
            params = {"page": page}
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                
                try:
                    logging.debug(f"Getting data from page {page} of {total_pages} from {route}")
                    res = self.request("GET", route)
                    break

                except requests.exceptions.Timeout as e:
                    if attempts < max_attempts:
                        continue
                    else:
                        raise e

            responses.append(res)

            if not total_pages:
                try:
                    total_pages = int(res.json()["total_pages"])

                except KeyError:
                    total_pages = 1

            if page_limit < total_pages:
                total_pages = page_limit

            if page >= total_pages:
                break

            else:
                page += 1

        return responses