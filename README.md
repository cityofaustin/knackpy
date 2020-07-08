# Knackpy 

![Build](https://github.com/cityofaustin/knackpy/workflows/Build/badge.svg?branch=v1.0.0)
![Coverage](https://raw.githubusercontent.com/cityofaustin/knackpy/v1.0.0/coverage.svg)
![Python](https://img.shields.io/badge/Python-v3.6+-blue)

*Knackpy v1.0 is under development. Documented methods should work, but check the status badge ^^*

## Installation

Knackpy requires Python v3.6+. To use the development version Knackpy v1.0, install with:

```bash
$ pip install knackpy-dev
```

## Quick Start

You can use `knackpy.get()` to fetch "raw" data from your Knack app. Be aware that raw Knack timestamps [are problematic](). 

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

More likely, you'll want to use the `App` class to correct and format your data.

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey")
>>> records = app.get("object_1")
>>> records_formatted = [record.format() for record in records]
```

Container identifiers can be supplied as Knack keys (`object_1`, `view_1`) or names (`my_exciting_object`, `My Exciting View`)

```python
>>> app = knackpy.App(app_id="myappid",  api_key="myverysecretapikey")
>>> records = app.get("my_exciting_object")
```

`App.get()` returns a generator function. You'll need to re-intialize it with `App.get(<container:str>)` each time you iterate on your records.

```python
>>> records = app.get("my_exciting_object") 
>>> records_formatted = [record.format() for record in records]
# re-intialize the records generator
>>> records = app.get("my_exciting_object") 
# these records are raw, but the timestamps have been corrected
>>> records_raw = [record.raw for record in records]
```

Once you've constructed an `App` instance, you can resuse it to fetch records from other objects and views. This cuts down on calls to Knack's metadata API.

```python
>>> app.get("my_exciting_object") 
>>> app.get("my_boring_object")
>>> app.get("view_1")
```

By default, an `App` instance will only fetch records for a container once. Use `refresh=True` to force a new fetch from the Knack API.

```python
>>> records = app.get("my_exciting_object", refresh=True) 
```

You can check the available data in your App instance like so:

```python
>>> app.data.keys()
["object_1", "object_2", "view_1"]
>>> view_1_records = [record.format() for record in app.records("view_22")]
```

References to all available data endpoints are stored at `App.containers`. This is handy if you want to check the name of a container, or its key:

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
# you can find your app's metadata at: https://loader.knack.com/v1/applications/<app_id:str>"
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

* The `Knack` class is now `App`, and it's API is more intuitive.
* Fetch records using object/view names
* No more rows-per-page or page count limiting; just set a `record_limit`.
* `App` summary stats:

```python
>>> app.info()
{'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

* Pythonic use of `exceptions`, `warnings`, and `logging`.
* Automatic localization (no need to set TZ info)
* "Raw" data is available with timestamp corrections
* Reduce API calls with metadata and/or record side-loading
```python
>>> data = knackpy.get("my_app_id", api_key="myverysecretapikey", obj="object_3", record_limit=10)
```
* Null values are consistently returned as `NoneType`s
- `knackpy.record`: param `obj_key` >> `obj`.
- the id key of a `record` create/update/detele object must be "id"