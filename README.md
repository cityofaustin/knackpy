# Knackpy v1.0 [under development]

*Knackpy v1.0 is still under development*

## Quick Start

```python
>>> import knackpy

>>> app = knackpy.App("my_app_id", api_key="my_very_secret_api_key")
   
>>> app.get_data("my_object_name", record_limit=1)

>>> for record in app.records.get("my_object_name", format_keys=True, format_values=True):
        print(record)

# { 'id' : '5d7964422d7159001659b27a', 'my_number_field': 2, 'my_email_field': 'knackpy_user@genius.town' }  

```

## What's New in v1.0

* The `Knack` class is now `App`, and it's API is more intuitive.

* Fetch records from multiple objects and/or views from one `App` instance.

```python
>>> app.get_data("my_object_name", "my_view_name", record_limit=1)
>>> app.records.keys()
# dict_keys(['my_object_name', 'my_view_name'])

```

* Fetch records using object/view names
* No more need to supply scene keys
* No more rows-per-page or page count limiting; just set a `record_limit`.
* Selectively humanize your record keys, values, or both. 
* `App`s have built-in metadata:

```python
>>> app.info()
# {'objects': 10, 'scenes': 4, 'records': 6786, 'size': '25.47mb'}
```

* Pythonic use of `exceptions`, `warnings`, and `logging`.