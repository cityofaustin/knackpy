import knackpy
import pytest
import pytz


@pytest.fixture
def field_def_data():
    return {
        "_id": "abc123",
        "key": "field_99",
        "name": "Fake Field",
        "type": ("short_text"),
        "object": "object_0",
    }


@pytest.fixture
def record_data():
    return {
        "date_time": {
            "am_pm": "PM",
            "date": "09/11/2019",
            "date_formatted": "09/11/2019",
            "hours": "04",
            "iso_timestamp": "2019-09-11T16:14:00.000Z",
            "minutes": "14",
            "time": 974,
            "timestamp": "09/11/2019 04:14 pm",
            "unix_timestamp": 1568218440000,
        }
    }


def drop_key_from_dict(d, key):
    d = d.copy()
    d.pop(key)
    return d


def test_constructor_success(field_def_data):
    assert knackpy.fields.FieldDef(**field_def_data)


def test_constructor_fail_missing_required(field_def_data):
    bad_data = drop_key_from_dict(field_def_data, "object")
    with pytest.raises(KeyError):
        assert knackpy.fields.FieldDef(**bad_data)


def test_correct_knack_timestamp(record_data):
    local_timestamp = 1568218440000  # Sep 11, 2019 16:14pm UTC
    tz = pytz.timezone("US/Central")
    unix_timestamp = knackpy.utils.correct_knack_timestamp(local_timestamp, tz)
    assert unix_timestamp == 1568236440000  # Sep 11, 2019 16:14pm US/Central


def test_format_date_time(record_data):
    """ note that this timestamp is not corrected, we're just assuming it's a valid
    unix timestamp,
    - input:  1568218440000 Sep 11, 2019 16:14pm UTC
    """
    knack_date_time_dict = record_data["date_time"]
    timezone = pytz.timezone("US/Central")
    date_iso_formatted = knackpy.formatters.date_time(knack_date_time_dict, timezone)
    assert date_iso_formatted == "2019-09-11T11:14:00-05:00"


def test_format_address(record_data):
    """ note that this timestamp is not corrected, we're just assuming it's a valid
    unix timestamp.
        - input:  1568218440000 Sep 11, 2019 16:14pm UTC
    """
    knack_date_time_dict = record_data["date_time"]
    timezone = pytz.timezone("US/Central")
    date_iso_formatted = knackpy.formatters.date_time(knack_date_time_dict, timezone)
    assert date_iso_formatted == "2019-09-11T11:14:00-05:00"
