"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo".
"""

from django.test import TestCase
from popolo.behaviors.tests import TimestampableTests, DateframeableTests, PermalinkableTests
from popolo.models import Person, Organization, Post, ContactDetail


class PersonTestCase(DateframeableTests, TimestampableTests, PermalinkableTests, TestCase):
    model = Person
    object_name = 'person'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Person.objects.create(**kwargs)

    def test_add_membership(self):
        p = Person.objects.create(name=u'Mario Rossi', birth_date='1980')
        o = Organization.objects.create(name=u'Parlamento')
        p.add_membership(o)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_memberships(self):
        p = Person.objects.create(name=u'Mario Rossi', birth_date='1980')
        os = [
            Organization.objects.create(name=u'Parlamento'),
            Organization.objects.create(name=u'P2'),
            Organization.objects.create(name=u'Banco Ambrosiano')
        ]
        p.add_memberships(os)
        self.assertEqual(p.memberships.count(), 3)

    def test_add_role(self):
        p = Person.objects.create(name=u'Mario Rossi', birth_date='1980')
        r = Post.objects.create(label=u'CEO')
        p.add_role(r)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_contact_detail(self):
        p = self.create_instance()
        p.add_contact_detail(contact_type=ContactDetail.CONTACT_TYPES.email, value=u'test@openpolis.it')
        self.assertEqual(p.contact_details.count(), 1)




class OrganizationTestCase(DateframeableTests, TimestampableTests, PermalinkableTests, TestCase):
    model = Organization
    object_name = 'organization'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Organization.objects.create(**kwargs)

    def test_add_member(self):
        o = Organization.objects.create(name=u'Parlamento')
        p = Person.objects.create(name=u'Mario Rossi', birth_date='1980')
        o.add_member(p)
        self.assertEqual(o.memberships.count(), 1)

    def test_add_members(self):
        o = Organization.objects.create(name=u'Parlamento')
        ps = [
            Person.objects.create(name=u'Mario Rossi', birth_date='1980'),
            Person.objects.create(name=u'Gino Bianchi', birth_date='1982'),
            Person.objects.create(name=u'Carla Verdi', birth_date='1979')
        ]
        o.add_members(ps)
        self.assertEqual(o.memberships.count(), 3)

    def test_add_post(self):
        o = Organization.objects.create(name=u'Parlamento')
        o.add_post(label=u'CEO')
        self.assertEqual(o.posts.count(), 1)

    def test_add_posts(self):
        o = Organization.objects.create(name=u'Parlamento')
        o.add_posts([
            {'label': u'Presidente'},
            {'label': u'Vicepresidente'},
        ])
        self.assertEqual(o.posts.count(), 2)

class PostTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Post

    def create_instance(self, **kwargs):
        if 'label' not in kwargs:
            kwargs.update({'label': u'test instance'})
        return Post.objects.create(**kwargs)

    def test_add_person(self):
        p = Post.objects.create(label=u'CEO')
        pr = Person.objects.create(name=u'Gino Bianchi', birth_date='1982')
        p.add_person(pr)
        self.assertEqual(p.memberships.count(), 1)