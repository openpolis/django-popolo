"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo".
"""

from django.test import TestCase
from popolo.behaviors.tests import TimestampableTests, DateframeableTests, PermalinkableTests
from popolo.models import Person, Organization, Post, ContactDetail
from faker import Factory
from unittest import skip

faker = Factory.create('it_IT') #a factory to create fake names for tests


class PersonTestCase(DateframeableTests, TimestampableTests, PermalinkableTests, TestCase):
    model = Person
    object_name = 'person'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Person.objects.create(**kwargs)

    def test_add_membership(self):
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())
        p.add_membership(o)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_memberships(self):
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        os = [
            Organization.objects.create(name=faker.company())
            for i in range(3)
        ]
        p.add_memberships(os)
        self.assertEqual(p.memberships.count(), 3)

    def test_memberships_slug_source(self):
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        os = [
            Organization.objects.create(name=faker.company())
            for i in range(3)
        ]
        p.add_memberships(os)

        memberships = p.memberships.all()
        for membership in memberships:
            membership.label = membership.organization.name
            membership.save()

        self.assertTrue(memberships[0].slug_source, memberships[0].label)
        self.assertTrue(memberships[1].slug_source, memberships[1].label)
        self.assertTrue(memberships[2].slug_source, memberships[2].label)

    def test_add_role(self):
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())
        r = Post.objects.create(label=u'CEO', organization=o)
        p.add_role(r)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_contact_detail(self):
        p = self.create_instance()
        p.add_contact_detail(contact_type=ContactDetail.CONTACT_TYPES.email, value=faker.email())
        self.assertEqual(p.contact_details.count(), 1)

    def test_add_contact_details(self):
        p = self.create_instance()
        contacts = [
            {'contact_type': ContactDetail.CONTACT_TYPES.email,
             'value': faker.email()},
            {'contact_type': ContactDetail.CONTACT_TYPES.phone,
             'value': faker.phone_number()},

        ]
        p.add_contact_details(contacts)
        self.assertEqual(p.contact_details.count(), 2)

    def test_it_copies_birth_date_after_saving(self):
        pr = Person(name=faker.name(), birth_date=faker.year())
        self.assertIsNone(pr.start_date)
        pr.save()
        self.assertEqual(pr.start_date, pr.birth_date)

    def test_it_copies_death_date_after_saving(self):
        pr = Person(name=faker.name(), death_date=faker.year())
        self.assertIsNone(pr.end_date)
        pr.save()
        self.assertEqual(pr.end_date, pr.death_date)


    def test_add_links_and_sources(self):
        p = self.create_instance()
        p.links.create( url='http://link.example.org/', note='Note' )
        p.sources.create( url='http://source.example.org/', note='Source note' )
        self.assertEqual(p.links.count(), 1)
        self.assertEqual(p.sources.filter(url='http://link.example.org/').count(), 0)

class OrganizationTestCase(DateframeableTests, TimestampableTests, PermalinkableTests, TestCase):
    model = Organization
    object_name = 'organization'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Organization.objects.create(**kwargs)

    def test_add_member(self):
        o = Organization.objects.create(name=faker.company())
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        o.add_member(p)
        self.assertEqual(o.memberships.count(), 1)

    def test_add_members(self):
        o = Organization.objects.create(name=faker.company())
        ps = [
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
        ]
        o.add_members(ps)
        self.assertEqual(o.memberships.count(), 3)

    def test_add_post(self):
        o = Organization.objects.create(name=faker.company())
        o.add_post(label=u'CEO')
        self.assertEqual(o.posts.count(), 1)

    def test_add_posts(self):
        o = Organization.objects.create(name=faker.company())
        o.add_posts([
            {'label': u'Presidente'},
            {'label': u'Vicepresidente'},
        ])
        self.assertEqual(o.posts.count(), 2)

    def test_it_copies_the_foundation_date_to_start_date(self):
        o = Organization(name=faker.company(), founding_date=faker.year())
        #it is not set to start_date until saved
        self.assertIsNone(o.start_date)
        o.save()
        self.assertEqual(o.start_date, o.founding_date)

    def test_it_copies_the_dissolution_date_to_end_date(self):
        o = Organization(name=faker.company(), dissolution_date=faker.year())
        #it is not set to start_date until saved
        self.assertIsNone(o.end_date)
        o.save()
        self.assertEqual(o.end_date, o.dissolution_date)


class PostTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Post

    def create_instance(self, **kwargs):
        if 'label' not in kwargs:
            kwargs.update({'label': u'test instance'})
        if 'organization' not in kwargs:
            o = Organization.objects.create(name=faker.company())
            kwargs.update({'organization': o})
        return Post.objects.create(**kwargs)

    def test_add_person(self):
        o = Organization.objects.create(name=faker.company())
        p = Post.objects.create(label=u'CEO', organization=o)
        pr = Person.objects.create(name=faker.name(), birth_date=faker.year())
        p.add_person(pr)
        self.assertEqual(p.memberships.count(), 1)
