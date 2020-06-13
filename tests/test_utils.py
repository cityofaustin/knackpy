import json
import pytest

import pytz

import knackpy


@pytest.fixture
def metadata():
    with open("tests/_metadata.json", "r") as fin:
        return json.loads(fin.read())


@pytest.fixture
def app(metadata):
    return knackpy.App(app_id=metadata["id"], metadata=metadata)


@pytest.fixture
def container_index(metadata):
    return knackpy.utils.utils.generate_container_index(metadata)


def test_query_container_index_by_obj_key(container_index):
    assert container_index["object_3"]


def test_query_container_index_by_obj_name(container_index):
    assert container_index["all_fields_test"]


def test_query_container_index_by_view_key(container_index):
    assert container_index["view_1"]


def test_query_container_index_by_view_name(container_index):
    assert container_index["thing - many to many w/ parent"]


def test_query_container_has_conflicts(container_index):
    assert len(container_index["_conflicts"]) > 0


def test_query_container_index_keyerror(container_index):
    with pytest.raises(KeyError):
        assert container_index["Pizza the Hut"]

def test_correct_knack_timestamp():
    local_timestamp = 1568218440000  #  Sep 11, 2019 16:14pm UTC
    tz = pytz.timezone("US/Central")
    unix_timestamp = knackpy.utils.utils.correct_knack_timestamp(local_timestamp, tz)
    assert unix_timestamp ==  1568236440000 # Sep 11, 2019 16:14pm US/Central