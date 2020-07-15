# Knackpy

![Build](https://github.com/cityofaustin/knackpy/workflows/Build/badge.svg?branch=v1.0.0)
![Coverage](https://raw.githubusercontent.com/cityofaustin/knackpy/dev/coverage.svg)
![Python](https://img.shields.io/badge/Python-v3.6+-blue)

_Knackpy v1.0 is under development. Documented methods should work, but check the status badge ^^_

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Modules](#modules)
  - [App](#app)
  - [Records](#records)
  - [Fields](#fields)
  - [Api](#api)
  - [CRUD Operations](#crud-operations)
- [File Uploads and Downloads](#file-uploads-and-downloads)
- [Advanced Usage](#advanced-usage)
- [Timestamps and Localization](#timestamps-and-localization)
- [Exceptions](#exceptions)
- [Migrating from `v0.1`](#migrating-from-v0.1)
- [Contributing](#contributing)

## Installation

Knackpy requires Python v3.6+. To use the development version Knackpy v1.0, install with:

```bash
$ pip install knackpy-dev
```

## Quick Start

```python
>>> import knackpy
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey")
>>> records = app.records("object_1")
>>> records_formatted = [record.format() for record in records]
```

## Modules

### `App`

Knackpy is designed around the `App` class. It provides helpers for querying and manipulating Knack application data. You should use the `App` class because:

- It allows you to query obejcts and views by key or name
- It takes care of [localization issues](#timestamps-and-localization)
- It let's you download and upload files from your app.
- It does other things, too

##### Args

- `app_id` (`str`): Knack [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id) string.

- `api_key` (`str`, optional, default=`None`): Knack [API key](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).

- `metadata` (`dict`, optional, default=`None`): The Knack app's metadata as a `dict`. If `None` it will be fetched on init. You can find your apps metadata at [here](https://loader.knack.com/v1/applications/5d79512148c4af00106d1507).

- `tzinfo` (`pytz.Timezone`, optional): A [pytz.Timezone](https://pythonhosted.org/pytz/) object. Defaults to None. When None, is set automatically based on the app's `metadadata`.

- `max_attempts` (`int`): The maximum number of attempts to make if a request times out. Default values that are set in `knackpy.api.request`.

- `timeout` (`int`, optional, default=`30`): Number of seconds to wait before a Knack API request times out. Further reading: [Requests docs](https://requests.readthedocs.io/en/master/user/quickstart/#timeouts).

##### Usage

To create an `App` instance, the bare minimum you need to provide is your [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).

If you construct an `App` instance without providing an API key, you will only be able to fetch records from publicly-availble views.

Note that fetching data from public views is a smart way to avoid hitting your [API limit](https://www.knack.com/developer-documentation/#api-limits).

```python
# basic app construction with api key
>>> import knackpy
>>> my_app = knackpy.App(app_id="myappid", api_key="myverysecretapikey")
```

#### `App.records()`

Fetch records from a Knack application.

##### Args

- `name_or_key` (`str`): An object or view key or name string that exists in the app.
- `refresh` (`bool`, optional, default=`None`): If true, will re-fetch the records from the Knack API, regardless of if they have already been downloaded.
- `record_limit` (`int`, optional, default=`None`): The maximum number of records to retrieve. If `None`, all records will be downloaded.
- `filters` (`dict` or `list`, optional): A `dict` or `list` of query filters to be applied, per [Knack's specification](https://www.knack.com/developer-documentation/#filters).

##### Returns

A generator function which yields `knackpy.Record` objects.

##### Usage

```python
# fetch all records from object_1
>>> records = my_app.records("object_1")
```

```python
# fetch all records from view named "My Exciting View"
>>> records = my_app.records("My Exciting View")
```

Container identifiers can be supplied as an object or view key (`object_1`, `view_1`) or name (`my_exciting_object`, `My Exciting View`).

Note that namespace conflicts are highly likely when fetching by name, because Knack uses object names as the default name for views. If you attempt to query your application by a name that exists as both an object and a view, Knackpy will raise a `ValueError`.

`App.records()` returns a generator. You'll need to re-intialize it with `App.records(<container:str>)` each time you iterate on your records.

```python
>>> records_formatted = [
...    record.format() for record in my_app.records("my_exciting_object")
... ]
# re-intialize the records generator
>>> records_raw = [record.raw for record in my_app.recordss("my_exciting_object")]
```

If you've only fetched one container, you can omit the container name when accessing your records. This is helpful during development, but for readability we suggest you avoid this practice in production code.

```python
>>> my_app = knackpy.App(app_id="myappid")
>>> records = [record for record in my_app.records("My Exciting View")]
# you can omit the container name if you want to access your records again
>>> same_records_without_accessor = [record for record in my_app.records()]
```

Once you've constructed an `App` instance, you can resuse it to fetch records from other objects and views. This cuts down on calls to Knack's metadata API.

```python
>>> my_app.records("my_exciting_object")
>>> my_app.records("my_boring_object")
>>> my_app.records("view_1")
```

Raw record data is available at `App.data`. You can also use this to cehck the readily available data in your App instance, like so:

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

You can cut down on API calls by providing your own Knack metadata when creating an `App` instance:

```python
>>> import json
# get your app's metadata here: https://loader.knack.com/v1/applications/<app_id:str>"
>>> with open("my_metadata.json", "r") as fin:
...     metadata = json.loads(fin.read())
>> app = knackpy.App(app_id,  metadata=metadata)
```

You can side-load record data into your your app as well. Note that you must assign your data to a valid key that exists in your app:

```python
>>> with open("my_knack_data.json", "r") as fin:
...     data = { "object_3": json.loads(fin.read()) }
>> app.data = data
>> records = [record.format() for record in app.records("object_3")]
```

You can use `knackpy.records()` to fetch "raw" data from your Knack app. Be aware that raw Knack timestamps [are problematic](#timestamps-and-localization). See the [Records](#records) documentation.

#### `App.info()`

Display summary metrics about the app.

```python
>>> app.info()
{'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

#### `App.to_csv()`

Write formatted Knack records to CSV. Be aware that destination will be overwritten, if they exist.

##### Args

- `name_or_key` (`str`): an object or view key or name string that exists in the app.
- `out_dir` (`str`, optional): Relative path to the directory to which files will be written. Defaults to "\_csv"
- `delimiter` (`str`, optional): The delimiter string. Defaults to comma (`,`).

-

### Api

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
>>> my_app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey", tzinfo="US/Eastern")
# yields raw records with corrected millisecond timestamps
>>> records_raw = [record.raw for record in app.records("object_3")]
# yields corrected timestamps as ISO-8601 strings
>>> records_formatted = [record.format() for record in app.records("object_3")]
```

## Exceptions

Knackpy uses Python's built-in exceptions, as well as Requests's [exceptions](https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions) when interacting with the Knack API.

If you need to inspect an API exception (for example to see the text content of the response), you can access the `Response` object by handling the exception like so:

```python
>>> my_app = knackpy.App(api_key="myappid")
# raises HTTPError. You cannot request object records without supplying an API key
>>> try:
...       records = my_app.records("object_1")
... except HTTPError as e:
...     print(e.response.text)
...     raise e
# 'Unauthorized Object Access'
```
