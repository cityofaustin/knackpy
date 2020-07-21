import json

import knackpy
import pytest

OBJ_KEY = "object_3"
FIELD_TO_FORMAT = {"key": "field_127", "name": "address_international_with_country"}
FIELD_TO_NOT_FORMAT = {"key": "field_126", "name": "address_international"}


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


def test_format_record_keys_values_default(app, records):
    assert records[0].format()


def test_format_record_values_only(app, records):
    record = records[0].format(keys=False)
    assert FIELD_TO_FORMAT["key"] in record and isinstance(
        record[FIELD_TO_FORMAT["key"]], str
    )


def test_format_record_keys_only(app, records):
    record = records[0].format(values=False)
    assert FIELD_TO_FORMAT["name"] in record and isinstance(
        record[FIELD_TO_FORMAT["name"]], dict
    )


def test_format_record_key_list(app, records):
    record = records[0].format(keys=[FIELD_TO_FORMAT["key"]])
    assert (
        FIELD_TO_FORMAT["name"] in record and FIELD_TO_NOT_FORMAT["name"] not in record
    )


def test_format_record_value_list(app, records):
    record = records[0].format(values=[FIELD_TO_FORMAT["key"]], keys=False)
    assert isinstance(record[FIELD_TO_FORMAT["key"]], str) and isinstance(
        record[FIELD_TO_NOT_FORMAT["key"]], dict
    )


def test_names(records):
    record = records[0]
    field_names = record.names()
    assert len(field_names) > 0


def test_keys(records):
    # this is a custom .keys() method; hence the test
    record = records[0]
    keys = record.keys()
    assert len(keys) > 0


def test_get_by_name(records):
    record = records[0]
    field_name = record.names()[0]
    assert record[field_name]


def test_get_by_key(records):
    # this is a custom __getitem__; hence the test
    record = records[0]
    key = record.keys()[0]
    assert record[key]


def test_unifom_length(records):
    # all records should have the same number of fields
    # one per field def
    for record in records:
        assert len(record.field_defs) == len(record.fields)
