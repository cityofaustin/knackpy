# Knackpy v1.0 [under development]

*Knackpy v1.0 is still under development*

## Quick Start

You can use `knackpy.get()` to fetch "raw" data from your Knack app. Be aware that raw Knack timestamps [are problematic](). 

```python
# This is equivalent to exporting records in JSON format from the Knack Builder
>>> import json
>>> import knackpy
>>> data = knackpy.get("my_app_id", api_key="myverysecretapikey", obj="object_1")
>>> with open("object_1.json", "w") as fout:
  fout.write(json.dumps(data))
```

More likely, you'll want to use the `App` class to correct and format your data.

```python
>>> app = knackpy.App(app_id,  api_key="myverysecretapikey")
>>> records = app.get("object_1")
>>> records_formatted = [record.format() for record in records]
```

Container identifiers can be supplied as Knack keys (`object_1`, `view_1`) or names (`my_exciting_object`, `My Exciting View`)

```python
>>> app = knackpy.App(app_id,  api_key="myverysecretapikey")
>>> records = app.get("my_exciting_object")
```

`App.get()` returns a generator function. You'll need to re-intialize it with `App.get(<container:str>)` each time you iterate on your records.

```python
>>> records = app.get("my_exciting_object") 
>>> records_formatted = [record.format() for record in records]
# re-intialize the records generator
>>> records = app.get(container="my_exciting_object") 
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
>>> view_1_records = [record.format() for record in app.get("view_22")]
```

References to all available data endpoints are stored at `App.containers`. This is handy if you want to check the name of a container, or its key:

```python
>>> app.containers
{
 'object_1': Container(obj='object_1', view=None, scene=None, name='my_boring_object'),
 'object_2': Container(obj='object_2', view=None, scene=None, name='my_exciting_object'),
 'view_1': Container(obj=None, view='view_1', scene='scene_1', name='My Exciting View'),
}
```

You can cut down on API calls by side-loading your own Knack metadata and/or record data to an `App`:

```python
>>> import json
# you can find your app's metadata at: https://{subdomain}.knack.com/v1/applications"
>> my_metadata = json.loads("my_metadata.json")
>> app = knackpy.App(app_id,  metadata=my_metadata)
# note that the top-level keys of side-loaded records must be container names that exist in your app's metadata
>> data = { "my_object_name": json.loads("my_data.json") }
>> app.data = data
>> records = [record.format() for record in app.get("my_object_name")]
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