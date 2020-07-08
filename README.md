
** *Version 1.0 is in progress, [here](https://github.com/cityofaustin/knackpy/tree/dev). All methods documented in the README are ready for a test drive* **

# Knackpy

A Python client for interacting with [Knack](http://knack.com) applications. 

## Contents

- [Issues and Contributions](#issues-and-contributions)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [License](https://github.com/cityofaustin/knackpy/blob/master/LICENSE.md)

## Issues and Contributions

Please @ me (johnclary, repo maintainer) in your issue description.

Contributions are welcome. Know that your contributions are donated to the [public domain](https://github.com/cityofaustin/knackpy/blob/master/LICENSE.md).

## Installation

Knackpy requires Python v3.6+.

```
pip install knackpy
```

## Quick Start

```python
>>> kn = Knack(
      obj='object_1',
      app_id='abc123',
      api_key='topsecretapikey',
      tzinfo="US/Central" # Be careful, this is the default value!
    )
   
>>> kn.data
[{'store_id': 30424, 'inspection_date': 1479448800000, 'id': '58598262bcb3437b51194040'},...]
```

## Documentation

- [Object](#object-based-requests) and [view-based](#view-based-requests) requests
- [Filters](#filters)
- [Parsing of fieldnames and field labels](#field-data)
- [Create, update, and delete records](#create-update-or-delete-records)
- [CSV output](#csv-output)
- [File downloads](#file-downloads)
- [Page and Row Limitng](#page-and-row-limiting)
- [Localization and Timezone Settings](#localization-and-timezone-settings)
- [Connection Fields](#connection-fields)
- [Timeouts and Retrying](#timeouts-and-retrying)
- [Knack Record ID's](#knack-record-ids)

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
  destination="my_downloads", # Writes to `my_downloads` directory
  label_fields=["Attachment ID", "Date"], # Prepends the "Attachment ID" and "Date" values to the filename
  download_fields=["Photo", "Document"] # Downloads files from these specific fields only
)
```

### CSV Output

You can write Knack data to a `CSV` file. Note that timestamps are converted to ISO 8601 format when written to CSV.

```python
>>> kn.to_csv('data.csv')
"store_id","inspection_date","store_status"
"30424","2020-01-05T15:05:00-05:00","OPEN"
"30200","2020-01-05T15:05:00-05:00","CLOSED"
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

### Page and Row Limiting

Use `rows_per_page` (default=`1000`) and/or `page_limit` (default=`1000`) to limit results. 

Note that maximum rows-per-page allowed by the Knack API is 1000.

```python
>>> kn = Knack(
      obj='object_1',
      app_id='abc123',
      api_key='topsecretapikey',
      rows_per_page=1, # 
      page_limit=1
    )

```

### Localization and Timezone Settings

*Note that knackpy's default timezone value is `US/Central`.*

#### A Note about Knack Timestamps

You may be wondering why timezone settings are concern, given that Knackpy, like the Knack API, returns timestamp values as Unix timestamps in millesconds (thus, there is no timezone encoding at all). However, the Knack API confusingly returns *millisecond timestamps in your localized  timezone*!

For example, if you inspect a timezone value in Knack, e.g., `1578254700000`, this value represents  Sunday, January 5, 2020 8:05:00 PM *local time*.

To address this, knackpy handles the conversion of Knack timestamps into *real* millisecond unix timestamps which are timezone naive. However, the original "local timestamps" are preserved in the `Knack.data_raw` object. If you're working with that data, you'll need to convert the tiemstamps yourself. See the `Knack._convert_timestamps` method in the source code for help.

#### Setting your timezone

Use the `tzinfo` parameter to specify your applications timezone setting. This value should be formatted as a timezone string compliant to the [tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
 
```python
>>> kn = Knack(
      obj='object_1',
      app_id='abc123',
      api_key='topsecretapikey',
      tzinfo="US/Central" # Be careful, this is the default value!
    )
```

### Timeouts and Retrying

By default, knackpy will attempt to send an HTTP request to the Knack API 5 times until a status code of `200` is returned. You can adjust the number of request attempts (`max_attempts`, default=`5`) and the timeout (`timeout`, default=`10`):

```python
>>> kn = Knack(
      obj='object_1',
      app_id='abc123',
      api_key='topsecretapikey',
      max_attempts=4,
      timeout=20,
      tzinfo="US/Central" # Be careful, this is the default value!
    )
```

### Connection Fields

By default, connection fields are (if one connection) returned as the field's display name, or (if many connetions) an array of the connection fields' display names.

Use `raw_connections=True` to retain the entire connection array from Knack:

```python
[
  {
    "id": "5a7a027b82fecf67ab01f263", # Record ID of connected record
    "identifier": "Pizza Hut" # This the value of the connection's display name field
  }
],
```

### Knack Record ID's

By default, the Knack record ID is included within each record under the `id` key. This can create problems if you have a field named `id` in our object. You can exclude the record IDs entirely with `include_ids=False` or set your own ID key with `id_key="your_field_id"`. 

## License

As a work of the City of Austin, this project is in the public domain within the United States.

Additionally, we waive copyright and related rights of the work worldwide through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
