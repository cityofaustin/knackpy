import json
import os
import types

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
        app_id=app_data["metadata"]["application"]["id"],
        api_key=API_KEY,
        metadata=app_data["metadata"],
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


def test_object_get_by_key_static(app_static):
    assert isinstance(app_static.records("object_3"), types.GeneratorType)


def test_get_object_by_key_live(app_live):
    assert isinstance(app_live.records("object_3"), types.GeneratorType)


def test_view_by_key_static(app_static):
    assert isinstance(app_static.records("view_11"), types.GeneratorType)


def test_get_view_by_key_live(app_live):
    assert isinstance(app_live.records("view_11"), types.GeneratorType)


def test_get_view_by_name(app_live):
    assert isinstance(app_live.records("view_11"), types.GeneratorType)


def test_get_by_key_refresh(app_live):
    records = app_live.records("object_3")
    records = app_live.records("object_3", refresh=True)
    assert [record for record in records]


def test_no_api_key_get(app_static):
    with pytest.raises(requests.exceptions.HTTPError):
        app_static.api_key = None
        app_static.records("object_3", refresh=True)


def test_get_object_records_with_filters(app_live):
    records = app_live.records("object_3", filters=FILTERS)
    assert len([record for record in records]) == 1


def test_get_view_records_with_filters(app_live):
    records = app_live.records("view_11", filters=FILTERS)
    assert len([record for record in records]) == 1


def test_get_records_by_object_name(app_static):
    assert app_static.records("orders")


def test_get_records_by_view_name(app_static):
    assert app_static.records("all fields")


def test_no_key_or_name_param(app_static):
    # the API allows you to use App.reords() (without any key or view name) if only
    # one container has been retrieved. in this case, it's the sideloaded records in
    # object_3.
    assert app_static.records()

def test_no_key_or_name_param_fail(app_static):
    # the API allows you to use App.reords() (without any key or view name) if only
    # one container has been retrieved. in this case, we side-load additional data
    # such that the app is holding data for two containers, and so the user must
    # specifiy the container name or key
    data = app_static.data["object_3"]
    app_static.data["fake_data_holder"] = data
    with pytest.raises(TypeError):
        assert app_static.records()

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


def test_csv(app_static, tmpdir):
    app_static.to_csv("object_3", out_dir=tmpdir)
    assert os.path.exists(tmpdir / "object_3.csv")


def test_downloads(app_live, tmpdir):
    app_live.download(
        "object_3", field="file", out_dir=tmpdir, label_keys=["field_125"]
    )
    assert True
