import math

# courtesy of https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
def _humanize_bytes(bytes_):
    if bytes_ == 0:
        return "0B"
    size_name = ("b", "kb", "mb", "gb", "tb", "pb", "eb", "zb", "yb")
    i = int(math.floor(math.log(bytes_, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_ / p, 2)
    return f"{s}{size_name[i]}"


def _valid_name(key):
    RESERVED_NAMES = ["id"]
    if key in RESERVED_NAMES:
        return f"_{key}"
    else:
        return key
