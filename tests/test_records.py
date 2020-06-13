import json
import types

import knackpy
import pytest

OBJ_NAME_KEY = "all_fields_test"

@pytest.fixture
def app():
    """
    Records are not dependent on the App class, but App wraps a bunch of helpful methods
    that get us to the point of generating a record. So we use it as a fixture rather than 
    duplicating that code here.
    """
    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    app = knackpy.App(app_id=metadata["id"], metadata=metadata)
    app.data = {OBJ_NAME_KEY: data}
    return app

@pytest.fixture
def record(app):
    """
    You will notice elsewhere in the tests that we use a fixture that is identical
    to a unit test. i'm not sure how to gracefully accomplish this in tests:
    - test the basic construction of a class
    - test the public methods of a class
    """
    data = app.data.get(OBJ_NAME_KEY)[0]
    identifier = "field_6"
    field_defs = app.field_defs
    timezone = app.timezone
    return knackpy._records.Record(data, field_defs, identifier, timezone)

def test_record_constructor(app):
    data = app.data.get(OBJ_NAME_KEY)[0]
    identifier = "field_6"
    field_defs = app.field_defs
    timezone = app.timezone
    assert knackpy._records.Record(data, field_defs, identifier, timezone)

def test_record_format(record):
    assert record.format()
    
