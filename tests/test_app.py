import json
import pytest
import knackpy

@pytest.fixture
def app_data():
    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())
        metadata = metadata["application"]

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    return { "data": data, "metadata": metadata }

@pytest.fixture
def app(app_data):
    app = knackpy.App(app_id=app_data["metadata"]["id"], metadata=app_data["metadata"])
    app.data = {"all_fields_test": app_data["data"]}
    return app

def test_constructor_success(app_data):
    app = knackpy.App(app_id=app_data["metadata"]["id"], metadata=app_data["metadata"])
    assert app

def test_constructor_generate_records(app, app_data):
    app.generate_records()
    assert(app.records)

def test_constructor_fail_missing_app_id(app, app_data):
    with pytest.raises(TypeError):
        app = knackpy.App()