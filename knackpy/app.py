import datetime
import logging
import warnings
import typing

import requests
import pytz

import knackpy
from knackpy import _records
from knackpy import _fields
from knackpy.utils import utils
from knackpy.utils.timezones import TIMEZONES
from knackpy.exceptions.exceptions import ValidationError


class App:
    """Knack application wrapper. This thing does it all, folks!

    Note that requet params `timeout` and `max_attempts` are defined here at 
    construction, while `record_limit` and `filters` are defined in `App.records()`.
    The thinking being that the user will want to specifiy these params differently
    based on the container being queried.

        Args:
            app_id (str): Knack application ID string.
            metadata (str, optional): [description]. Defaults to None.
            api_key (str, optional): [description]. Defaults to None.
            tzinfo (pytz.Timezone, optional): [description]. Defaults to None.
            max_attempts (int): the maximum number of attempts to make if a request
                times out. Default values that are set in `knackpy.api.request`.
            timeout (int, optional): Number of seconds to wait before a Knack API
                request times out. Default values that are set in
                `knackpy.api.request`.
        """

    def __repr__(self):
        return f"""<App [{self.metadata["name"]}]>"""

    def __init__(
        self,
        *,
        app_id: str,
        api_key: str = None,
        metadata: str = None,
        tzinfo: datetime.tzinfo = None,
        max_attempts: int = None,
        timeout: int = None,
    ):

        if not api_key:
            warnings.warn(
                "No API key has been supplied. Only public views will be accessible."
            )

        self.app_id = app_id
        self.api_key = api_key
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.metadata = (
            self._get_metadata()["application"]
            if not metadata
            else metadata["application"]
        )
        self.tzinfo = tzinfo if tzinfo else self.metadata["settings"]["timezone"]
        self.timezone = self.get_timezone(self.tzinfo)
        field_defs = _fields.generate_field_defs(self.metadata)
        self.field_defs = _fields.set_field_def_views(field_defs, self.metadata)
        self.containers = utils.generate_containers(self.metadata)
        self.data = {}
        logging.debug(self)

    def _get_metadata(self):
        return knackpy.api.get_metadata(app_id=self.app_id, timeout=self.timeout)

    def info(self):
        total_obj = len(self.metadata.get("objects"))
        total_scenes = len(self.metadata.get("scenes"))
        total_records = self.metadata.get("counts").get("total_entries")
        total_size = utils._humanize_bytes(
            self.metadata.get("counts").get("asset_size")
        )

        return {
            "objects": total_obj,
            "scenes": total_scenes,
            "records": total_records,
            "size": total_size,
        }

    @staticmethod
    def get_timezone(tzinfo):
        # TODO: move to utils
        """
        Knack stores timezone information in the app metadata, but it does not
        use IANA timezone database names. Instead it uses common names e.g.,
        "Eastern Time (US & Canada)" instead of "US/Eastern".

        I'm sure these common names are standardized somewhere, and I did not
        bother to munge the IANA timezone DB to figure it out, so I created the
        `TIMZONES` index in `knackpy.utils.timezones` by copying a table from
        the internets.

        As such, we can't be certain our index contains all of the timezone
        names that knack uses in its metadata. So, this method will attempt to
        lookup the Knack metadata timezone in our TIMEZONES index, and raise an
        error of it fails.

        Alternatively, the client can override the Knack timezone common name by
        including an IANA-compliant timezone name (e.g., "US/Central")by passing
        the `tzinfo` kwarg when constructing the `App` innstance, or directly to
        this method.

        See also, note in knackpy._fields.real_unix_timestamp_mills() about why
        we need valid timezone info to handle Knack records.

        Inputs:
        - tzinfo (str): either an IANA-compliant timezone name, or the common
          timezone name available in metadata.settings.timezone

        Returns (hopefully): - a `pytz.timezone` instance
        """

        try:
            # first let pytz try to handle the tzinfo
            return pytz.timezone(tzinfo)
        except pytz.exceptions.UnknownTimeZoneError:
            pass

        try:
            # perhaps the tzinfo matches a known timezone common name
            matches = [
                tz["iana_name"]
                for tz in TIMEZONES
                if tz["common_name"].lower() == tzinfo.lower()
            ]
            return pytz.timezone(matches[0])

        except (pytz.exceptions.UnknownTimeZoneError, IndexError):
            pass

        raise ValidationError(
            """
                Unknown timezone supplied. `tzinfo` should formatted as a
                timezone string compliant to the IANA timezone database. See:
                https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
            """
        )

    def _find_container(self, client_key):

        matches = [
            container
            for container in self.containers
            if client_key in [container.obj, container.view, container.name]
        ]

        if len(matches) > 1:
            raise ValidationError(
                f"Multiple containers use name {client_key}. Try using a view or object key."  # noqa
            )

        try:
            return matches[0]
        except IndexError:
            raise ValidationError(
                f"Unknown container specified: {client_key}. Inspect App.containers for available containers."  # noqa
            )

    def _build_request_kwargs(
        self, max_attempts: int, timeout: int, record_limit: int
    ) -> dict:
        """
        Compile the keyword arguments to be passed to `knackpy.api`. We drop params
        that are NoneType because we don't want to override the default values for
        these params that are define in the api methods.

        TODO: a more pythonic approach would be...?
        """
        request_kwargs = {}
        if record_limit:
            request_kwargs["record_limit"] = record_limit
        if max_attempts:
            request_kwargs["max_attempts"] = max_attempts
        if timeout:
            request_kwargs["timeout"] = timeout

        return request_kwargs

    def records(
        self,
        client_key: str,
        refresh: bool = False,
        record_limit: int = None,
        filters: typing.Union[dict, list] = None,
    ):
        """Get records from a knack object or view. Supported kwargs are record_limit
            (type: int), max_attempts (type: int), and filters (type: dict).

            Note that we accept the request params `record_limit` and `filters` here
            because the user would presumably want to set these on a per-object/view
            basis. They are not stored in state. Whereas `max_attempts` and
            `timtout` are set on App construction and persist in `App` state.

            Args:
                client_key (str): an object or view key or name string that
                    exists in the app.
                refresh (bool, optional): Force the re-querying of data from Knack
                    API. Defaults to False.
                record_limit (int): the maximum number of records to retrieve.
                    Default value is set in `knackpy.api.request`.
                filters (dict or list, optional): A dict or of Knack API filiters.
                    See: https://www.knack.com/developer-documentation/#filters.
                
            Returns:
                [generator]: A generator which yields Knack record data.
        """
        container = self._find_container(client_key)

        container_key = container.obj or container.view

        route = knackpy.api._record_route(
            obj=container.obj, scene=container.scene, view=container.view
        )

        if not self.data.get(container_key) or refresh:
            request_kwargs = self._build_request_kwargs(
                self.max_attempts, self.timeout, record_limit
            )

            self.data[container_key] = knackpy.api.get(
                app_id=self.app_id,
                api_key=self.api_key,
                obj=container.obj,
                scene=container.scene,
                view=container.scene,
                filters=filters,
                **request_kwargs,
            )

        return self._generate_records(container_key, self.data[container_key])

    def _generate_records(self, container_key, data):
        return _records.Records(
            container_key, data, self.field_defs, self.timezone
        ).records()
