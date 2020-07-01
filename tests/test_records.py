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
    return knackpy._records.Records(
        "object_3", app.data[KEY], app.field_defs, app.timezone
    )


def test_constructor_success(app):
    assert knackpy._records.Records(
        "object_3", app.data[KEY], app.field_defs, app.timezone
    )


def test_constructor_fail(app):
    with pytest.raises(TypeError):
        knackpy._records.Records()


def test_get(records):
    recs = records.records()
    assert isinstance(recs, types.GeneratorType)
