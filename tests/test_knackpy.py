from secrets import AUTH
from config import config
from knackpy import Knack, get_app_data, record

def test_scene_view_with_api_key():

    cfg = config.get("toppings")

    kn = Knack(
        scene=cfg['scene'],
        view=cfg['view'],
        ref_obj=cfg['ref_obj'],
        app_id=AUTH['app_id'],
        api_key=AUTH['api_key'],
        page_limit=2,
        rows_per_page=10
    )

    assert len(kn.data) > 0


def test_object_api_key():
    
    cfg = config.get("toppings")

    kn = Knack(
        obj=cfg['obj'],
        app_id=AUTH['app_id'],
        api_key=AUTH['api_key'],
        page_limit=2,
        rows_per_page=10
    )

    assert len(kn.data) > 0

if __name__ == "__main__":
    test_scene_view_with_api_key()
    test_object_api_key()
