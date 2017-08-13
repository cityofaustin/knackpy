class TestClass:
    def setUp(self):
        from test_secrets import app_id, api_key

        self.apps = {
            'scene_view_with_api_key' :
                {   
                    #  view-based request with api_key
                    'scene' : 'scene_73',
                    'view' : 'view_197',
                    'ref_obj' : ['object_12', 'object_11'],
                    'app_id' : app_id,
                    'api_key' : api_key,
                    'page_limit' : 1,
                    'rows_per_page' : 10
                },
            'scene_view_no_api_key' :
                {   
                    #  view-based request without api_key
                    'scene' : 'scene_467',
                    'view' : 'view_1329',
                    'ref_obj' : ['object_31'],
                    'app_id' : app_id,
                    'page_limit' : 1,
                    'rows_per_page' : 10
                },
            'object_api_key' :
            {   
                #  object-based request
                'obj' : 'object_12',
                'app_id' : app_id,
                'api_key' : api_key,
                'page_limit' : 1,
                'rows_per_page' : 10
            }

        }


    def tearDown(self):
        #  for filename in self.filenames:
        #       delete filename
        return

    def test_scene_view_with_api_key(self):
        from knackpy import Knack

        app = self.apps['scene_view_with_api_key']

        kn = Knack(
            scene=app['scene'],
            view=app['view'],
            ref_obj=app['ref_obj'],
            app_id=app['app_id'],
            api_key=app['api_key'],
            page_limit=2,
            rows_per_page=10
        )

        assert len(kn.data) == 20

    def test_scene_view_no_api_key(self):
        from knackpy import Knack

        app = self.apps['scene_view_no_api_key']

        kn = Knack(
            scene=app['scene'],
            view=app['view'],
            app_id=app['app_id'],
            page_limit=1,
            rows_per_page=10
        )

        assert len(kn.data_raw) > 0

    def test_object_api_key(self):
        from knackpy import Knack

        app = self.apps['object_api_key']

        kn = Knack(
            obj=app['obj'],
            app_id=app['app_id'],
            api_key=app['api_key'],
            page_limit=2,
            rows_per_page=10
        )

        assert len(kn.data) == 20











