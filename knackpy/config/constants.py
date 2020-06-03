BASE_URL = "https://api.knack.com/v1/"
BASE_URL_METADATA = "https://loader.knack.com/v1"

FIELD_SETTINGS = {
    "address" : {
        "subfields": [
            "city",
            "state",
            "street",
            "street2",
            "zip",
            "country",
            "latitude",
            "longitude",
        ],
    },
    "file": {
        "subfields": ["filename", "url"],
    },
    "timer": {
        "use_knack_format": True
    }
}
       