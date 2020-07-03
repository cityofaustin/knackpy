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
    return knackpy._records.Records(
        "object_3", app.data[KEY], app.field_defs, app.timezone
    )


def test_basic_constructor(app, records):
    assert len([record for record in records.records()]) == len(app.data[KEY])


def test_format_record(app, records):
    assert len([record.format() for record in records.records()]) == len(app.data[KEY])
