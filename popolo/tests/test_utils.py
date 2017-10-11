# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from unittest import TestCase
from faker import Factory
from popolo.utils import PartialDate, PartialDateException, PartialDatesInterval

faker = Factory.create('it_IT')  # a factory to create fake names for tests


class PartialDateTestCase(TestCase):

    def create_instance(self, ds=None, pattern=PartialDate.d_fmt):
        if not ds:
            ds = faker.date(pattern=pattern)
        return PartialDate(ds)

    def test_new_instance(self):
        ds = faker.date(PartialDate.d_fmt)
        d = self.create_instance(ds)

        self.assertEqual(isinstance(d.date, str), True)
        self.assertEqual(isinstance(d.date_as_dt, datetime), True)

    def test_new_instance_using_d_fmt(self):
        ds = faker.date(PartialDate.d_fmt)
        d = self.create_instance(ds)

        self.assertEqual(d.date, ds)
        self.assertEqual(
            d.date_as_dt, datetime.strptime(ds, PartialDate.d_fmt)
        )

    def test_new_instance_using_m_fmt(self):
        ds = faker.date(PartialDate.m_fmt)
        d = self.create_instance(ds)

        self.assertEqual(
            d.date_as_dt, datetime.strptime(ds, PartialDate.m_fmt)
        )

    def test_new_instance_using_y_fmt(self):
        ds = faker.date(PartialDate.y_fmt)
        d = self.create_instance(ds)

        self.assertEqual(
            d.date_as_dt, datetime.strptime(ds, PartialDate.y_fmt)
        )

    def test_new_instance_null(self):
        d = PartialDate(None)
        self.assertEqual(d.date, None)
        self.assertEqual(d.date_as_dt, None)

    def test_sub_partialdate(self):
        dt = timedelta(100)

        da = faker.date()
        a = PartialDate(da)
        b = a + dt

        self.assertTrue(b - a, dt)

    def test_sub_timedelta(self):
        dt = timedelta(100)

        da = faker.date()
        a = PartialDate(da)
        b = PartialDate(da) + dt

        self.assertTrue(b - dt, a)

    def test_sum_timedelta(self):
        da = faker.date()
        a = PartialDate(da)

        dt = timedelta(100)

        db = datetime.strftime(
            faker.date_time_between(
                a.date_as_dt + timedelta(days=100)
            ), '%Y-%m-%d'
        )
        b = PartialDate(db)
        self.assertTrue(b + dt, a)

    def test_eq_comparison(self):
        da = db = faker.date()
        a = self.create_instance(da)
        b = self.create_instance(db)

        self.assertEqual(a, b)

    def test_eq_comparison_null(self):
        a = PartialDate(None)
        b = PartialDate(None)

        self.assertEqual(a, b)

    def test_gt_comparison(self):
        dt = timedelta(100)

        da = faker.date()
        a = PartialDate(da)
        b = PartialDate(da) + dt

        self.assertGreater(b, a)

    def test_gt_comparison_null(self):
        da = faker.date()

        a = PartialDate(da)
        b = PartialDate(None)
        with self.assertRaises(PartialDateException):
            self.assertGreater(b, a)

    def test_lt_comparison(self):
        dt = timedelta(100)

        da = faker.date()
        a = PartialDate(da)
        b = PartialDate(da) + dt

        self.assertLess(a, b)

    def test_lt_comparison_null(self):
        da = faker.date()

        a = PartialDate(da)
        b = PartialDate(None)
        with self.assertRaises(PartialDateException):
            self.assertLess(a, b)

    def test_ge_comparison(self):
        dt = timedelta(100)

        da = faker.date()
        a = PartialDate(da)
        b = PartialDate(da) + dt
        c = PartialDate(da)

        self.assertGreaterEqual(b, a)
        self.assertGreaterEqual(c, a)

    def test_intervals_overlap(self):
        da_start = faker.date()
        a_start = PartialDate(da_start)

        da_end = datetime.strftime(
            faker.date_time_between(
                a_start.date_as_dt
            ), '%Y-%m-%d'
        )
        a_end = PartialDate(da_end)

        db_start = datetime.strftime(
            faker.date_time_between(
                a_start.date_as_dt, a_end.date_as_dt
            ), '%Y-%m-%d'
        )
        b_start = PartialDate(db_start)

        db_end = datetime.strftime(
            faker.date_time_between(
                b_start.date_as_dt
            ), '%Y-%m-%d'
        )
        b_end = PartialDate(db_end)

        self.assertLessEqual(b_start, a_end)

        a = PartialDatesInterval(start=a_start, end=a_end)
        b = PartialDatesInterval(start=b_start, end=b_end)

        overlap = PartialDate.intervals_overlap(a, b)
        self.assertGreater(overlap, 0)

    def test_intervals_do_not_overlap(self):
        da_start = faker.date()
        a_start = PartialDate(da_start)

        da_end = datetime.strftime(
            faker.date_time_between(
                a_start.date_as_dt
            ), '%Y-%m-%d'
        )
        a_end = PartialDate(da_end)

        db_start = datetime.strftime(
            faker.date_time_between(
                a_end.date_as_dt
            ), '%Y-%m-%d'
        )
        b_start = PartialDate(db_start)

        db_end = datetime.strftime(
            faker.date_time_between(
                b_start.date_as_dt
            ), '%Y-%m-%d'
        )
        b_end = PartialDate(db_end)

        a = PartialDatesInterval(start=a_start, end=a_end)
        b = PartialDatesInterval(start=b_start, end=b_end)

        overlap = PartialDate.intervals_overlap(a, b)
        self.assertLessEqual(overlap, 0)

    def test_intervals_overlap_null_start_end(self):
        a_start = PartialDate(None)

        da_end = faker.date()
        a_end = PartialDate(da_end)

        db_start = datetime.strftime(
            faker.date_time_between(
                a_end.date_as_dt - timedelta(days=50),
                a_end.date_as_dt
            ), '%Y-%m-%d'
        )
        b_start = PartialDate(db_start)
        b_end = PartialDate(None)

        a = PartialDatesInterval(start=a_start, end=a_end)
        b = PartialDatesInterval(start=b_start, end=b_end)

        overlap = PartialDate.intervals_overlap(a, b)
        self.assertGreater(overlap, 0)

    def test_intervals_do_not_overlap_null_start_end(self):
        a_start = PartialDate(None)

        da_end = faker.date()
        a_end = PartialDate(da_end)

        db_start = datetime.strftime(
            faker.date_time_between(
                a_end.date_as_dt + timedelta(days=10)
            ), '%Y-%m-%d'
        )
        b_start = PartialDate(db_start)

        b_end = PartialDate(None)

        a = PartialDatesInterval(start=a_start, end=a_end)
        b = PartialDatesInterval(start=b_start, end=b_end)

        overlap = PartialDate.intervals_overlap(a, b)
        self.assertLessEqual(overlap, 0)
