import os
import random
import time

import knackpy
import pytest

APP_ID = os.environ["KNACK_APP_ID"]
API_KEY = os.environ["KNACK_API_KEY"]
OBJ = "object_3"  # "all_fields_test"
UPDATE_KEY = "field_25"  # rating field type
FILTERS = {
    "match": "or",
    "rules": [
        # field_125 is name: "id", type: short text
        {"field": "field_125", "operator": "is", "value": "1"},
    ],
}


@pytest.fixture
def random_pause():
    seconds = random.randrange(1, 10, 1)
    time.sleep(seconds / 10)


@pytest.fixture
def records(random_pause):
    random_pause
    return knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ, record_limit=1)


def test_get_limit(records):
    assert len(records) == 1


def test_get_no_limit():
    random_pause
    records = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ)
    assert len(records) > 1


def test_get_filters():
    random_pause
    records = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ, filters=FILTERS)
    assert len(records) == 1


def test_record_create_delete():
    # yes, two tests in one :/
    random_pause
    new_record = knackpy.api.record(
        method="create", app_id=APP_ID, api_key=API_KEY, data={}, obj=OBJ
    )
    assert new_record
    random_pause
    response = knackpy.api.record(
        method="delete",
        app_id=APP_ID,
        api_key=API_KEY,
        data={"id": new_record["id"]},
        obj=OBJ,
    )
    assert response["delete"]


def test_record_update(records):
    """
    Given the first record in our static data, update one value and validate the
    updated data returned in the response.
    """
    record = records[0]
    update_value = "0.00" if record[UPDATE_KEY] != "0.00" else "1.00"
    data = {"id": record["id"], UPDATE_KEY: update_value}
    record_updated = knackpy.api.record(
        method="update", app_id=APP_ID, api_key=API_KEY, data=data, obj=OBJ
    )
    assert record_updated[UPDATE_KEY] == update_value


def test_get_metadata():
    metadata = knackpy.api.get_metadata(app_id=APP_ID)
    assert metadata["application"]
