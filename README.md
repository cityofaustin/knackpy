# Knackpy 

A Python client for interacting with [Knack](http://knack.com) applications.

## Installation

```
pip install git+git://github.com/cityofaustin/knack-py.git
```

Knackpy requires [Arrow](http://arrow.readthedocs.io/en/latest/) and [Requests](http://docs.python-requests.org/en/master/). ```pip``` will install both dependencies automatically.

## Features
- Supports Python 2.7 and 3.5
- Object and view-based requests
- Filters
- Parsing of fieldnames and field labels
- Datetime localization
- CSV output

## Example

```python
from knackpy import Knack

>>> kn = Knack(
    scene='scene_34',
    view='view_10',
    ref_obj=['object_1', 'object_2'],
    app_id='abc123',
    api_key='topsecretapikey'
)

>>> kn.data
[{'store_id': 30424, 'inspection_date': 1479448800000, 'id': '58598262bcb3437b51194040'},...]

>>> kn.data_raw
['field_1': 30424, 'field_1_raw': 30424, 'field_2': '11/18/2016',...]

>>> kn.fields
{'field_1': {'label': 'store_id', 'key': 'field_1,required': False, 'type': 'auto_increment'},...}

>>> kn.fieldnames
{'store_id', 'inspection_date', 'store_status',...}

>>>kn.to_csv('data.csv')
"store_id","inspection_date","store_status"
"30424","11-18-2016","OPEN"
"30200","10-01-2013","CLOSED"
...
```

## License

As a work of the City of Austin, this project is in the public domain within the United States.

Additionally, we waive copyright and related rights of the work worldwide through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).

