import csv
import datetime
import logging
import os
import warnings
import typing

import requests
import pytz

from . import api, fields, utils
from . import record as knackpy_record
from .models import TIMEZONES, FIELD_SETTINGS


class App:
    """Knackpy is designed around the `App` class. It provides helpers for querying
    and manipulating Knack application data. You should use the `App` class
    because:

    - It allows you to query obejcts and views by key or name
    - It takes care of [localization issues](https://cityofaustin.github.io/knackpy/docs/user-guide#timestamps-and-localization)  # noqa:E501
    - It let's you download and upload files from your app.
    - It does other things, too.

    Args:
        app_id (str): Knack [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id)  # noqa:E501
            string.
        api_key (str, optional, default=`None`): [Knack API key](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).
        metadata (dict, optional): The Knack app's metadata as a `dict`. If `None`
            it will be fetched on init. You can find your apps metadata
            [here](https://loader.knack.com/v1/applications/5d79512148c4af00106d1507).
        tzinfo (`pytz.Timezone`, optional): [description].  A
            [pytz.Timezone](https://pythonhosted.org/pytz/) object. When `None`, is set
            automatically based on the app's `metadadata`.
        max_attempts (int): The maximum number of attempts to make if a request times
            out. Default values that are set in `knackpy.api.request`.
        timeout (int, optional): Number of seconds to wait before a Knack API request
            times out. Further reading:
            [Requests docs](https://requests.readthedocs.io/en/master/user/quickstart/).
    """

    def __repr__(self):
        return f"""<App [{self.metadata["name"]}]>"""

    def __init__(
        self,
        *,
        app_id: str,
        api_key: str = None,
        slug: str = None,
        metadata: str = None,
        tzinfo: datetime.tzinfo = None,
        max_attempts: int = 5,
        timeout: int = 30,
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
            api.get_metadata(app_id=self.app_id, timeout=self.timeout, slug=slug)[
                "application"
            ]
            if not metadata
            else metadata["application"]
        )
        self.slug = self.metadata["account"]["slug"]
        self.tzinfo = tzinfo if tzinfo else self.metadata["settings"]["timezone"]
        self.timezone = self._get_timezone(self.tzinfo)
        self.field_defs = fields.field_defs_from_metadata(self.metadata)
        self.containers = utils.generate_containers(self.metadata)
        self.data = {}
        self.records = {}
        logging.debug(self)

    def _get_metadata(self):
        return api.get_metadata(app_id=self.app_id, timeout=self.timeout)

    def info(self):
        """Returns a `dict` of basic app information:
            - Number of objects
            - Number of scenes
            - Number of records
            - Number total file size
        """
        total_obj = len(self.metadata.get("objects"))
        total_scenes = len(self.metadata.get("scenes"))
        total_records = self.metadata.get("counts").get("total_entries")
        total_size = utils.humanize_bytes(self.metadata.get("counts").get("asset_size"))

        return {
            "objects": total_obj,
            "scenes": total_scenes,
            "records": total_records,
            "size": total_size,
        }

    @staticmethod
    def _get_timezone(tzinfo: str):
        # TODO: move to utils
        """Create a pytz.Timezone instance from a timezone string.

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

        See also, note in knackpy.fields.real_unix_timestamp_mills() about why
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

        raise ValueError(
            """
                Unknown timezone supplied. `tzinfo` should formatted as a
                timezone string compliant to the IANA timezone database. See:
                https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
            """
        )

    def _find_container(self, identifier: str):
        matches = [
            container
            for container in self.containers
            if identifier in [container.obj, container.view, container.name]
        ]

        if len(matches) > 1:
            raise ValueError(
                f"Multiple containers use name {identifier}. Try using a view or object key."  # noqa
            )

        try:
            return matches[0]
        except IndexError:
            raise IndexError(
                f"Unknown container specified: {identifier}. Inspect App.containers for available containers."  # noqa
            )

    def get(
        self,
        identifier: str = None,
        refresh: bool = False,
        record_limit: int = None,
        filters: typing.Union[dict, list] = None,
        generate=False,
    ):
        """Get records from a knack object or view.

            Note that we accept the request params `record_limit` and `filters` here
            because the user would presumably want to set these on a per-object/view
            basis. They are not stored in state. Whereas `max_attempts` and
            `timeout` are set on App construction and persist in `App` state.

            Args:
                identifier (str, optional*): an object or view key or name string that
                    exists in the app. If None is provided and only one container has
                    been fetched, will return records from that container.
                refresh (bool, optional): Force the re-querying of data from Knack
                    API. Defaults to False.
                record_limit (int): the maximum number of records to retrieve. If
                    `None`, will return all records.
                filters (dict or list, optional): A dict or of Knack API filiters.
                    See: https://www.knack.com/developer-documentation/#filters.
                generate (bool, optional): If True, will return a generator which
                    yields knacky.Record objects instead of return a list of of them.

            Returns:
                A `generator` which yields knackpy Record objects.
        """
        if not identifier and len(self.data) == 1:
            identifier = list(self.data.keys())[0]
        elif not identifier:
            raise TypeError("Missing 1 required argument: identifier")

        container = self._find_container(identifier)

        # note that data is always assigned to an object or view key, regardless of
        # whether or not the client provides an object or view *name*
        container_key = container.obj or container.view

        if self.records.get(container_key) and not refresh:
            # if the data has already been retrieved we do not fetch it again or convert
            # the data into knackpy.record.Record's again, unless refresh.
            return self.records[container_key]

        if not self.data.get(container_key) or refresh:
            # to support side-loading of data, we may have a situation where data is
            # present, but records have not never been generated
            self.data[container_key] = api.get(
                app_id=self.app_id,
                api_key=self.api_key,
                obj=container.obj,
                scene=container.scene,
                view=container.view,
                filters=filters,
                slug=self.slug,
                max_attempts=self.max_attempts,
                timeout=self.timeout,
                record_limit=record_limit,
            )

        self.records[container_key] = self._records(container_key, generate)
        return self.records[container_key]

    def _records(self, container_key, generate=False):
        """Return a list or generator of knackpy.record.Record objects.

        Args:
            container_key (str): An Knack object or view key.
            generate (bool, optional): If true, will return a Record generator function
                instead of a list of Record's.

        Returns:
            list or generator: A list or generator of knackpy.record.Record's.
        """
        data = self.data[container_key]

        # filter field defs by requested container
        field_defs = [
            field_def
            for field_def in self.field_defs
            if container_key == field_def.obj or container_key in field_def.views
        ]

        try:
            identifier = [
                field_def.key for field_def in field_defs if field_def.identifier
            ][0]
        except IndexError:
            identifier = None

        if generate:
            return self._generate_records(data, field_defs, identifier)

        return [
            knackpy_record.Record(record, field_defs, identifier, self.timezone)
            for record in data
        ]

    def _generate_records(self, data, field_defs, identifier):
        for record in data:
            yield knackpy_record.Record(record, field_defs, identifier, self.timezone)

    def _find_field_def(self, identifier, obj):
        return [
            field_def
            for field_def in self.field_defs
            if identifier.lower() in [field_def.name.lower(), field_def.key]
            and field_def.obj == obj
        ]

    def _unpack_subfields(self, records: list) -> list:
        """Unpack subfields and for select field types so that they can be handled as
        individual columns in CSV. See `models.py` for subfield definitions.

        Also formats field data according each field's formatter. Note that any
        field with subfields does not any formatting applied. It's simply unpacked.

        Receives a list of `Record` objects and returns a list of dicts."""
        records_formatted = []

        for record in records:
            record_formatted = {}
            for field in record.values():
                try:
                    subfields = FIELD_SETTINGS[field.field_def.type]["subfields"]
                except KeyError:
                    subfields = None

                if subfields:
                    try:
                        field_dict = {
                            f"{field.name}_{subfield}": field.raw.get(subfield)
                            for subfield in subfields
                        }
                    except AttributeError:
                        # assume field.raw is None. we still want to assign None to
                        # each subfield, so that each record has the same cols
                        field_dict = {
                            f"{field.name}_{subfield}": None for subfield in subfields
                        }
                else:
                    field_dict = {field.name: field.formatted}
                record_formatted.update(field_dict)
            records_formatted.append(record_formatted)
        return records_formatted

    def to_csv(
        self,
        identifier: str,
        *,
        out_dir: str = "_csv",
        delimiter=",",
        record_limit: int = None,
        filters: typing.Union[dict, list] = None,
    ) -> None:
        """Write formatted Knack records to CSV.

        Args:
            identifier (str): an object or view key or name string that exists in the
                app.
            out_dir (str, optional): Relative path to the directory to which files
                will be written. Defaults to "_csv".
            delimiter (str, optional): [description]. Defaults to ",".
            record_limit (int): the maximum number of records to retrieve. If
                `None`, will return all records.
            filters (dict or list, optional): A dict or of Knack API filiters.
                See: https://www.knack.com/developer-documentation/#filters.
        """
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        records = self.get(identifier, record_limit=record_limit, filters=filters)

        csv_data = self._unpack_subfields(records)

        fieldnames = csv_data[0].keys()

        fname = os.path.join(out_dir, f"{identifier}.csv")

        with open(fname, "w") as fout:
            writer = csv.DictWriter(fout, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(csv_data)

    def _assemble_downloads(
        self, identifier: str, field_key: str, label_keys: list, out_dir: str
    ):
        """Extract file download paths and custom filenames/output paths.

        Args:
            identifier (str): The name or key of the object from which files will be
                downloaded.
           field_key (str): The knack field key to be downloaded (must be a "file" or
            "image" field type)
            label_keys (list, optional): A list of field keys whose *values* will be
                prepended to the attachment filename, separated by an underscore.
            out_dir (str, optional): Relative path to the directory to which files
                will be written. Defaults to "_downloads".

        Returns:
            list: A list of dictionaries with file properties that will be passed to
                the HTTP request. Dict's look like this:
            {
                "id": "5d7967132be2bb0010892ce7",
                "application_id": "abc123xzy456",
                "s3": true,
                "type": "file",
                "filename": "_data/my_file.pdf",
                "url": "https://api.knack.com/v1/applications/abc123xzy456/download/asset/5d7967132be2bb0010892ce7/my_file.pdf",   # noqa:E501
                "thumb_url": "",
                "size": 305741,
                "field_key": "field_17"
            }
        """
        downloads = []

        field_key_raw = f"{field_key}_raw"

        downloads = []

        for record in self.get(identifier):
            file_dict = record.raw.get(field_key_raw)

            if not file_dict:
                continue

            filename = file_dict["filename"]

            if label_keys:
                # reverse traverse to ensure that field labels are prepended in
                # sequence provided.
                for field in reversed(label_keys):
                    filename = f"{record.raw.get(field)}_{filename}"

            file_dict["filename"] = os.path.join(out_dir, filename)

            downloads.append(file_dict)

        return downloads

    def _download_files(self, downloads: list):
        """Download files from Knack and write them locally.

        Args:
            downloads (list): A list of dictionaries with file properties that will be
            passed to the HTTP request. Dict's look like this:

            {
                "id": "5d7967132be2bb0010892ce7",
                "application_id": "abc123xzy456",
                "s3": true,
                "type": "file",
                "filename": "_data/my_file.pdf",
                "url": "https://api.knack.com/v1/applications/abc123xzy456/download/asset/5d7967132be2bb0010892ce7/my_file.pdf",  # noqa:E501
                "thumb_url": "",
                "size": 305741,
                "field_key": "field_17"
            }

        Returns:
            int: A count of the number of files downloaded.

        """
        count = 0

        for file_info in downloads:
            filename = file_info["filename"]
            filesize = utils.humanize_bytes(file_info["size"])
            logging.debug(f"\nDownloading {file_info['url']} - size: {filesize}")

            res = requests.get(file_info["url"], allow_redirects=True)

            res.raise_for_status()

            with open(filename, "wb") as fout:
                fout.write(res.content)
                count += 1

        return count

    def download(
        self,
        *,
        container: str,
        field: str,
        out_dir: str = "_downloads",
        label_keys: list = None,
    ):
        """Download files and images from Knack records.

        Args:
            container (str): The name or key of the object from which files will be
                downloaded.
            out_dir (str, optional): Relative path to the directory to which files
                will be written. Defaults to "_downloads".
            field (str): The Knack field key of the file or image field to be
                downloaded.
            label_keys (list, optional): A list of field keys whose *values* will be
                prepended to the attachment filename, separated by an underscore.

        Returns:
            [int]: Count of files downloaded.
        """
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        download_container = self._find_container(container)

        field_defs = self._find_field_def(field, container)

        if not field_defs:
            raise ValueError(f"Field not found: '{field}'")

        downloads = self._assemble_downloads(
            download_container.obj, field_defs[0].key, label_keys, out_dir
        )

        download_count = self._download_files(downloads)

        logging.debug(f"{download_count} files downloaded.")

        return download_count

    def _replace_record(self, record, obj):
        for rec in self.data[obj]:
            if rec["id"] == record["id"]:
                rec = record
                return self.data[obj]

    def _update_record_state(self, res, obj, method, record_id=None):
        """ Keep local data and records in sync with CRUD operations.

        Args:
            res (dict): Knack API response. Either a record `dict` or `{"delete": True}`
            obj (str): The Knack object key that was updated.
            method (str): `create`, `update`, or `delete`.
            record_id (str): The Knack record ID of the affected record, if applicable.

        Side-Effects:
            Update `self.data[key]` accordingly; regenerate `self.records[key]`.

        Returns:
            None
        """
        if method == "create":
            self.data[obj].append(res)

        elif method == "update":
            self.data[obj] = self._replace_record(res, obj)

        elif method == "delete":
            # the Knack API responds with {"delete": True} when deleting records so we
            # need to have the record_id of the deleted record explicitly here (ie
            # there is no `record` response to work with)
            self.data[obj] = [
                record for record in self.data[obj] if record["id"] != record_id
            ]

        self.records[obj] = self._records(obj)
        return None

    def record(
        self, *, data: dict, method: str, obj: str,
    ):
        """Create, update, or delete a Knack record.

        Args:
            data (dict): The Knack record data payload.
            method (str): Choose from `create`, `update`, or `delete`.
            obj (str, optional): The Knack object key or name which holds the record
                data.

        Returns:
            dict: The updated or newly created Knack record data, or, if deleting a
                record: `{"delete": true}`
        """

        # if the client provides a view identifier, it will raise no error until the
        # Knack API raises an HTTPError
        container = self._find_container(obj)

        res = api.record(
            app_id=self.app_id,
            api_key=self.api_key,
            data=data,
            method=method,
            obj=container.obj,
            slug=self.slug,
            max_attempts=self.max_attempts,
            timeout=self.timeout,
        )

        if self.data.get(obj):
            # if data for the affected obj is stored locally, update it accordingly.
            self._update_record_state(res, obj, method, record_id=data.get("id"))
        return res

    def upload(
        self,
        *,
        container: str,
        field: str,
        path: str,
        asset_type: str,
        record_id: str = None,
    ):
        """Upload a file or image to Knack. This is a two-step process:

        1) Upload file asset to Knack storage
        2) Create/update a record that links to the file in storage

        Knack docs: https://www.knack.com/developer-documentation/#file-image-uploads

        Args:
            container (str): The name or key of the object from which files will be
                downloaded.
            field (str): The knack field key of the field you're uploading into.
            path (str): The path to the file to be uploaded.
            asset_type (str): The type of Knack field you're uploading to. Must be
                `file` or `image`.
            record_id (str, optional): The knack record ID to which the upload will be
                attached. If `None`, will create a new record. Otherwise will update an
                existing record.
        """
        download_container = self._find_container(container)

        return api.upload(
            app_id=self.app_id,
            api_key=self.api_key,
            obj=download_container.obj,
            field=field,
            path=path,
            asset_type=asset_type,
            record_id=record_id,
            slug=self.slug,
            max_attempts=self.max_attempts,
            timeout=self.timeout,
        )
