import os

import knackpy
import pytest

APP_ID = os.environ["KNACK_APP_ID"]
API_KEY = os.environ["KNACK_API_KEY"]
OBJ = "object_3"  # "all_fields_test"
UPDATE_KEY = "field_25"  # rating field type


@pytest.fixture
def record():
    return knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ, record_limit=1)[0]


def test_get_limit():
    records = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ, record_limit=1)
    assert len(records) == 1


def test_record_create_delete():
    # yes, two tests in one :/
    new_record = knackpy.api.record(
        method="create", app_id=APP_ID, api_key=API_KEY, data={}, obj=OBJ
    )
    assert new_record

    response = knackpy.api.record(
        method="delete",
        app_id=APP_ID,
        api_key=API_KEY,
        data={"id": new_record["id"]},
        obj=OBJ,
    )
    assert response["delete"]


def test_record_update(record):
    update_value = "0.00" if record[UPDATE_KEY] != "0.00" else "1.00"
    data = {"id": record["id"], UPDATE_KEY: update_value}
    record_updated = knackpy.api.record(
        method="update", app_id=APP_ID, api_key=API_KEY, data=data, obj=OBJ
    )
    assert record_updated[UPDATE_KEY] == update_value


def test_get_metadata():
    metadata = knackpy.api.get_metadata(app_id=APP_ID)
    assert metadata["application"]
