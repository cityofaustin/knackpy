import collections
import logging
import warnings
import pytz

from knackpy import api
from knackpy import _records
from knackpy import _fields
from knackpy._knack_session import KnackSession
from knackpy.utils import utils
from knackpy.utils.timezones import TIMEZONES
from knackpy.exceptions.exceptions import ValidationError


class App:
    """
    Knack application wrapper. This thing does it all, folks!
    """

    def __repr__(self):
        return f"""<App [{self.metadata["name"]}]>"""

    def __init__(self, app_id, metadata=None, api_key=None, timeout=30, tzinfo=None):

        if not api_key:
            warnings.warn(
                "No API key has been supplied. Only public views will be accessible."
            )

        self.app_id = app_id
        self.api_key = api_key
        """
        we accept timeout as an init kwarg because the client may want to set timeout for
        getting metadata, which is a side-effect of initialization. This timeout can be
        overridden by the `get` method.
        """
        self.session = KnackSession(self.app_id, api_key=self.api_key, timeout=timeout)
        self.metadata = self._get_metadata() if not metadata else metadata
        self.tzinfo = tzinfo if tzinfo else self.metadata["settings"]["timezone"]
        self.timezone = self.get_timezone(self.tzinfo)
        field_defs = _fields.generate_field_defs(self.metadata)
        self.field_defs = _fields.set_field_def_views(field_defs, self.metadata)
        self.containers = utils.generate_containers(self.metadata)
        self.data = {}
        logging.debug(self)

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

    def _get_metadata(self, route=f"/applications"):
        route = f"{route}/{self.app_id}"
        # todo: use API instead?
        res = self.session.request("get", route)
        return res.json()["application"]

    @staticmethod
    def get_timezone(tzinfo):
        # TODO: move to utils
        """
        Knack stores timezone information in the app metadata, but it does not use IANA
        timezone database names. Instead it uses common names e.g.,
        "Eastern Time (US & Canada)" instead of "US/Eastern".

        I'm sure these common names are standardized somewhere, and I did not bother to
        munge the IANA timezone DB to figure it out, so I created the `TIMZONES` index in
        `knackpy.utils.timezones` by copying a table from the internets.
        
        As such, we can't be certain our index contains all of the timezone names that knack
        uses in its metadata. So, this method will attempt to lookup the Knack metadata
        timezone in our TIMEZONES index, and raise an error of it fails.

        Alternatively, the client can override the Knack timezone common name by including
        an IANA-compliant timezone name (e.g., "US/Central")by passing the `tzinfo` kwarg
        when constructing the `App` innstance, or directly to this method.

        See also, note in knackpy._fields.real_unix_timestamp_mills() about why we
        need valid timezone info to handle Knack records.

        Inputs:
        - tzinfo (str): either an IANA-compliant timezone name, or the common timezone name
        available in metadata.settings.timezone

        Returns (hopefully):
            - a `pytz.timezone` instance
        """

        try:
            # first let pytz try to handle the tzinfo
            return pytz.timezone(tzinfo)
        except:
            pass

        try:
            # perhaps the tzinfo matches a known timezone common name
            matches = [
                tz["iana_name"]
                for tz in TIMEZONES
                if tz["common_name"].lower() == tzinfo.lower()
            ]
            return pytz.timezone(matches[0])

        except (pytz.exceptions.UnknownTimeZoneError, IndexError) as e:
            pass

        raise ValidationError(
            """
                Unknown timezone supplied. `tzinfo` should formatted as a timezone string
                compliant to the IANA timezone database.
                See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
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
                f"Multiple containers use name {client_key}. Try using a view or object key."
            )

        try:
            return matches[0]
        except IndexError:
            raise ValidationError(
                f"Unknown container specified: {client_key}. Inspect App.containers for available containers."
            )

    def get(self, client_key, refresh=False, **kwargs):
        """Get records from a knack object or view. Supported kwargs are record_limit
            (type: int), max_attempts (type: int), and filters (type: dict).

            Args:
                client_key (str): an object or view key or name string that
                    exists in the app
                refresh (bool, optional): [description]. Defaults
                    to False.

            Returns: [generator]: record generator
        """
        container = self._find_container(client_key)

        container_key = container.obj or container.view

        route = api._route(
            obj=container.obj, scene=container.scene, view=container.view
        )

        if not self.data.get(container_key) or refresh:
            # fetch data if it has not already been collected, or force via `refresh=True`
            self.data[container_key] = self.session._get_paginated_data(route, **kwargs)

        return self._generate_records(container_key, self.data[container_key])

    def _generate_records(self, container_key, data):
        return _records.Records(
            container_key, data, self.field_defs, self.timezone
        ).records()
