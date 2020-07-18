import json
import os
import random
import time
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

OBJ = "object_3"
UPDATE_KEY = "field_25"  # rating field type


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
    knackpy_app.data = {OBJ: app_data["data"]}
    return knackpy_app


@pytest.fixture
def app_live():
    # testing on live app (as in over-the-wire data fetch, not side-loaded)
    return knackpy.app.App(app_id=APP_ID, api_key=API_KEY)


@pytest.fixture
def random_pause():
    """sleep for at least .333 seconds"""
    seconds = random.randrange(3, 10, 1)
    time.sleep(seconds / 10)


def test_record_update(app_static, app_live):
    """
    Given the first record in our static data, update one value and validate the
    updated data returned in the response.
    """
    record = dict(app_static.get(OBJ)[0])
    update_value = "0.00" if record[UPDATE_KEY] != "0.00" else "1.00"
    data = {"id": record["id"], UPDATE_KEY: update_value}
    record_updated = app_live.record(method="update", data=data, obj=OBJ)
    assert record_updated[UPDATE_KEY] == update_value


def test_record_create_delete(app_live, random_pause):
    # yes, two tests in one :/
    random_pause
    new_record = app_live.record(method="create", data={}, obj=OBJ)
    assert new_record
    random_pause
    response = app_live.record(method="delete", data={"id": new_record["id"]}, obj=OBJ,)
    assert response["delete"]


def test_basic_over_the_wire_construction(app_live):
    assert app_live


def test_over_the_wire_construction_with_slug(app_live):
    assert knackpy.app.App(app_id=APP_ID, api_key=API_KEY, slug="atd")


def test_basic_static_app_construction(app_static):
    assert app_static


def test_app_repr(app_static):
    assert repr(app_static)


def test_constructor_fail_missing_app_id(app_static):
    with pytest.raises(TypeError):
        knackpy.app.App()


def test_object_get_by_key_static(app_static):
    assert app_static.get(OBJ)


def test_get_object_by_key_live(app_live):
    assert app_live.get(OBJ)


def test_view_by_key_static(app_static):
    assert app_static.get("view_11")


def test_get_view_by_key_live(app_live):
    assert app_live.get("view_11")


def test_get_view_by_name(app_live):
    assert app_live.get("view_11")


def test_get_by_key_refresh(app_live):
    records = app_live.get(OBJ, refresh=True)
    assert records


def test_generate_records_is_generator(app_static):
    assert isinstance(app_static.get(OBJ, generate=True), types.GeneratorType)


def test_generate_records(app_static):
    assert len([record for record in app_static.get(OBJ, generate=True)]) > 0


def test_get_obj_records_no_api_key_get(app_static):
    with pytest.raises(requests.exceptions.HTTPError):
        app_static.api_key = None
        app_static.get(OBJ, refresh=True)


def test_get_object_records_with_filters(app_live):
    records = app_live.get(OBJ, filters=FILTERS)
    assert len(records) == 1


def test_get_view_records_with_filters(app_live):
    records = app_live.get("view_11", filters=FILTERS)
    assert len(records) == 1


def test_get_records_by_object_name(app_static):
    assert app_static.get("orders")


def test_get_records_by_view_name(app_static):
    assert app_static.get("all fields")


def test_no_key_or_name_param(app_static):
    # the API allows you to use App.reords() (without any key or view name) if only
    # one container has been retrieved. in this case, it's the sideloaded records in
    # object_3.
    assert app_static.get()


def test_no_key_or_name_param_fail(app_static):
    # the API allows you to use App.reords() (without any key or view name) if only
    # one container has been retrieved. in this case, we side-load additional data
    # such that the app is holding data for two containers, and so the user must
    # specifiy the container name or key
    data = app_static.data["object_3"]
    app_static.data["fake_data_holder"] = data
    with pytest.raises(TypeError):
        assert app_static.get()


def test_get_by_dupe_name_fail(app_static):
    # the "all_fields_test" container name exists in our app as both an object
    # and as a view. so trying to query by that name results in a KeyError.
    with pytest.raises(ValueError):
        assert isinstance(app_static.get("all_fields_test"), types.GeneratorType)


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
