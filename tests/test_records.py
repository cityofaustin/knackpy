import json
import types

import knackpy
import pytest

KEY = "all_fields_test"


@pytest.fixture
def app():

    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())
        metadata = metadata["application"]

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    app = knackpy.App(app_id=metadata["id"], metadata=metadata)
    app.data = {KEY: data}
    return app


@pytest.fixture
def records(app):
    return knackpy._records.Records(app.data, app.field_defs)


def test_constructor_success(app):
    assert knackpy._records.Records(app.data, app.field_defs)


def test_constructor_fail(app):
    with pytest.raises(TypeError):
        knackpy._records.Records()


def test_get(records):
    recs = records.get(KEY)
    assert isinstance(recs, types.GeneratorType)


def test_handle_records(app, records):
    record = app.data[KEY][0]
    handled = records._handle_record(record, False, False)
    assert isinstance(handled, dict)


def test_handle_records_no_format_keys(app, records):
    record = app.data[KEY][0]
    handled = records._handle_record(record, False, False)
    assert set(record.keys()).issuperset(set(handled.keys()))


def test_handle_records_format_keys(app, records):
    record = app.data[KEY][0]
    fieldnames = [value.name for key, value in app.field_defs.items()]
    handled = records._handle_record(record, True, False)
    handled.pop("_id")  # ignore conflict-resovled `id` fieldname
    assert set(fieldnames).issuperset(set(handled.keys()))


def test_handle_records_no_format_values(app, records):
    record = app.data[KEY][0]
    record_vals = record.values()
    handled_vals = records._handle_record(record, False, False).values()
    assert all([val in record_vals for val in handled_vals])


def test_handle_records_no_format(app, records):
    record = app.data[KEY][0]
    record_vals = record.values()
    handled_vals = records._handle_record(record, False, False).values()
    assert all([val in record_vals for val in handled_vals])
