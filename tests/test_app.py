import json
import types
import os

import knackpy
import requests
import pytest


APP_ID = os.environ["KNACK_APP_ID"]
API_KEY = os.environ["KNACK_API_KEY"]
FILTERS = {
    "match": "or",
    "rules": [
        # field_125 is name: "id", type: short text
        {"field": "field_125", "operator": "is", "value": "1"},
    ],
}


@pytest.fixture
def app_data():
    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    return {"data": data, "metadata": metadata}


@pytest.fixture
def app_static(app_data):
    # app with side-loaded metadata and records
    knackpy_app = knackpy.app.App(
        app_id=app_data["metadata"]["application"]["id"], metadata=app_data["metadata"]
    )
    knackpy_app.data = {"object_3": app_data["data"]}
    return knackpy_app


@pytest.fixture
def app_live():
    # testing on live app (as in over-the-wire data fetch, not side-loaded)
    return knackpy.app.App(app_id=APP_ID, api_key=API_KEY)


def test_basic_over_the_wire_construction(app_live):
    assert app_live


def test_basic_static_app_construction(app_static):
    assert app_static


def test_constructor_fail_missing_app_id(app_static):
    with pytest.raises(TypeError):
        knackpy.app.App()


def test_get_by_key_static(app_static):
    assert isinstance(app_static.records("object_3"), types.GeneratorType)


def test_get_by_key_live(app_live):
    assert isinstance(app_live.records("object_3"), types.GeneratorType)


def test_get_by_key_refresh(app_live):
    records = app_live.records("object_3")
    records = app_live.records("object_3", refresh=True)
    assert [record for record in records]


def test_no_api_key_get(app_static):
    # our static app has been constructed w/o an API key, so object-based requests
    # should fail with an HTTPError
    with pytest.raises(requests.exceptions.HTTPError):
        app_static.records("object_3", refresh=True)


def test_get_with_filters(app_live):
    records = app_live.records("object_3", filters=FILTERS)
    assert len([record for record in records]) == 1


def test_get_by_dupe_name_fail(app_static):
    # the "all_fields_test" container name exists in our app as both an object
    # and as a view. so trying to query by that name results in a KeyError.
    with pytest.raises(ValueError):
        assert isinstance(app_static.records("all_fields_test"), types.GeneratorType)


def test_valid_tzinfo(app_data):
    assert knackpy.app.App(
        app_id=app_data["metadata"]["application"]["id"],
        metadata=app_data["metadata"],
        tzinfo="US/Eastern",
    )


def test_invalid_tzinfo(app_data):
    with pytest.raises(ValueError):
        assert knackpy.app.App(
            app_id=app_data["metadata"]["application"]["id"],
            metadata=app_data["metadata"],
            tzinfo="Austin, Texas",
        )


def test_info(app_static):
    assert isinstance(app_static.info(), dict)
