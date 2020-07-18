import json
import types

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
    field_defs = [field_def for field_def in app.field_defs if field_def.obj == OBJ_KEY]
    return knackpy.records.records(app.data[OBJ_KEY], field_defs, app.timezone)


@pytest.fixture
def generate_records(app):
    field_defs = [field_def for field_def in app.field_defs if field_def.obj == OBJ_KEY]
    return knackpy.records.generate_records(app.data[OBJ_KEY], field_defs, app.timezone)


def test_records(records):
    assert records


def test_generate_records(generate_records):
    assert isinstance(generate_records, types.GeneratorType)

