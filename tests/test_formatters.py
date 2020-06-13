def test_format_date_time(record_data):
    """ note that this timestamp is not corrected, we're just assuming it's a valid unix timestamp"""
    # input:  1568218440000 Sep 11, 2019 16:14pm UTC
    knack_date_time_dict = record_data["date_time"]
    timezone = pytz.timezone("US/Central")
    date_iso_formatted = knackpy.utils.formatters.date_time(knack_date_time_dict, timezone)
    assert date_iso_formatted == "2019-09-11T11:14:00-05:00"

def test_format_address(record_data):
    """ note that this timestamp is not corrected, we're just assuming it's a valid unix timestamp"""
    # input:  1568218440000 Sep 11, 2019 16:14pm UTC
    knack_date_time_dict = record_data["date_time"]
    timezone = pytz.timezone("US/Central")
    date_iso_formatted = knackpy.utils.formatters.date_time(knack_date_time_dict, timezone)
    assert date_iso_formatted == "2019-09-11T11:14:00-05:00"