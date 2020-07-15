# Knackpy

![Build](https://github.com/cityofaustin/knackpy/workflows/Build/badge.svg?branch=v1.0.0)
![Coverage](https://raw.githubusercontent.com/cityofaustin/knackpy/dev/coverage.svg)
![Python](https://img.shields.io/badge/Python-v3.6+-blue)

_Knackpy v1.0 is under development. Documented methods should work, but check the status badge ^^_

## Table of Contents

- Installation
- Quick Start
- The `App` Class
- Working with Records and Fields
- CRUD Operations
- File Uploads and Downloads
- Advanced Methods
- Timestamps and Localization
- Logging and Exceptions
- Migrating from Knackpy `v0.1`
- Contributing

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

## The `App` Class (`knackpy.App()`)

The Knackpy API is designed around the `App()` class, which provides helpers for query and manipulating data from a Knack application.

### Args:

- `app_id` (`str`): Knack [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id) string.

- `api_key` (`str`, optional, default=`None`): Knack [API key](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).

- `metadata` (`dict`, optional, default=`None`): The Knack app's metadata as a `dict`. If `None` it will be fetched on init. You can find your apps metadata at [here](https://loader.knack.com/v1/applications/5d79512148c4af00106d1507).

- `tzinfo` (`pytz.Timezone`, optional): A [pytz.Timezone](https://pythonhosted.org/pytz/) object. Defaults to None. When None, is set automatically based on the app's `metadadata`.

- `max_attempts` (`int`): The maximum number of attempts to make if a request times out. Default values that are set in `knackpy.api.request`.

- `timeout` (`int`, optional, default=`30`): Number of seconds to wait before a Knack API request times out.

### Usage

To create an `App` instance, the bare minimum you need to provide is your [application ID](https://www.knack.com/developer-documentation/#find-your-api-key-amp-application-id).

If you construct an `App` instance without also providing an API key, you will only be able to fetch records from publicly-availble views.

Note that fetching data from public views is a smart way to avoid hitting your [API limit](https://www.knack.com/developer-documentation/#api-limits).

```python
# basic app construction with api key
>>> import knackpy
>>> my_app = knackpy.App(app_id="myappid", api_key="myverysecretapikey")
```

### Accessing Records

To fetch records, use `App.records(<container_name:str>)`.

```python
# fetch all records from object_1
>>> records = my_app.records("object_1")
```

Container identifiers can be supplied as an object or view key (`object_1`, `view_1`) or name (`my_exciting_object`, `My Exciting View`).

Note that namespace conflicts are highly likely when fetching by name, because Knack uses object names as the default name for views. If you attempt to query your application by a name that exists as both an object and a view, Knackpy will raise a `ValueError`.

```python
# fetch all records from view named "My Exciting View"
>>> records = my_app.records("My Exciting View")
```

`App.records()` returns a generator. You'll need to re-intialize it with `App.records(<container:str>)` each time you iterate on your records.

```python
>>> records_formatted = [
...    record.format() for record in my_app.record("my_exciting_object")
... ]
# re-intialize the records generator
>>> records_raw = [record.raw for record in my_app.records("my_exciting_object")]
```

Once you've constructed an `App` instance, you can resuse it to fetch records from other objects and views. This cuts down on calls to Knack's metadata API.

```python
>>> my_app.records("my_exciting_object")
>>> my_app.records("my_boring_object")
>>> my_app.records("view_1")
```

By default, an `App` instance will only fetch records for a container once. Use `refresh=True` to force a new fetch from the Knack API.

```python
>>> records = app.records("my_exciting_object", refresh=True)
```

You can check the readily available data in your App instance like so:

```python
>>> app.data.keys()
["object_1", "object_2", "view_1"]
>>> view_1_records = [record.format() for record in app.records("view_22")]
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

You can use `knackpy.records()` to fetch "raw" data from your Knack app. Be aware that raw Knack timestamps [are problematic](#timestamps-and-localization).

### Other `App` Methods

#### `App.info()`

Display summary metrics about the app.

```python
>>> app.info()
{'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

#### `App.to_csv()`

Write formatted Knack records to CSV. Be aware that destination will be overwritten, if they exist.

Args:

- `name_or_key` (`str`): an object or view key or name string that exists in the app.
- `out_dir` (`str`, optional): Relative path to the directory to which files will be written. Defaults to "\_csv"
- `delimiter` (`str`, optional): The delimiter characte(s). Defaults to comma (`,`).

-

## Advanced Methods

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

Although the Knack API returns timestamp values as Unix timestamps in millesconds these raw values represent millisecond timestamps _in your localized timezone_. For example a Knack timestamp value of `1578254700000` represents Sunday, January 5, 2020 8:05:00 PM _local time_.

To address this, the `App` class handles the conversion of Knack timestamps into _real_ millisecond unix timestamps which are timezone naive. Timestamps are corrected by referencing the timezone info in your apps metadata. You can manually override your app's timezone information by passing an [IANA-compliant](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) timezone string to your `App` instance, like so:

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey", tzinfo="US/Eastern")
```

If you'd like to access your raw, uncorrected records, they can be found at `app.data[<container_name:str>]`.

Note also that `Record` objects return corrected timestamps via `Record.raw` and `Record.format()`. So,

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey", tzinfo="US/Eastern")
# yields raw records with corrected millisecond timestamps
>>> records_raw = [record.raw for record in app.records("object_3")]
# yields corrected timestamps as ISO-8601 strings
>>> records_formatted = [record.format() for record in app.records("object_3")]
```
