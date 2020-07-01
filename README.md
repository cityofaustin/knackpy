# Knackpy v1.0 [under development]

*Knackpy v1.0 is still under development*

## Quick Start

You can use `knackpy.get()` to fetch "raw" data from your Knack app. Be aware that raw Knack timestamps [are problematic](). 

```python
# This is equivalent to exporting records in JSON format from the Knack Builder
>>> import json
>>> import knackpy
>>> data = knackpy.get("my_app_id", api_key="myverysecretapikey", obj="object_3")
>>> with open("object_3.json", "w") as fout:
  fout.write(json.dumps(data))
```

More likely, you'll want to use the `App` class to correct and format your data.

```python
>>> import knackpy
>>> app = knackpy.App(app_id,  api_key="myverysecretapikey")

# containers can be supplied as Knack keys (`object_1`, `view_22`) or names (`my_exciting_object_name`, `my_exciting_view_name`)
>>> container = "my_exciting_object_name"
>>> records = app.get(container)
>>> records_formatted = [record.format() for record in records]
```

Knackpy is designed to handle lots of records, so `App.get()` returns a generator function. You'll need to re-intialize the generator with `App.records(<container:str>)` each time you iterate on your records.

```python
>>> records = app.get("my_exciting_object_name") 
>>> records_formatted = [record.format() for record in records]
# re-intialize the records generator. `<container>` must match a name you supplied to App.get() `
>>> records = app.records(container="my_exciting_object_name") 
# these records are raw, but the timestamps have been corrected
>>> records_raw = [record.raw for record in records]
```

Once you've constructed an `App` instance, you can resuse it to fetch records from other objects and views. This cuts down on calls to Knack's metadata API.

```python
>>> app.get("my_exciting_object_name") 
>>> app.get("my_boring_object_name")
>>> app.get("view_22")
```

You can check the available data in your App instance like so:

```python
>>> app.data.keys()
["my_boring_object", "my_exciting_object", "view_22"]

>>> view_22_records = [record.format() for record in app.records("view_22")]
```

References to all available data endpoints are stored at `App.containers`. This is handy if you want to check the name of container, or vice-versa:

```python
>>> app.containers.keys()
['_conflicts',
 'object_1',
 'My Boring Object', # Eek, I recommend you use lower_snake_case for your object names
 'object_2',
 'My Exciting Object',
 'view_1',
 'My Boring View']

>>> app.containers["object_1"]
Container(obj='object_1', view=None, scene=None, name='My Boring Object')
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
>> records = [record.format() for record in app.records("my_object_name")]
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