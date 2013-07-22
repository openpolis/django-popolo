"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo".
"""

from django.test import TestCase
from popolo.behaviors.tests import TimestampableTests, DateframeableTests, PermalinkableTests
from popolo.models import Person, Organization, Post


class PersonTestCase(DateframeableTests, TimestampableTests, PermalinkableTests, TestCase):
    model = Person
    object_name = 'person'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Person.objects.create(**kwargs)



class OrganizationTestCase(DateframeableTests, TimestampableTests, PermalinkableTests, TestCase):
    model = Organization
    object_name = 'organization'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Organization.objects.create(**kwargs)



class PostTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Post

    def create_instance(self, **kwargs):
        if 'label' not in kwargs:
            kwargs.update({'label': u'test instance'})
        return Post.objects.create(**kwargs)
