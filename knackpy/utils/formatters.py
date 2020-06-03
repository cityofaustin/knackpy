import datetime
import pdb


def default(value):
    """ Handles types:
    - address x
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
    - sum
    - user_roles
    """
    return value


def signature(value):
    return value.get("base30")


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


def date_time(value, timezone=None):
    mills_timestamp = value.get("unix_timestamp")
    timestamp = mills_timestamp / 1000
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    return dt.astimezone(timezone).isoformat()


def timer(value):
    # we're handling somthing that looks like this: '<span>09/11/19</span>&nbsp;4:14pm to 5:14pm = 1:00 hours'
    return value.replace("<span>", "").replace("</span>", "").replace("&nbsp;", "; ")
