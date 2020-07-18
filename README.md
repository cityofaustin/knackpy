# Knackpy

Docs v1.0
![Build](https://github.com/cityofaustin/knackpy/workflows/Build/badge.svg?branch=master)
![Coverage](https://raw.githubusercontent.com/cityofaustin/knackpy/dev/coverage.svg)
![Python](https://img.shields.io/badge/Python-v3.6+-blue)

_Knackpy v1.0 is under development. Documented methods should work, but check the status badge_

## Installation

Knackpy requires Python v3.6+. To use the development version Knackpy v1.0, install with:

```shell
$ pip install knackpy-dev
```

## Quick Start

```python
>>> import knackpy
# basic app construction
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey")
# fetch all records from 'object_1'
>>> records = app.get("object_1")]
# get the formatted keys/values of each record
>>> records_formatted = [record.format() for record in records]
# access a record property by name
>>> customer_address = records[0]["Customer Address"]
# create a record
>>> knackpy.record()
```

## Working with Apps

Knackpy is designed around the `App` class. It provides helpers for querying
and manipulating Knack application data. You should use the `App` class
because:

- It allows you to query obejcts and views by key or name
- It takes care of [localization issues](#timestamps-and-localization)
- It let's you download and upload files from your app.
- It does other things, too.

To create an `App` instance, the bare minimum you need to provide is your [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).

If you construct an `App` instance without providing an API key, you will only be able to fetch records from publicly-availble views.

Note that fetching data from public views is a smart way to avoid hitting your [API limit](https://www.knack.com/developer-documentation/#api-limits).

```python
# basic app construction with api key
>>> import knackpy
>>> app = knackpy.App(app_id="myappid", api_key="myverysecretapikey")
```

### Getting Records

Use `App.get()` to fetch records from a Knack application. Container identifiers can be supplied as a key (`object_1`, `view_1`) or a name (`my_exciting_object`, `My Exciting View`).

```python
# fetch all records from object_1
>>> records = app.get("object_1")
# or
# fetch all records from view named "My Exciting View"
>>> records = app.get("My Exciting View")
```

{{< hint warning >}}

#### Be Careful When Using Named References

Namespace conflicts are highly likely when fetching by name, because Knack uses object names as the default name for views. If you attempt to query your application by a name that exists as both an object and a view, Knackpy will raise a `ValueError`.
{{< /hint >}}

You can resuse the same `App` instance to fetch records from other objects and views.

```python
>>> app.get("my_exciting_object")
>>> app.get("my_boring_object")
>>> app.get("view_1")
```

{{< hint info >}}

#### Omitting the Container Name

If you've only fetched one container, you can omit the container name when accessing your records. This is helpful during development, but for readability we suggest you avoid this practice in production code.

{{< /hint >}}

```python
>>> records = app.get("My Exciting View")
# you can omit the container name if you want to access your records again
>>> same_records_without_accessor = app.get()
```

You can refine your record requests by specififying a `record_limit`, `filters`, and `timeout`. See the [module documentaiton]() for details.

```python
>>> filters = {
    "match": "or",
    "rules": [
        {"field": "field_1", "operator": "is", "value": 1},
        {"field": "field_2", "operator": "is", "value": "Pizza"},
    ],
}
>>> records = app.get("object_1", record_limit=10, filters=filters)
```

### Creating, Updating, and Deleting Records

Create a record.

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey")
>>> data = {"field_1": "pizza"}
>>> record = app.record(method="create", data=data, obj="object_1")
```

Update a record.

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey")
>>> record = app.get("object_1")[0]
>>> data = dict(record)
>>> data["field_1"] = "new value"
>>> record = app.record(method="update", data=data, obj="object_1")
```

Delete a record.

```python
>>> response = app.record(method="delete", data={"id": "abc123xyz789"}, obj="object_1")
# response == {"delete": True}
```

### Downloading Files

Download files from an object or view.

- `container` (`str`): The name or key of the object or view from which files will be
  downloaded.

- `field` (`str`): The field key of the file or image field to be downloaded.

- `out_dir` (`str`, optional): Relative path to the directory to which files
  will be written. Defaults to "\_downloads".

- `label_keys` (`list`, optional): A list of field keys whose _values_ will be prepended to the attachment filename, separated by an underscore.

```python
>>> app.download(
...     container="object_1",
...     field="field_1",
...     out_dir="_downloads",
...     label_keys="field_2"
... )
```

### Uploading Files

### Advanced `App` Usage

Raw record data is available at `App.data`. You can use this property to check the readily available data in your App instance.

```python
>>> app.data.keys()
["object_1", "object_2", "view_1"]
```

References to all available endpoints are stored at `App.containers`. This is handy if you want to check the name of a container, or its key:

```python
>>> app.containers
[
    Container(obj='object_1', view=None, scene=None, name='my_boring_object'),
    Container(obj='object_2', view=None, scene=None, name='my_exciting_object'),
    Container(obj=None, view='view_1', scene='scene_1', name='My Exciting View'),
]
```

You can avoid an API call by providing your own Knack metadata when creating an `App` instance (unclear if metadata requests count against [API limits](https://www.knack.com/developer-documentation/#api-limits))

```python
>>> import json
# get your app's metadata here: https://loader.knack.com/v1/applications/<app_id:str>"
>>> with open("my_metadata.json", "r") as fin:
...     metadata = json.loads(fin.read())
>> app = knackpy.App(app_id,  metadata=metadata)
```

You can side-load record data into your your app as well. Note that you must assign your data to a valid key that exists in your app.

```python
>>> with open("my_knack_data.json", "r") as fin:
...     data = { "object_3": json.loads(fin.read()) }
>> app.data = data
>> records = [record.format() for record in app.get("object_3")]
```

You can use `knackpy.get()` to fetch "raw" data from your Knack app. Be aware that raw Knack timestamps [are problematic](#timestamps-and-localization). See the [Records](#records) documentation.

### Other `App` Methods

Display summary metrics about the app.

```python
>>> app.info()
{'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

Write a container to CSV. Be aware that destination files will be overwritten, if they exist.

```python
>>> app.to_csv("my exciting view", out_dir="data")
```

## Working with `Record` Objects

`Record` objects are `dict`-like containers for Knack record data. Note that all timestamps have been [correctly set to unix time](#timestamps-and-localization).

You can access a record value like you would a `dict`, using the field key or field name.

```python
>>> record = app.get("object_1")[0]
# access a value via field key
>>> record["field_22"]
{"city": "Austin", "state": "TX", "street": "8700 Cameron Rd", "street2": "Suite 1", "zip": "78754"}
# access a value via field name
>>> record["Customer Address"]
{"city": "Austin", "state": "TX", "street": "8700 Cameron Rd", "street2": "Suite 1", "zip": "78754"}
```

### Formatting Records

Format the keys and/or values of a record.

```python
# format keys and values
>>> formatted_record = record.format()
{ "id": "abc123xyz789", "Customer Address": "8700 Cameron Rd, Austin, TX, 78754" }
# only format the keys
>>> formatted_keys = record.format(values=False)
{ "id": "abc123xyz789", "Customer Address": {"city": "Austin", "state": "TX", "street": "8700 Cameron Rd", "street2": "Suite 1", "zip": "78754"}}
# only format the values
>>> formatted_values = record.format(keys=False)
{ "id": "abc123xyz789", "field_22": "8700 Cameron Rd, Austin, TX, 78754" }
```

Although a `Record` object looks like a `dict`, it contains `Field` objects (TODO: link to docs). If you want to convert a `Record` object into a plain-old `dict`, use the `dict()` built-in.

```python
>>> record = app.get("object_1")[0]
>>> data = dict(record)
```

### Dict-like `Record` methods (Items, Keys, and Names)

- `Record.items()`: returns a list of the knackpy `Field` objects contained within the `Record`.
- `Record.keys()`: returns a list (not a [`view`](https://docs.python.org/3/glossary.html#term-dictionary-view)) of the record's field keys.
- `Record.names()`: returns a list of the record's field names.

{{< hint warning >}}

Records may look raw, but any timestamps have been [corrected to real unix time](#timestamps-and-localization). If you want the raw, untouched data, use the `Record.raw` property.

{{ < /hint > }}

## Accessing the API Directly

```python
# This is equivalent to exporting records in JSON format from the Knack Builder
>>> import knackpy
>>> data = knackpy.get(
...     app_id="myappid",
...     api_key="myverysecretapikey",
...     obj="object_1",
...     record_limit=None,
...     timeout=30
... )
```

## Crud Operations

## What's New in v1.0

- The `Knack` class is now `App`.
- Fetch records using object/view names
- No more rows-per-page or page count limiting; just set a `record_limit`.
- `App` summary stats:

```python
>>> app.info()
{'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

- Pythonic use of `exceptions`, `warnings`, and `logging`.
- Automatic localization (no need to set TZ info)
- "Raw" data is available with timestamp corrections
- Reduce API calls with metadata and/or record side-loading
- Null values are consistently returned as `NoneType`'s

## Issues and Contributions

Issues and pull requests are welcome. Know that your contributions are donated to the [public domain](https://github.com/cityofaustin/knackpy/blob/master/LICENSE.md).

## Timestamps and Localization

Although the Knack API returns timestamp values as Unix timestamps in millesconds, these raw values represent millisecond timestamps _in your localized timezone_. For example a Knack timestamp value of `1578254700000` represents Sunday, January 5, 2020 8:05:00 PM _local time_.

To address this, the `App` class converts Knack timestamps into _real_ (UTC-based) unix timestamps. Timestamps are corrected by referencing the timezone info in your apps metadata. You can manually override your app's timezone information by passing an [IANA-compliant](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) timezone string to your `App` instance, like so:

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey", tzinfo="US/Eastern")
```

If you'd like to access your raw, uncorrected records, they can be found at `App.data[<container_name:str>]`.

Note also that `Record` objects return corrected timestamps via `Record.raw` and `Record.format()`. So,

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey", tzinfo="US/Eastern")
# yields raw records with corrected millisecond timestamps
>>> records_raw = [record.raw for record in app.get("object_3")]
# yields corrected timestamps as ISO-8601 strings
>>> records_formatted = [record.format() for record in app.get("object_3")]
```

## Exceptions

Knackpy uses Python's built-in exceptions, as well as Requests's [exceptions](https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions) when interacting with the Knack API.

If you need to inspect an API exception (for example to see the text content of the response), you can access the `Response` object by handling the exception like so:

```python
>>> app = knackpy.App(api_key="myappid")
# raises HTTPError. You cannot request object records without supplying an API key
>>> try:
...       records = app.get("object_1")
... except HTTPError as e:
...     print(e.response.text)
...     raise e
# 'Unauthorized Object Access'
```
