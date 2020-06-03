BASE_URL = "https://api.knack.com/v1/"
BASE_URL_METADATA = "https://loader.knack.com/v1"

FIELD_TYPE_SUBFIELDS = {
    "address": [
        "city",
        "state",
        "street",
        "street2",
        "zip",
        "country",
        "latitude",
        "longitude",
    ],
    "file": ["filename", "url"],
    "phone": ["formatted", "full"],
}
       