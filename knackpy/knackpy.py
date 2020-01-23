from copy import deepcopy
import csv
from datetime import datetime
import json
import logging
import os
import pdb
from urllib.parse import urlparse

import pytz
import requests


class Knack(object):
    def __init__(
        self,
        api_key=None,
        app_id=None,
        filters=None,
        include_ids=True,
        id_key="id",
        max_attempts=5,
        obj=None,
        page_limit=1000,
        raw_connections=False,
        rows_per_page=1000,
        ref_obj=None,
        scene=None,
        timeout=10,
        tzinfo="US/Central",
        view=None,
    ):
        """  
        Class to interact with Knack application records via the API as
        documented at https://www.knack.com/developer-documentation/
        
        Parameters
        ----------
        app_id : string (required)
            Knack application ID string
        api_key : string (optional)
            Knack application key. Required for accessing private views.
        filters : dict (optional)
            Search and limit the records returned by object query. Ignored for
            view-based requests. Does not currently support range queries.
            Filters dict must be formatted as described in API docs:
            See: https://www.knack.com/developer-documentation/#filters
        timeout : numeric (optional | default : 10)
            Number of seconds before http request timeout
        max_attempts : number (optional | default : 5)
            The maximum number times knackpy will attempt to send a request,
            in the event of timeout.
        obj : string (required if scene + view are not specified)
            A Knack object idenfiter in format "object_xx". If specified, the
            instance will retrieve data from an object endpoint.
        scene : string (required with view if obj not specified)
            A Knack scene identifier in format "scene_xx"
        view : string (required with scene if obj not specified)
            A Knack view identifier in format "view_xx"
        ref_obj : list (optional)
            An array of Knack object identifiers which specify the Knck objects
            that are referenced by a Knack view. Required to retrieve
            field metadata for view-based requests.
        include_ids : bool (optional | default : True)
            When true, Knack record IDs will be included in the parsed data.
        id_key : string (optional | default : 'id')
            The name that should be assigned to the the Knack record ID field.
            Make sure this field name does not match any existing
            field names in your application.
        tzinfo : string (optional | default : 'US/Central')
            This value should match the timezone setting of your Knack
            application, formatted as a timezone string compliant to the tz database
            (https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
            When specified, datetime fields will be localized
            accordingly.
        raw_connections : bool (option | default : False)
            When true, connection fields will be parsed as "raw" connection fields,
            i.e., the connection field will be assigned
            an array of Knack record of format:
                {'id': 'abc_record_id', 'identifier': 'record identifier'}
            will be returned. When false, connection fields are (if one
            connection) returned as the field's display name, or (if many
            connetions) an array of the connection field's display name
        rows_per_page : int (optional | default: 1000)
            The number of rows to return per page requested. The maximum
            supported amount is 1000.
        page_limit : int (optional | default: 10)
            The maximum number of pages to request when retrieving data from
             an object or view.  
        """
        self.obj = obj
        self.scene = scene
        self.view = view
        self.ref_obj = ref_obj
        self.filters = filters
        self.app_id = app_id
        self.api_key = api_key
        self.timeout = float(timeout)
        self.max_attempts = max_attempts
        self.include_ids = include_ids
        self.id_key = id_key
        self.tzinfo = tzinfo
        self.raw_connections = raw_connections
        self.rows_per_page = rows_per_page
        self.page_limit = page_limit
        self.fields = None
        self.fieldnames = None
        self.field_map = None
        self.endpoint = None
        self.data_raw = None
        self.data = None

        if not app_id:
            raise Exception("app_id is required.")

        if not (self.view and self.scene) and not self.obj:
            raise Exception(
                """
                Records instance must specify an object or a view/scene
                """
            )

        if self.obj and (self.view or self.scene):
            raise Exception(
                """'
                Records instance must specify an object or view/scene,
                but not both.
                """
            )

        if self.rows_per_page > 1000:
            print("Warning: maximum rows per page is 1000. Only 1000 rows per page will be returned.")

        self.endpoint = self._get_endpoint()
        self.data_raw = self._get_data(self.endpoint, "records", self.filters)

        if not self.data_raw:
            logging.warning("No data found at {}".format(self.endpoint))

        if self.view and self.scene and self.ref_obj and self.api_key:
            self._get_fields(self.ref_obj)
            self._process_fields()  #  assign self.fields and self.fieldnames
            self._make_field_map()

        elif self.view and self.scene and not self.api_key:
            self._extract_fields()  #  assign self.fieldnames
            self.data = self.data_raw

        elif self.obj:
            self._get_fields([self.obj])
            self._process_fields()  #  assign self.fields and self.fieldnames
            self._make_field_map()

        if self.data_raw and self.fields:
            self.data = self._parse_data()

    def _get_data(self, endpoint, record_type, filters=None):
        """
        Get data from Knack view or object.

        Parameters
        ----------
        endpoint : string (required)
            URL of the api endpoint from which data will be retrieved
        record_type : string (required)
            Identifies the type of records to be retrieved from the Knack API.
            Must be specified as either 'fields' or 'records'.
        filters :
            A filter dict that should be included in the request. Only
            applicable for object-based record requests.

        Returns
        -------
        data (list or dict)
            If record_type is 'fields', a dictionary of field metatdata.
            If record type is 'records', a list of dictionaries of database
            records.
        """
        print("Get data from {}".format(endpoint))

        headers = {
            "x-knack-application-id": self.app_id,
            "x-knack-rest-api-key": self.api_key,
        }

        if not self.api_key:
            #  'knack' must be used as api key for public views
            headers["x-knack-rest-api-key"] = "knack"

        current_page = 1
        data = []

        while current_page:

            params = {"page": current_page}

            if filters:
                params["filters"] = json.dumps(filters)

            #  logic to retry request on timeout
            attempts = 0
            while attempts < self.max_attempts:

                attempts += 1

                try:
                    req = requests.get(
                        endpoint, headers=headers, params=params, timeout=self.timeout
                    )

                    break

                except requests.exceptions.Timeout as e:
                    #  handle error unless max tries
                    if attempts < self.max_attempts:
                        logging.info("Request timeout. Trying again...")
                        continue
                    else:
                        raise e

            if req.status_code == 200:
                data = data + req.json()[record_type]
            else:
                raise Exception(req.text)

            try:
                total_pages = req.json()["total_pages"]
            except KeyError:
                total_pages = 1

            if self.page_limit < total_pages:
                total_pages = self.page_limit

            if current_page >= total_pages:
                current_page = None
            else:
                current_page = current_page + 1

        print("Retrieved {} {}".format(len(data), record_type))

        return data

    def _get_fields(self, objects):
        """
        Get field data from Knack objects
        
        Returns self.fields : A list of field metadata where each entry
        is a field

        """
        fields = []

        for obj in objects:
            print("Get field data for {}".format(obj))

            fields_endpoint = "https://api.knack.com/v1/objects/{}/fields?rows_per_page={}".format(
                obj, self.rows_per_page
            )

            field_data = self._get_data(fields_endpoint, "fields")

            fields = fields + field_data

        self.fields = fields
        return self.fields

    def _extract_fields(self):
        """
        Extract field names from list of knack records.
        Useful if field metadata is unavilable.
        """
        keys = [key for row in self.data_raw for key in row]
        self.fieldnames = list(set(keys))
        return self.fieldnames

    def _process_fields(self):

        if self.include_ids:
            #  create an 'id' field
            self.fields.append({"key": "id", "label": self.id_key, "type": "id"})

        field_dict = {}
        for field in self.fields:
            field_dict[field["key"]] = field

        self.fields = field_dict

        return self.fields

    def _make_field_map(self):
        """
        return a dict of format field_label : field_name
        """
        self.field_map = {self.fields[field]["label"]: field for field in self.fields}
        return self.field_map

    def _parse_data(self):
        """
        Replace Knack field names with field labels and extract
        subfields.

        Returns self.data (list of record dictionaries)
        """

        parsed_data = []

        #  unique fieldnames that *actually appear in the data* are collected here
        fieldnames = []

        count = 0

        for record in self.data_raw:
            count += 1
            new_record = {}  #  parsed record goes here

            for field in self.fields.keys():

                if field in record:
                    field_label = self.fields[field]["label"]

                else:
                    continue

                if "{}_raw".format(field) in record:
                    """
                    Check if 'raw' field exists. If raw field exists,
                    data will be extracted from raw field based on field type.
                    Raw fields are not available when fields are empty or
                    calculated (and possibly some other cases)
                    """
                    field_type = self.fields[field]["type"]
                    field = "{}_raw".format(field)

                    if field_type == "address":
                        #  extract subfields
                        for subfield in [
                            "latitude",
                            "longitude",
                            "formatted_value",
                            "street",
                            "street2",
                            "city",
                            "state",
                            "country",
                            "zip",
                        ]:
                            if subfield in record[field]:
                                #  generate label for subfield
                                subfield_label = "{}_{}".format(field_label, subfield)
                                #  assign subfield value if field exists
                                new_record[subfield_label] = record[field][subfield]
                                fieldnames.append(subfield_label)

                    elif field_type == "name":
                        #  extract subfields
                        for subfield in ["title", "first", "middle", "last"]:
                            if subfield in record[field]:
                                #  generate label for subfield
                                subfield_label = "{}_{}".format(field_label, subfield)
                                #  assign subfield value if field exists
                                new_record[subfield_label] = record[field][subfield]
                                fieldnames.append(subfield_label)

                    elif field_type == "email":
                        #  extract subfields
                        for subfield in ["email", "label"]:
                            if subfield in record[field]:
                                #  generate label for subfield
                                subfield_label = "{}_{}".format(field_label, subfield)
                                #  assign subfield value if field exists
                                new_record[subfield_label] = record[field][subfield]
                                fieldnames.append(subfield_label)

                    elif field_type == "multiple_choice":

                        fieldnames.append(field_label)

                        field_val = self._stringify_ambiguous_field(record[field])
                        new_record[field_label] = field_val

                    elif field_type == "link":
                        #  extract subfields
                        for subfield in ["url", "label"]:

                            if subfield in record[field]:
                                #  generate label for subfield
                                subfield_label = "{}_{}".format(field_label, subfield)
                                #  assign subfield value if field exists
                                new_record[subfield_label] = record[field][subfield]
                                fieldnames.append(subfield_label)

                    elif field_type in ["date", "date_time"]:

                        fieldnames.append(field_label)
                        #  get unix timestamps from datetime fields
                        #  ignore other subfields
                        if record[field]:
                            #  this "unix" timestamp has milliseconds
                            d = int(record[field]["unix_timestamp"])

                            if self.tzinfo:
                                # Knack timetstamps are "local" timestamps.
                                # I.e., millesconds elapsed since epoch **in local time**.
                                # So we convert them to actual unlocalized timestamps
                                tz = pytz.timezone(self.tzinfo)

                                # create a naive datetime object from the timestamp
                                dt_utc = datetime.utcfromtimestamp(d / 1000)

                                # localize the datetime object
                                dt_local = tz.localize(dt_utc)

                                # convert to unix timestamp + mills
                                d = int(dt_local.timestamp() * 1000)

                        else:
                            d = ""

                        new_record[field_label] = d

                    elif field_type == "connection":
                        fieldnames.append(field_label)

                        if self.raw_connections:
                            #  assign entire connection dict to field
                            new_record[field_label] = record[field]

                        elif record[field]:
                            #  assign only connection identifier
                            #  (aka display field) to label
                            new_record[field_label] = record[field][0]["identifier"]
                        else:
                            #  connection is empty
                            new_record[field_label] = ""

                    elif field_type == "file" or field_type == "image":
                        fieldnames.append(field_label)
                        
                        if record[field]:
                            """
                            Image fields come in two flavors: direct upload or reference
                            URL. When images are uploaded directly to a field, they are
                            comprised of a dict with "url" key of the image's endpoint.
                            When the image field is configured with a reference URL,
                            the field value is simply a string.
                            """
                            try:
                                new_record[field_label] = record[field].get("url")

                            except AttributeError:
                                new_record[field_label] = record[field]
                        else:
                            new_record[field_label] =  ""

                    else:
                        fieldnames.append(field_label)

                        #  handle raw fields whose value is an empty list
                        try:
                            length = len(record[field]) > 0

                        except TypeError:
                            length = True

                        if length:
                            new_record[field_label] = record[field]
                        else:
                            new_record[field_label] = ""

                else:
                    #  raw not in record
                    new_record[field_label] = record[field]
                    fieldnames.append(field_label)

            parsed_data.append(new_record)

        self.data = parsed_data
        self.fieldnames = list(set(fieldnames))

        return self.data

    def _get_endpoint(self):
        """
        Get endpoint for object or view-based request

        return self.endpoint (string)
        """
        if self.scene and self.view:
            self.endpoint = "https://api.knack.com/v1/pages/{}/views/{}/records?rows_per_page={}".format(
                self.scene, self.view, self.rows_per_page
            )

            return self.endpoint

        if self.obj:
            self.endpoint = "https://api.knack.com/v1/objects/{}/records?rows_per_page={}".format(
                self.obj, self.rows_per_page
            )
            return self.endpoint

    def _stringify_ambiguous_field(self, field_data):
        """
        Handle ambiguous Knack fields that may be a string or an array.
        Return a comma-separated string of field values (for arrays)
        or a field value string if only one value is present
        """
        if type(field_data) is not list:
            return field_data
        elif len(field_data) > 1:
            return ",".join(str(f) for f in field_data)
        elif len(field_data) == 1:
            return field_data[0]
        else:
            return ""

    def _convert_timestamps(self):

        converted_records = deepcopy(self.data)

        if self.tzinfo:
            tz = pytz.timezone(self.tzinfo)
            localize = True

        for record in converted_records:
            for field in record.keys():
                field_id = self.field_map.get(field)

                if not field_id:
                    # generated "subfields" will not have a field map, and they
                    # will not be date/time. so don't handle them.
                    continue

                field_type = self.fields[field_id]["type"]

                if field_type in ["date", "date_time"]:
                    d = record[field]

                    if isinstance(d, str):
                        # this is a null value that has been string-converted
                        continue

                    # create a naive datetime object from the timestamp
                    dt_utc = datetime.utcfromtimestamp(d / 1000)

                    if localize:
                        # set timezone and print in local datestring
                        record[field] = (
                            dt_utc.replace(tzinfo=pytz.utc).astimezone(tz).isoformat()
                        )
                    else:
                        # or just stringify the UTC, if no tzinfo
                        record[field] = dt_utc.replace(tzinfo=pytz.utc).isoformat()

        return converted_records

    def _assemble_downloads(self, path, download_fields, label_fields):
        """
        Assemble paths and filenames of files to be downloaded.
        Returns list of dicts where each entry is {"url" : "abc", "filename" : "xyz"}
        """
        downloads = []

        for record in self.data:
            for field in download_fields:
                download = {}

                download["url"] = record.get(field)

                if not download["url"]:
                    continue
                
                filename = os.path.basename(download["url"])

                if label_fields:
                    """
                    We reverse traverse to ensure that field labels are prepended in
                    sequence provided.
                    """
                    for field in reversed(label_fields):
                        filename = f"{record.get(field)}_{filename}"

                download["filename"] = os.path.join(path, filename)

                downloads.append(download)

        return downloads

    def _download_files(self):
        download_count = 0

        for file in self.downloads:
            print(f"\nDownloading {file['url']}")

            if not self.overwrite_files:
                if os.path.exists(file["filename"]):
                    print(f"\nWARNING: {file['filename']} already exist.")
                continue

            r = requests.get(file["url"], allow_redirects=True)

            r.raise_for_status()

            with open(file["filename"], "wb") as fout:
                fout.write(r.content)
                download_count += 1

        return download_count

    def download(
        self,
        destination="_downloads",
        download_fields=None,
        label_fields=None,
        overwrite=True,
    ):
        """
        Download files from Knack records. Requires that the Knack instance has been
        supplied scene and view keys.

        Parameters
        ----------
        destination : string (optional | default: _downloads)
            relative path to the directory to which files will be written
        download_fields : list (optional | default : knackpy_downloads)
            The specific field names (by label, not knack ID) in which contain
            file references. If none are provided, all fields of type=="file" will
            be retrieved.
        label_fields : list (optional | default: None)
            Any field names (by label, not knack ID) specificed here will be prepended
            to the attachment filename, separated by an underscore (_).
        overwrite : bool (optional | default: True)
            Indicates if existing files will be overwritten.
        Returns
        _______
        Integer count of files downloaded.

        # TODO: how to handle many fieldnames in field?
        """
        if not self.scene and self.view:
            raise Exception(
                "Scene and view keys are required to download files. This Knack instance must have been created with an object ID rather than scene + view ids."
            )

        if not isinstance(download_fields, list) and download_fields:
            raise Exception("download_fields paramenter must be a list.")

        if not isinstance(label_fields, list) and label_fields:
            raise Exception("label_fields paramenter must be a list.")

        # create output directory if it doesn't exist
        if not os.path.exists(destination):
            os.makedirs(destination)

        if not download_fields:
            # identify fields of type "file" if none are provided
            download_fields = [
                self.fields[field]["label"]
                for field in self.fields.keys()
                if self.fields[field]["type"] == "file" or self.fields[field]["type"] == "image"
            ]

        self.overwrite_files = overwrite

        self.downloads = self._assemble_downloads(
            destination, download_fields, label_fields
        )

        download_count = self._download_files()
        print(f"\n{download_count} files downloaded.")

        return download_count

    def to_csv(self, filename, delimiter=","):
        """
        Write data from Knack instance to csv
        
        Parameters
        ----------
        filename : string (required)
            Name of the output file that will be created
        delimiter : string (optional | default : ",")
            The column separation character that will be used when
            writing data to file.

        Returns
        _______
        None
    """
        csv_data = self._convert_timestamps()

        with open(filename, "w", newline="\n") as fout:
            self.fieldnames.sort()

            writer = csv.DictWriter(
                fout, fieldnames=self.fieldnames, delimiter=delimiter
            )
            writer.writeheader()

            for row in csv_data:
                writer.writerow(row)

        return None


#  helper functions
def get_app_data(app_id, timeout=10):
    """
    Get a Knack app configuration object
    """
    endpoint = "https://loader.knack.com/v1/applications/{}".format(app_id)
    res = requests.get(endpoint, timeout=timeout)

    if res.status_code == 200:
        return res.json()["application"]
    else:
        raise Exception(req.text)


def record(
    data,
    obj_key=None,
    app_id=None,
    api_key=None,
    id_key="id",
    method=None,
    timeout=10,
    max_attempts=5,
):

    """
    Knack API request wrapper creating, updating, and deleting Knack records.
    """
    endpoint = "https://api.knack.com/v1/objects/{}/records".format(obj_key)

    if method != "create":
        _id = data[id_key]
        endpoint = "{}/{}".format(endpoint, _id)

    if method == "create":
        method = "POST"

    elif method == "update":
        method = "PUT"

    elif method == "delete":
        method = "DELETE"

    else:
        raise Exception("Invalid method: {}".format(method))

    headers = {
        "x-knack-application-id": app_id,
        "x-knack-rest-api-key": api_key,
        "Content-type": "application/json",
    }

    return _record_request(
        data, endpoint, headers, method, timeout=timeout, max_attempts=max_attempts
    )


def _record_request(data, endpoint, headers, method, timeout=10, max_attempts=5):
    """
    Build and send a Knack create/update/delete record request
    """
    s = requests.Session()

    req = requests.Request(method, endpoint, json=data, headers=headers)

    prepped = req.prepare()

    attempts = 0

    while attempts < max_attempts:

        attempts += 1

        try:

            res = s.send(prepped, timeout=timeout)

            break

        except requests.exceptions.Timeout as e:
            if attempts < max_attempts:
                logging.info("Request timeout.")
                continue
            else:
                raise e

    if res.status_code == 200:
        return res.json()
    else:
        raise Exception(res.text)
