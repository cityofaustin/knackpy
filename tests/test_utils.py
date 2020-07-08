import json

import knackpy
import pytz
import pytest


@pytest.fixture
def timezone():
    return pytz.timezone("US/Central")


@pytest.fixture
def metadata():
    with open("tests/_metadata.json", "r") as fin:
        meta = json.loads(fin.read())
        return meta["application"]


def test_valid_name():
    assert knackpy.utils.valid_name("id") == "_id"


def test_correct_knack_timestamp(timezone):
    """
    **Timestamp outside of daylight savings time**

    Given `1577893645000`:
    UTC: Wednesday, January 1, 2020 3:47:25 PM
    US/Central: Wednesday, January 1, 2020 9:47:25 AM GMT-06:00

    We are targeting: `1593636445000`
    GMT: Wednesday, January 1, 2020 9:47:25 PM
    US/Central: Wednesday, January 1, 2020 3:47:25 PM GMT-06:00
    """
    timestamp_input = 1577893645000
    timestamp_output = knackpy.utils.correct_knack_timestamp(timestamp_input, timezone)
    assert timestamp_output == 1577915245000


def test_correct_knack_timestamp_during_dst(timezone):
    """
    **Timestamp during daylight savings time**

    Given `1593618445000`:
    UTC: Wednesday, July 1, 2020 3:47:25 PM
    US/Central: 10:47:25 AM GMT-05:00 DST

    We are targeting: `1593636445000`
    UTC: Wednesday, July 1, 2020 8:47:25 PM
    US/Central 3:47:25 PM GMT-05:00 DST
    """
    timestamp_input = 1593618445000
    timestamp_output = knackpy.utils.correct_knack_timestamp(timestamp_input, timezone)
    assert timestamp_output == 1593636445000


def test_generate_containers(metadata):
    containers = knackpy.utils.generate_containers(metadata)
    assert len(containers) > 0


def test_humanize_bytes():
    kb = knackpy.utils.humanize_bytes(1000000)
    assert kb == "976.56kb"
    mb = knackpy.utils.humanize_bytes(10000000)
    assert mb == "9.54mb"
    gb = knackpy.utils.humanize_bytes(10000000000)
    assert gb == "9.31gb"
