import json
import pytest
import knackpy

from knackpy.exceptions.exceptions import ValidationError

@pytest.fixture
def metadata():
    with open("tests/_metadata.json", "r") as fin:
        return json.loads(fin.read())


@pytest.fixture
def app(metadata):
    return knackpy.App(app_id=metadata["id"], metadata=metadata)

def test_app_info(app):
    assert app.info()["objects"] > 0
    assert app.info()["scenes"] > 0
    assert app.info()["records"] > 0
    assert app.info()["size"]

@pytest.fixture
def app(app_data):
    knackpy_app = knackpy.App(app_id=app_data["metadata"]["id"], metadata=app_data["metadata"])
    app.data = {"all_fields_test": app_data["data"]}
    return knackpy_app
    
def test_constructor_fail_missing_app_id():
    with pytest.raises(TypeError):
        knackpy.App()


def test_tzinfo_iana(app):
    assert knackpy.App.get_timezone("US/Central")


def test_tzinfo_common_name(app):
    assert knackpy.App.get_timezone("eastern time (us & canada)")


def test_bad_tzinfo(app):
    with pytest.raises(ValidationError):
        assert knackpy.App.get_timezone("Pizza the Hut")


