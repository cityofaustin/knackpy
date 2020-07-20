import os
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

UPLOAD_CONFIG = {
    "path": "tests/plaid.jpg",
    "obj": OBJ,
    "file_field": "field_17",
    "image_field": "field_18",
}


@pytest.fixture
def records():
    time.sleep(0.5)
    return knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ, record_limit=1)


def test_random_pause():
    knackpy.api._random_pause()
    assert True


def test_upload_file_create_update_delete_record():
    """
    Yes, this is three tests in one. Create a record with a new file. Update the
    record with another file (ok, well, technically the same file), delete that
    record.
    """
    path = UPLOAD_CONFIG["path"]
    field = UPLOAD_CONFIG["file_field"]
    obj = UPLOAD_CONFIG["obj"]
    # create
    record1 = knackpy.api.upload(
        app_id=APP_ID,
        api_key=API_KEY,
        obj=obj,
        asset_type="file",
        path=path,
        field=field,
    )
    assert record1
    time.sleep(0.5)
    # update
    record2 = knackpy.api.upload(
        app_id=APP_ID,
        api_key=API_KEY,
        record_id=record1["id"],
        obj=obj,
        asset_type="file",
        path=path,
        field=field,
    )
    # verify a new record was not created
    assert record1["id"] == record2["id"]
    time.sleep(0.5)
    # delete
    response = knackpy.api.record(
        method="delete",
        app_id=APP_ID,
        api_key=API_KEY,
        data={"id": record2["id"]},
        obj=OBJ,
    )
    assert response["delete"]


def test_upload_image_create_update_delete_record():
    """
    Yes, this is three tests in one. Create a record with a new image. Update the
    record with another image (ok, well, technically the same image), delete that
    record.
    """
    path = UPLOAD_CONFIG["path"]
    field = UPLOAD_CONFIG["image_field"]
    obj = UPLOAD_CONFIG["obj"]
    # create
    record1 = knackpy.api.upload(
        app_id=APP_ID,
        api_key=API_KEY,
        obj=obj,
        asset_type="image",
        path=path,
        field=field,
    )
    assert record1
    time.sleep(0.5)
    # update
    record2 = knackpy.api.upload(
        app_id=APP_ID,
        api_key=API_KEY,
        record_id=record1["id"],
        obj=obj,
        asset_type="image",
        path=path,
        field=field,
    )
    assert record1["id"] == record2["id"]
    time.sleep(0.5)
    # delete
    response = knackpy.api.record(
        method="delete",
        app_id=APP_ID,
        api_key=API_KEY,
        data={"id": record2["id"]},
        obj=OBJ,
    )
    assert response["delete"]


def test_get_limit(records):
    assert len(records) == 1


def test_get_no_limit():
    time.sleep(0.5)
    records = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ)
    assert len(records) > 1


def test_get_filters():
    time.sleep(0.5)
    records = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, obj=OBJ, filters=FILTERS)
    assert len(records) == 1


def test_record_create_delete():
    # yes, two tests in one :/
    time.sleep(0.5)
    new_record = knackpy.api.record(
        method="create", app_id=APP_ID, api_key=API_KEY, data={}, obj=OBJ
    )
    assert new_record
    time.sleep(0.5)
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


def test_slug_param():
    time.sleep(0.5)
    assert knackpy.api.get_metadata(app_id=APP_ID, slug="atd")
