
from knackpy import *
from secrets import app_id, api_key

apps = [
    {   
        #  view-based request with api_key
        'scene' : 'scene_467',
        'view' : 'view_1329',
        'field_obj' : ['object_31'],
        'app_id' : app_id,
        'api_key' : api_key,
        'page_limit' : 1,
        'rows_per_page' : 10
    },
    {   
        #  view-based request without api_key
        'scene' : 'scene_467',
        'view' : 'view_1329',
        'field_obj' : ['object_31'],
        'app_id' : app_id,
        'page_limit' : 1,
        'rows_per_page' : 10
    },
    {   
        #  object-based request
        'obj' : 'object_31',
        'app_id' : app_id,
        'api_key' : api_key,
        'page_limit' : 1,
        'rows_per_page' : 10
    }

]

app = apps[0]
#  view-based request with api_key
kn = Knack(
    scene=app['scene'],
    view=app['view'],
    field_obj=app['field_obj'],
    app_id=app['app_id'],
    api_key=app['api_key'],
    page_limit=1,
    rows_per_page=10
)

if not kn.data:
    raise Exception("No data rerieved for view-based request with api_key")

if len(kn.data) > 10:
    raise Exception("More records retrieved than expected")

if not kn.fields:
    raise Exception("No fields rerieved view-based request with api_key")

if not kn.field_map:
    raise Exception("No field_map created for view-based request with api_key")



