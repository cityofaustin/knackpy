import json
import pytest
import knackpy


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

def test_constructor_fail_missing_app_id():
    with pytest.raises(TypeError):
        knackpy.App()


def test_tzinfo_iana(app):
    assert knackpy.App.get_timezone("US/Central")


def test_tzinfo_common_name(app):
    assert knackpy.App.get_timezone("eastern time (us & canada)")


def test_bad_tzinfo(app):
    assert knackpy.App.get_timezone("US/Central")


