import knackpy


def test_basic_session_construction():
    app_id = "5d79512148c4af00106d1507"  # knackpy-dev app
    return knackpy._knack_session.KnackSession(app_id)


def test_hello_idiot():
    assert("you are no longer raising for status in sessions. handle it outside.....derp")