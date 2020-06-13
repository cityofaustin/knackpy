import json
import types

import knackpy
import pytest
import pytz


@pytest.fixture
def metadata():
    with open("tests/_metadata.json", "r") as fin:
        return json.loads(fin.read())


@pytest.fixture
def field_def_data():
    return {
        "_id": "abc123",
        "key": "field_99",
        "name": "Fake Field",
        "type_": "short_text",
        "object": "object_3",
    }


@pytest.fixture
def record_data():
    return {
        "date_time": {
            "am_pm": "PM",
            "date": "09/11/2019",
            "date_formatted": "09/11/2019",
            "hours": "04",
            "iso_timestamp": "2019-09-11T16:14:00.000Z",
            "minutes": "14",
            "time": 974,
            "timestamp": "09/11/2019 04:14 pm",
            "unix_timestamp": 1568218440000,
        }
    }


@pytest.fixture
def field_defs(metadata):
    return knackpy._fields.generate_field_defs(metadata)


def drop_key_from_dict(d, key):
    d = d.copy()
    d.pop(key)
    return d


def test_constructor_success(field_def_data):
    assert knackpy._fields.FieldDef(**field_def_data)


def test_constructor_fail_missing_required(field_def_data):
    bad_data = drop_key_from_dict(field_def_data, "_id")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)

    bad_data = drop_key_from_dict(field_def_data, "key")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)

    bad_data = drop_key_from_dict(field_def_data, "type_")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)

    bad_data = drop_key_from_dict(field_def_data, "name")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)


def test_generate_field_defs(metadata):
    field_defs = knackpy._fields.generate_field_defs(metadata)
    assert len(list(field_defs.keys())) > 0


def test_set_field_def_views(field_defs, metadata):
    field_defs = knackpy._fields.set_field_def_views(field_defs, metadata)
    assert len(field_defs["field_11"].views) > 0
