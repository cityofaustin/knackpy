import json
import types
import pytest
import knackpy
import types

@pytest.fixture
def app_data():
    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())
        metadata = metadata["application"]

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    return {"data": data, "metadata": metadata}


@pytest.fixture
def app(app_data):
    knackpy_app = knackpy.App(app_id=app_data["metadata"]["id"], metadata=app_data["metadata"])
    app.data = {"all_fields_test": app_data["data"]}
    return knackpy_app


def test_constructor_success(app_data):
    app = knackpy.App(app_id=app_data["metadata"]["id"], metadata=app_data["metadata"])
    assert app


def test_constructor_fail_missing_app_id(app, app_data):
    with pytest.raises(TypeError):
        knackpy.App()

def test_get_by_key(app_data):
    app = knackpy.App(app_id=app_data["metadata"]["id"], metadata=app_data["metadata"])
    # to side-load records, data[<key>] must exist in the app's container index (ie, it has to exist in the app's metadata)
    app.data["object_3"] = app_data["data"]
    assert type(app.records("object_3")) == types.GeneratorType

def test_get_by_name(app_data):
    app = knackpy.App(app_id=app_data["metadata"]["id"], metadata=app_data["metadata"])
    # to side-load records, data[<key>] must exist in the app's container index (ie, it has to exist in the app's metadata)
    app.data["object_3"] = app_data["data"]
    assert type(app.records("all_fields_test")) == types.GeneratorType


def test_tzinfo(app_data):
    assert knackpy.App(
        app_id=app_data["metadata"]["id"],
        metadata=app_data["metadata"],
        tzinfo="US/Eastern",
    )
