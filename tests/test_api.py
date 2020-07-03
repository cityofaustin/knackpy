import json
import os

import knackpy
import requests
import pytest

APP_ID = os.environ['KNACK_APP_ID']
API_KEY = os.environ['KNACK_API_KEY']

@pytest.fixture
def app_data():
    with open("tests/_metadata.json", "r") as fin:
        metadata = json.loads(fin.read())

    with open("tests/_all_fields.json", "r") as fin:
        data = json.loads(fin.read())
        data = data["records"]

    return {"data": data, "metadata": metadata}


def test_record_create(app_data):
    assert knackpy.api.record(
        method="create", app_id=APP_ID, api_key=API_KEY, data={}, obj="object_3"
    )
