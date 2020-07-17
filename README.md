# Knackpy

Docs v1.0

![Build](https://github.com/cityofaustin/knackpy/workflows/Build/badge.svg?branch=v1.0.0)
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
>>> records = [record for record in app.records("object_1")]
# get the formatted keys/values of each record
>>> records_formatted = [record.format() for record in records]
# access a record property by name
>>> customer_address =  records[0]["Customer Address"]
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

Use `App.records()` to fetch records from a Knack application. Container identifiers can be supplied as a key (`object_1`, `view_1`) or a name (`my_exciting_object`, `My Exciting View`).

```python
# fetch all records from object_1
>>> records = app.records("object_1")
# or
# fetch all records from view named "My Exciting View"
>>> records = app.records("My Exciting View")
```

{{< hint danger >}}
#### Be Careful When Using Named References
Namespace conflicts are highly likely when fetching by name, because Knack uses object names as the default name for views. If you attempt to query your application by a name that exists as both an object and a view, Knackpy will raise a `ValueError`.
{{< /hint >}}

You can resuse the same `App` instance to fetch records from other objects and views.

```python
>>> app.records("my_exciting_object")
>>> app.records("my_boring_object")
>>> app.records("view_1")
```

If you've only fetched one container, you can omit the container name when accessing your records. This is helpful during development, but for readability we suggest you avoid this practice in production code.

```python
>>> records = [record for record in app.records("My Exciting View")]
# you can omit the container name if you want to access your records again
>>> same_records_without_accessor = [record for record in app.records()]
```

You can refine your record requests by specifify a `record_limit`, `filters`, and `timeout`. See the [module documentaiton]() for details.

```python
>>> filters = {
    "match": "or",
    "rules": [
        {"field": "field_1", "operator": "is", "value": 1},
        {"field": "field_2", "operator": "is", "value": "Pizza"},
    ],
}
>>> records = app.records("object_1", record_limit=10, filters=filters)
```

### Advanced `App.records()` Usage

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

### Other `App` Methods

Display summary metrics about the app.

```python
>>> app.info()
{'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

Write a container to CSV. Be aware that destination will be overwritten, if they exist.

```python
>>> app.to_csv("my exciting view", out_dir="data")
```

## Working with `Record` Objects

`Record` objects are `dict`-like containers for Knack record data. Note that all timestamps have been [correctly set to unix time]().

You can access a record value like you would a `dict`, using the field key or field name:

```python
>>> record = next(app.records("object_1")
# access a value via field key
{"city": "Austin", "state": "TX", "street": "8700 Cameron Rd", "street2": "Suite 1", "zip": "78754"}
>>> record["field_22"]
# access a value via field name
>>> record["Customer Address"]
{"city": "Austin", "state": "TX", "street": "8700 Cameron Rd", "street2": "Suite 1", "zip": "78754"}
```

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
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey", tzinfo="US/Eastern")
# yields raw records with corrected millisecond timestamps
>>> records_raw = [record.raw for record in app.records("object_3")]
# yields corrected timestamps as ISO-8601 strings
>>> records_formatted = [record.format() for record in app.records("object_3")]
```

## Exceptions

Knackpy uses Python's built-in exceptions, as well as Requests's [exceptions](https://requests.readthedocs.io/en/master/user/quickstart/#errors-and-exceptions) when interacting with the Knack API.

If you need to inspect an API exception (for example to see the text content of the response), you can access the `Response` object by handling the exception like so:

```python
>>> app = knackpy.App(api_key="myappid")
# raises HTTPError. You cannot request object records without supplying an API key
>>> try:
...       records = app.records("object_1")
... except HTTPError as e:
...     print(e.response.text)
...     raise e
# 'Unauthorized Object Access'
```
