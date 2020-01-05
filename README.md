# Knackpy 

A Python client for interacting with [Knack](http://knack.com) applications.

## Installation

Knackpy requires Python v3.6+.

```
pip install knackpy
```
## Features
- [Object](#object-based-requests) and [view-based](#view-based-requests) requests
- [Filters](#filters)
- [Parsing of fieldnames and field labels](#field-data)
- [Create, update, and delete records](#create-update-or-delete-records)
- [CSV output](#csv-output)
- [File downloads](#file-downloads)

## Quick Start

### View-Based Requests

Get data from a Knack view.

```python
>>> from knackpy import Knack

>>> kn = Knack(
      scene='scene_34',
      view='view_10',
      app_id='abc123'
    )

>>> kn.data_raw
[{'field_1': 30424, 'field_1_raw': 30424, 'field_2': '11/18/2016'},...]
```

Provide a list of the view's reference objects to return humanized field names.

```python
>>> kn = Knack(
      scene='scene_34',
      view='view_10',
      ref_obj=['object_1', 'object_2'],
      app_id='myappid',
      api_key='topsecretapikey'
    )
 
>>> kn.data
[{'store_id': 30424, 'inspection_date': 1479448800000, 'id': '58598262bcb3437b51194040'},...]
```

### Object-Based Requests

Retrieve data directly from an object.

```python
>>> kn = Knack(
      obj='object_1',
      app_id='abc123',
      api_key='topsecretapikey'
    )
   
>>> kn.data
[{'store_id': 30424, 'inspection_date': 1479448800000, 'id': '58598262bcb3437b51194040'},...]
```

### Filters

You can pass a [filter](https://www.knack.com/developer-documentation/#filters) to object-based requests. 

```python

>>> filters = {
      'match': 'and',
      'rules': [
        {
          'field':'field_10',
          'operator':'is',
          'value':'No'
        },
        {
          'field':'field_11',
          'operator':'is',
          'value':'Yes'
        }
      ]
    }

>>> kn = Knack(
      obj='object_1',
      app_id='abc123',
      api_key='topsecretapikey',
      filters=filters
    )
```

### Field Data

Field metadata is available in object-based requests or in view-based requests when reference objects have been specified.

```python
>>> kn.fields
{'field_1': {' ': 'store_id', 'key': 'field_1,required': False, 'type': 'auto_increment'},...}

>>> kn.fieldnames
['store_id', 'inspection_date', 'store_status',...]

>>> kn.field_map
{'store_id' : 'field_1', 'store_status' : 'field_2',...}
```

### File Downloads

You can download files for the records you retrieve from a view. Files are overwritten by default:

```python
 >>> kn.download(overwrite=False) # Writes all new files to `_downloads` directory

>>> kn.download(
  destination="my_downloads",
  label_fields=["Attachment ID", "Date"], # Prepends the "Attachment ID" and "Date" values to the filename
  download_fields=["Photo", "Document"] # Downloads files from these specific fields only
)
```

### CSV Output

```python
>>> kn.to_csv('data.csv')
"store_id","inspection_date","store_status"
"30424","11-18-2016","OPEN"
"30200","10-01-2013","CLOSED"
...
```

### Create, Update, or Delete Records

Create a new record.

```python
>>> import knackpy

>>> record = {'field_1': 30424}

>>> response = knackpy.record(
      record,
      obj_key='object_12',
      api_id='myappid',
      api_key='topsecretapikey',
      method='create'
    )

{ 'id':'6a204bd89f3c8348afd5c77c717a097a', 'field_1': 30424, ...}
```

Update a record.

```python
>>> import knackpy

>>> record = {'id':'6a204bd89f3c8348afd5c77c717a097a','field_1': 2049}

>>> response = knackpy.record(
      record,
      obj_key='object_12',
      app_id='myappid',
      api_key='topsecretapikey',
      method='update'
    )
    
{ 'id':'6a204bd89f3c8348afd5c77c717a097a', 'field_1': 2049, ...}
```

Delete a record

```python
>>> record = {'id':'6a204bd89f3c8348afd5c77c717a097a'}

>>> response = knackpy.record(
      record,
      obj_key='object_12',
      app_id='myappid',
      api_key='topsecretapikey',
      method='delete'
    )

# API returns `{'delete': True}`
```    

### App Data

Get an app's configuration data (objects, scenes, etc.)

```python
>>> from knackpy import get_app_data

>>> my_app = get_app_data('myAppIdString')

>>> my_app['name']

"John's Amazing App"
```

## License

As a work of the City of Austin, this project is in the public domain within the United States.

Additionally, we waive copyright and related rights of the work worldwide through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).