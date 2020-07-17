import json

import knackpy
import pytest

KEY = "all_fields_test"


@pytest.fixture
def app():
    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    app = knackpy.App(app_id=metadata["application"]["id"], metadata=metadata)
    app.data = {KEY: data}
    return app


@pytest.fixture
def records(app):
    return knackpy.records.Records(
        "object_3", app.data[KEY], app.field_defs, app.timezone
    )


def test_basic_constructor(app, records):
    assert len([record for record in records.records()]) == len(app.data[KEY])


def test_record_repr(records):
    assert [repr(record) for record in records.records()]


def test_records_repr(records):
    assert repr(records)


def test_format_record(app, records):
    assert len([record.format() for record in records.records()]) == len(app.data[KEY])


def test_names(records):
    record = next(records.records())
    field_names = record.names()
    assert len(field_names) > 0


def test_keys(records):
    # this is a custom .keys() method; hence the test
    record = next(records.records())
    keys = record.keys()
    assert len(keys) > 0


def get_by_name(records):
    record = next(records.records())
    field_name = record.names()[0]
    assert record[field_name]


def get_by_key(records):
    # this is a custom __getitem__; hence the test
    record = next(records.records())
    key = record.keys()[0]
    assert record[key]
