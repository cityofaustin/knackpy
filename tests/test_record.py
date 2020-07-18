import json

import knackpy
import pytest

OBJ_KEY = "object_3"


@pytest.fixture
def app():
    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    app = knackpy.App(app_id=metadata["application"]["id"], metadata=metadata)
    app.data = {OBJ_KEY: data}
    return app


@pytest.fixture
def records(app):
    return app.get(OBJ_KEY)


def test_basic_constructor(app, records):
    assert len(records) == len(app.data[OBJ_KEY])


def test_record_repr(records):
    assert [repr(record) for record in records]


def test_format_record(app, records):
    assert len([record.format() for record in records]) == len(app.data[OBJ_KEY])


def test_names(records):
    record = records[0]
    field_names = record.names()
    assert len(field_names) > 0


def test_keys(records):
    # this is a custom .keys() method; hence the test
    record = records[0]
    keys = record.keys()
    assert len(keys) > 0


def get_by_name(records):
    record = records[0]
    field_name = record.names()[0]
    assert record[field_name]


def get_by_key(records):
    # this is a custom __getitem__; hence the test
    record = records[0]
    key = record.keys()[0]
    assert record[key]
