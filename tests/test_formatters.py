import pytest
import pytz

import knackpy


@pytest.fixture
def record():
    return {
        "address_field": {
            "street": "123 Fake St",
            "street2": "APT C",
            "city": "London",
            "state": "London",
            "zip": "ABC123",
            "country": "United Kingdom",
        },
        "date_time_field": {
            "am_pm": "PM",
            "date": "09/11/2019",
            "date_formatted": "09/11/2019",
            "hours": "04",
            "iso_timestamp": "2019-09-11T16:14:00.000Z",
            "minutes": "14",
            "time": 974,
            "timestamp": "09/11/2019 04:14 pm",
            "unix_timestamp": 1568218440000,
        },
        "signature_field": {
            "base30": "1W0023344484340Z5aaa67Y68acccf4527681Z5644Y899855Z14332Y36aa5Z333Y36d64Z5412Y25477h584Z4_2QZae7a87530Y15ocec9521Z234678d553100Y5564520Z3212Y464432Z2453Y643Z26c44Y66533Z32Y100Z1222_8Q00000_1vb9c96_8y66hc86Z26522000Y1w568432751_1W000000Z35554YfcmkZ203744Y3Z46_cH10000458556376643_1C66bd5Z43Y1010300Z332",  # noqa
            "svg": '<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="389" height="89"><path stroke-linejoin="round" stroke-linecap="round" stroke-width="2" stroke="rgb(85, 84, 89)" fill="none" d="M 10 65 c 0 -0.42 -0.92 -16.42 0 -24 c 0.68 -5.6 2.93 -11.47 5 -17 c 1.94 -5.16 4.42 -10.31 7 -15 c 1 -1.81 2.54 -3.54 4 -5 c 1.14 -1.14 2.67 -2.83 4 -3 c 3.21 -0.4 9.27 -0.09 12 1 c 1.32 0.53 2.58 3.25 3 5 c 1.76 7.29 3.11 15.98 4 24 c 0.44 3.95 0.71 8.33 0 12 c -0.88 4.55 -2.69 10 -5 14 c -2.43 4.21 -6.4 8.22 -10 12 c -3.1 3.25 -6.47 6.53 -10 9 c -2.93 2.05 -6.58 3.81 -10 5 c -4.08 1.42 -13.2 3.11 -13 3 c 0.39 -0.21 16.2 -5.43 24 -9 c 8.3 -3.81 15.99 -8.33 24 -13 c 4.23 -2.47 8.18 -5.03 12 -8 c 5.26 -4.09 10.33 -8.33 15 -13 c 4.01 -4.01 6.97 -11.24 11 -13 c 4.98 -2.18 17.03 -1.72 21 -1 c 0.96 0.17 1.73 3.99 1 5 c -3.92 5.45 -17.55 17.1 -19 20 c -0.43 0.87 5.36 1.69 8 2 c 2.88 0.34 6.21 0.62 9 0 c 8.74 -1.94 23.78 -7.5 27 -8 c 0.47 -0.07 -0.33 2.92 -1 4 c -3.38 5.46 -10.47 13.76 -12 17 c -0.27 0.56 2.14 2.18 3 2 c 4.09 -0.86 10.78 -3.64 16 -6 c 5.2 -2.35 13.85 -7.81 15 -8 c 0.45 -0.08 -1.77 4.22 -3 6 c -1.69 2.45 -6.13 7.1 -6 7 c 0.58 -0.47 31.19 -27.44 32 -28 c 0.29 -0.2 -6.72 8.12 -9 12 c -0.78 1.32 -0.45 3.54 -1 5 c -0.39 1.03 -2 2.21 -2 3 c 0 0.79 1.35 3.12 2 3 c 1.86 -0.34 6.23 -4.31 9 -5 c 1.9 -0.48 4.64 0.92 7 1 c 8.02 0.26 16.23 0.63 24 0 c 4.32 -0.35 8.86 -1.78 13 -3 c 1.39 -0.41 4 -1.54 4 -2 l -4 -2"/><path stroke-linejoin="round" stroke-linecap="round" stroke-width="2" stroke="rgb(85, 84, 89)" fill="none" d="M 214 14 l 0 47"/><path stroke-linejoin="round" stroke-linecap="round" stroke-width="2" stroke="rgb(85, 84, 89)" fill="none" d="M 196 41 c 0.96 0 48.99 0.34 55 0 c 0.39 -0.02 -1.18 -2.18 -2 -3 c -3.39 -3.39 -8.2 -6.46 -11 -10 c -1.85 -2.35 -3.95 -9.46 -4 -9 c -0.23 2.27 -4.89 38.45 0 49 c 3.77 8.12 23.67 15.95 32 20 c 1.19 0.58 3.37 -1.7 5 -2 c 1.82 -0.33 4.18 0.39 6 0 c 2.59 -0.56 6.39 -1.29 8 -3 c 3.31 -3.5 6.34 -13 9 -15 c 1.16 -0.87 5.26 3.15 7 3 c 1.47 -0.12 4.12 -2.53 5 -4 l 1 -6"/><path stroke-linejoin="round" stroke-linecap="round" stroke-width="2" stroke="rgb(85, 84, 89)" fill="none" d="M 325 21 c 0.02 0.1 0.95 3.98 1 6 c 0.28 11.6 -0.39 31.96 0 35 c 0.06 0.49 2.56 -2.88 4 -4 c 1.49 -1.16 3.37 -2.94 5 -3 c 6.75 -0.23 17.56 0.81 24 2 c 1.13 0.21 1.91 2.79 3 3 c 3.35 0.63 9.41 1.1 13 0 c 4.21 -1.3 13 -8 13 -8"/></svg>',  # noqa
        },
        "email_field": {"email": "pizzathehut@spaceballs.town"},
        "link_field": {"url": "http://spaceballs.town"},
        "phone_field": {
            "area": "512",
            "formatted": "(512) 974-3546",
            "full": "5129743546",
            "number": "9743546",
        },
        "image_field": {
            "application_id": "5d79512148c4af00106d1507",
            "field_key": "field_18",
            "filename": "my_car_mazda_q.jpg",
            "id": "5d7966ecc8d68e0010c0834a",
            "s3": True,
            "size": 1219841,
            "thumb_url": "spaceballs.town",
            "type": "image",
            "url": "spaceballs.town",
        },
        "file_field": {
            "application_id": "5d79512148c4af00106d1507",
            "field_key": "field_17",
            "filename": "ibmdesignthinkingfieldguidewatsonbuildv3.5_ac.pdf",
            "id": "5d796903335a510011275b67",
            "s3": True,
            "size": 8619743,
            "thumb_url": "",
            "type": "file",
            "url": "spaceballs.town",
        },
        "timer_field": "<span>09/11/19</span>&nbsp;4:35pm to 5:35pm = 1:00 hours",
    }


def test_default_handler():
    input_val = "hi how are you"
    output_val = knackpy.formatters.default(input_val)
    assert input_val == output_val


def test_signature(record):
    input_data = record["signature_field"]
    assert knackpy.formatters.signature(input_data)


def test_email(record):
    assert (
        knackpy.formatters.email(record["email_field"]) == "pizzathehut@spaceballs.town"
    )


def test_address(record):
    assert (
        knackpy.formatters.address(record["address_field"])
        == "123 Fake St, APT C, London, London, ABC123, United Kingdom"
    )


def test_link(record):
    assert knackpy.formatters.link(record["link_field"]) == "http://spaceballs.town"


def test_phone(record):
    assert knackpy.formatters.phone(record["phone_field"]) == "5129743546"


def test_image_with_url_key(record):
    assert knackpy.formatters.image(record["image_field"]) == "spaceballs.town"


def test_image_without_url_key(record):
    assert knackpy.formatters.image("spaceballs.town") == "spaceballs.town"


def test_file(record):
    assert knackpy.formatters.file(record["file_field"]) == "spaceballs.town"


def test_format_date_time(record):
    timezone = pytz.timezone("US/Central")
    iso_formatted = knackpy.formatters.date_time(record["date_time_field"], timezone)
    assert iso_formatted == "2019-09-11T11:14:00-05:00"


def test_timer(record):
    assert (
        knackpy.formatters.timer(record["timer_field"])
        == "09/11/19; 4:35pm to 5:35pm = 1:00 hours"
    )
