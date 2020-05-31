from datetime import datetime, timezone
import pdb

def default(value):
    """ Handles types:
    - auto_increment
    - average
    - boolean
    - concatenation
    - connection
    - count
    - currency
    - file
    - id  x
    - multiple_choice  x
    - name  x
    - number 
    - password
    - rating
    - rich_text
    - short_text  x
    - signature
    - sum
    - timer  x
    - user_roles
    """
    return value

def email(value):
    return value.get("email")

def link(value):
    return value.get("url")

def phone(value):
    return value.get("full")

def image(value):
    # somtimes a dict, sometimes a str
    try:
        return value["url"]
    except TypeError:
        return value

def date_time(value, tz):
    mills_timestamp = value.get("unix_timestamp")
    timestamp = mills_timestamp / 1000
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.astimezone(tz).isoformat()