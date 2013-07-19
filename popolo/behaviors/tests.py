class BehaviorTestCaseMixin(object):
    def get_model(self):
            return getattr(self, 'model')
    
    def create_instance(self, **kwargs):
        raise NotImplementedError("Implement me")


class TimestampableTests(BehaviorTestCaseMixin):

    def test_object_is_timestampable(self):
        """Object are assigned timestamps when created"""
        obj = self.create_instance()
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)

