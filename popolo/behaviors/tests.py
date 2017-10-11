from time import sleep
from datetime import timedelta
from datetime import datetime

from django.core.exceptions import ValidationError


class BehaviorTestCaseMixin(object):
    def get_model(self):
        return getattr(self, 'model')

    def create_instance(self, **kwargs):
        raise NotImplementedError("Implement me")


class DateframeableTests(BehaviorTestCaseMixin):
    """
    Dateframeable tests.

    Are dates valid? Are invalid dates blocked?
    Are querysets to filter past, present and future items correct?
    """

    def test_new_instance_has_valid_dates(self):
        """Test complete or incomplete dates,
        according to the "^[0-9]{4}(-[0-9]{2}){0,2}$" pattern (incomplete
        dates)"""
        obj = self.create_instance(start_date='2012')
        self.assertRegexpMatches(obj.start_date, "^[0-9]{4}(-[0-9]{2}){0,2}$",
                                 "date does not match pattern")
        obj = self.create_instance(end_date='2012')
        self.assertRegexpMatches(obj.end_date, "^[0-9]{4}(-[0-9]{2}){0,2}$",
                                 "date does not match pattern")

        obj = self.create_instance(start_date='2012-01')
        self.assertRegexpMatches(obj.start_date, "^[0-9]{4}(-[0-9]{2}){0,2}$",
                                 "date does not match pattern")
        obj = self.create_instance(end_date='2012-02')
        self.assertRegexpMatches(obj.end_date, "^[0-9]{4}(-[0-9]{2}){0,2}$",
                                 "date does not match pattern")

        obj = self.create_instance(start_date='2012-10-12')
        self.assertRegexpMatches(obj.start_date, "^[0-9]{4}(-[0-9]{2}){0,2}$",
                                 "date does not match pattern")
        obj = self.create_instance(end_date='2012-12-10')
        self.assertRegexpMatches(obj.end_date, "^[0-9]{4}(-[0-9]{2}){0,2}$",
                                 "date does not match pattern")

    def test_invalid_dates_are_blocked(self):
        """Test if dates are valid (months and days range are tested)"""
        # test invalid start dates
        with self.assertRaises(ValidationError):
            obj = self.create_instance(start_date='YESTERDAY')

        with self.assertRaises(ValidationError):
            obj = self.create_instance(start_date='2012-1210')

        with self.assertRaises(ValidationError):
            obj = self.create_instance(start_date='2012-13')

        with self.assertRaises(ValidationError):
            obj = self.create_instance(start_date='2012-12-34')

        # test invalid end dates
        with self.assertRaises(ValidationError):
            obj = self.create_instance(end_date='YESTERDAY')

        with self.assertRaises(ValidationError):
            obj = self.create_instance(end_date='2012-1210')

        with self.assertRaises(ValidationError):
            obj = self.create_instance(end_date='2012-13')

        with self.assertRaises(ValidationError):
            obj = self.create_instance(end_date='2012-12-34')

    def test_querysets_filters(self):
        """Test current, past and future querysets"""
        past_obj = self.create_instance(
            start_date=datetime.strftime(datetime.now() - timedelta(days=10),
                                         '%Y-%m-%d'),
            end_date=datetime.strftime(datetime.now() - timedelta(days=5),
                                       '%Y-%m-%d'))
        current_obj = self.create_instance(
            start_date=datetime.strftime(datetime.now() - timedelta(days=5),
                                         '%Y-%m-%d'),
            end_date=datetime.strftime(datetime.now() + timedelta(days=5),
                                       '%Y-%m-%d'))
        future_obj = self.create_instance(
            start_date=datetime.strftime(datetime.now() + timedelta(days=5),
                                         '%Y-%m-%d'),
            end_date=datetime.strftime(datetime.now() + timedelta(days=10),
                                       '%Y-%m-%d'))

        self.assertEqual(self.get_model().objects.all().count(), 3,
                         "Something really bad is going on")
        self.assertEqual(self.get_model().objects.past().count(), 1,
                         "One past object should have been fetched")
        self.assertEqual(self.get_model().objects.current().count(), 1,
                         "One current object should have been fetched")
        self.assertEqual(self.get_model().objects.future().count(), 1,
                         "One future object should have been fetched")

    def test_is_active_now(self):
        i = self.create_instance()
        self.assertEqual(i.is_active_now, True)

        i = self.create_instance(
            start_date='2012', end_date='2017'
        )
        self.assertEqual(i.is_active_now, False)

        i = self.create_instance(
            start_date='2012', end_date='2019'
        )
        self.assertEqual(i.is_active_now, True)

        i = self.create_instance(
            start_date='2012'
        )
        self.assertEqual(i.is_active_now, True)

    def test_is_active(self):
        i = self.create_instance(
            start_date='2012', end_date='2017'
        )
        self.assertEqual(i.is_active('2015-04-23'), True)



class TimestampableTests(BehaviorTestCaseMixin):
    """
    Timestampable tests.

    Tests whether objects are assigned timestamps at creation time, and
    whether a successive modification changes the update timestamp only.
    """

    def test_new_instance_has_equal_timestamps(self):
        """Object is assigned timestamps when created"""
        obj = self.create_instance()
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)

        # created_at and updated_at are actually different, but still within
        # 20 millisec
        # that's because of the pre-save signal validation
        self.assertTrue(
            (obj.updated_at - obj.created_at) < timedelta(microseconds=20000))

    def test_updated_instance_has_different_timestamps(self):
        """Modified object has different created_at and updated_at timestamps
        """
        obj = self.create_instance()
        creation_ts = obj.created_at
        update_ts = obj.updated_at
        # save object after 30K microsecs and check again
        sleep(0.03)
        obj.save()
        self.assertEqual(obj.created_at, creation_ts)
        self.assertNotEqual(obj.updated_at, update_ts)

        # created_at and updated_at are actually different, well outside 20
        # millisecs
        self.assertFalse(
            (obj.updated_at - obj.created_at) < timedelta(microseconds=20000))


class PermalinkableTests(BehaviorTestCaseMixin):
    """
    Permalinkable tests.

    Tests whether objects are assigned slugs and have the correct absolute_url
    """

    def test_instance_has_slug(self):
        """The instance has been assigned a non-null slug"""
        i = self.create_instance()
        self.assertIsNotNone(i.slug)

    def test_instance_has_permalink(self):
        i = self.create_instance()
        self.assertIsNotNone(i.get_absolute_url())

    def test_instance_permalink_contains_slug(self):
        i = self.create_instance()
        self.assertIn(i.slug, i.get_absolute_url())
