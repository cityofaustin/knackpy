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

More likely, you'll want to use `knackpy.App` to correct and format your data.

```python
>>> import knackpy

>>> app = knackpy.App(app_id,  api_key="myverysecretapikey")
>>> records = app.get("object_3")
>>> records_formatted = [record.format() for record in records]
```

Knackpy is designed to handle lots of records, so `App.get()` returns a generator function. You'll need to re-intialize the generator with `App.records.get()` every time you iterate on all your records.

```python
>>> import knackpy
>>> app = knackpy.App(app_id,  api_key="myverysecretapikey")

# you can fetch by object name, object key, view name, or view key
>>> records = app.get("my_object_name") 
>>> records_formatted = [record.format() for record in records]

# re-intialize the records generator
>>> records = app.records.get("object_3")

# these records are raw, but the timestamps have been corrected
>>> records_raw = [record.raw for record in records]
```

Once you've constructed an `App` instance, you can resuse it to fetch records from other objects and views. This will cut down on calls to Knack's metadata API.

```python
# you can fetch by object name, object key, view name, or view key
>>> app.get("my_exciting_object") 

>>> app.get("my_boring_object")

>>> app.data.keys()
["my_boring_object", "my_exciting_object"]
```

## What's New in v1.0

* The `Knack` class is now `App`, and it's API is more intuitive.
* Fetch records using object/view names
* No more rows-per-page or page count limiting; just set a `record_limit`.
* `App`s have built-in metadata:

```python
>>> app.info()
# {'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

* Pythonic use of `exceptions`, `warnings`, and `logging`.
* Automatic localization (no need to set TZ info)