"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from popolo.behaviors.tests import TimestampableTests, DateframeableTests
from popolo.models import Person, Organization, Post


class PersonTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Person

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Person.objects.create(**kwargs)


class OrganizationTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Organization

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Organization.objects.create(**kwargs)

    def test_organization_has_slug(self):
        """The organization has the correct slug"""
        depp = self.create_instance(name=u"DEPP Srl", founding_date='2009-03-21', classification='Open data')
        self.assertEqual(depp.slug, 'depp-srl')

class PostTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Post

    def create_instance(self, **kwargs):
        if 'label' not in kwargs:
            kwargs.update({'label': u'post test instance'})
        return Post.objects.create(**kwargs)
