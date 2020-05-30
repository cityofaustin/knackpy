import json
import types

import knackpy
import pytest

@pytest.fixture
def field_data():
    return {
        "_id": "abc123",
        "key": "field_99",
        "name": "Fake Field",
        "type": ("short_text"),
    }

def drop_key_from_dict(d, key):
    d = d.copy()
    d.pop(key)
    return d

def test_constructor_success(field_data):
    assert knackpy._fields.FieldDef(**field_data)

def test_constructor_fail_missing_required(field_data):
    bad_data = drop_key_from_dict(field_data, "_id")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)

    bad_data = drop_key_from_dict(field_data, "key")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)
    
    bad_data = drop_key_from_dict(field_data, "type")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)

    bad_data = drop_key_from_dict(field_data, "name")
    with pytest.raises(knackpy.exceptions.exceptions.ValidationError):
        assert knackpy._fields.FieldDef(**bad_data)