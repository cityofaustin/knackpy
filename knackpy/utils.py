import collections
import datetime
import math


def valid_name(key):
    # TODO: subfield conflicts?
    RESERVED_NAMES = ["id"]
    if key in RESERVED_NAMES:
        return f"_{key}"
    else:
        return key


def generate_containers(metadata):
    """Returns a dict of knack object keys, object names, view keys, and view names,
        that serves as lookup for finding Knack app record containers (objects
        or views) by name or key.

        Note that namespace conflicts are highlighly likely, especially with
        views, whose default name in Knack is their parent object!

        If an app has object names that conflict with view names, a `ValidationError`
        will raise when attempting to query data by that name.

        As such, the best practice is to use keys (object_xx or view_xx) as
        much as possible, especially when fetching data from views.
        """

    Container = collections.namedtuple("Container", "obj view scene name")

    obj_containers = [
        Container(obj=obj["key"], scene=None, view=None, name=obj["name"])
        for obj in metadata["objects"]
    ]

    view_containers = [
        Container(obj=None, view=view["key"], scene=scene["key"], name=view["name"])
        for scene in metadata["scenes"]
        for view in scene["views"]
    ]

    return obj_containers + view_containers


def correct_knack_timestamp(mills_timestamp, timezone):
    """You may be wondering why timezone settings are concern, given that
    Knackpy, like the Knack API, returns timestamp values as Unix timestamps in
    millesconds (thus, there is no timezone encoding at all). However, the Knack
    API confusingly returns millisecond timestamps in your localized timezone!

    For example, if you inspect a timezone value in Knack, e.g., 1578254700000,
    this value represents Sunday, January 5, 2020 8:05:00 PM **local time**.

    Args: mills_timestamp ([int]): the Knack "local" timestamp, in milliseonds
        timezone ([pytz.timezone]): pytz timezone object

    Returns: [int]: a real UTC timestamp
    """
    timestamp = mills_timestamp / 1000
    # Don't use datetime.utcfromtimestamp()! this will assume the input
    # timestamp is in local (system) time If you try to pass our timezone to
    # the tz parameter here, it will have no affect.
    dt_utc = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    # All we've done so far is create a datetime object from our timestamp
    # now we have to remove the timezone info that we supplied
    dt_naive = dt_utc.replace(tzinfo=None)
    # Now we localize (i.e., translate) the datetime object to our local time
    # you cannot use datetime.replace() here, because it does not account for
    # daylight savings time. I know, this is completely insane.
    dt_local = timezone.localize(dt_naive)
    # Now we can convert our datetime object back to a timestamp
    unix_timestamp = dt_local.timestamp()
    # And add milliseconds
    return int(unix_timestamp * 1000)


def humanize_bytes(bytes_):
    # courtesy of https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python # noqa
    if bytes_ == 0:
        return "0B"
    size_name = ("b", "kb", "mb", "gb", "tb", "pb", "eb", "zb", "yb")
    i = int(math.floor(math.log(bytes_, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_ / p, 2)
    return f"{s}{size_name[i]}"
