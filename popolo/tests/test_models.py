"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo, or with python".
"""

from django.test import TestCase
from popolo.behaviors.tests import TimestampableTests, DateframeableTests, \
    PermalinkableTests
from popolo.models import Person, Organization, Post, ContactDetail, Area
from faker import Factory

faker = Factory.create('it_IT')  # a factory to create fake names for tests


class PersonTestCase(DateframeableTests, TimestampableTests,
    PermalinkableTests, TestCase):
    model = Person
    object_name = 'person'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Person.objects.create(**kwargs)


    def test_add_membership(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())
        p.add_membership(o)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_membership_with_date(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())

        start_date = faker.date()
        p.add_membership(o, start_date=start_date)
        m = p.memberships.first()
        self.assertEqual(m.start_date, start_date)


    def test_add_membership_with_dates(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())

        start_date = faker.date()
        end_date = faker.date()
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        p.add_membership(o, start_date=start_date, end_date=end_date)
        m = p.memberships.first()
        self.assertEqual(m.start_date, start_date)
        self.assertEqual(m.end_date, end_date)

    def test_add_membership_with_unordered_dates_raises_exception(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())

        start_date = faker.date()
        end_date = faker.date()
        if start_date < end_date:
            start_date, end_date = end_date, start_date

        with self.assertRaises(Exception):
            p.add_membership(o, start_date=start_date, end_date=end_date)

    def test_add_memberships(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        os = [
            Organization.objects.create(name=faker.company())
            for i in range(3)
        ]
        p.add_memberships(os)
        self.assertEqual(p.memberships.count(), 3)

    def test_membership_organizations(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        os = [
            Organization.objects.create(name=faker.company())
            for i in range(3)
        ]
        p.add_memberships(os)
        self.assertEqual(p.organizations_is_member_of().count(), 3)


    def test_add_role(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())
        r = Post.objects.create(label=u'CEO', organization=o)
        p.add_role(r)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_role_on_behalf_of(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o1 = Organization.objects.create(name=faker.company())
        o2 = Organization.objects.create(name=faker.company())
        r = o1.add_post(
            label=u'Director',
            other_label=u'DIR',
        )
        p.add_role_on_behalf_of(r, o2)
        self.assertEqual(p.memberships.first().on_behalf_of, o2)

    def test_post_organizations(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        for i in range(3):
            o = Organization.objects.create(name=faker.company())
            r = Post.objects.create(label=faker.word().title(), organization=o)
            p.add_role(r)

        self.assertEqual(p.organizations_has_role_in().count(), 3)

    def test_add_contact_detail(self):
        p = self.create_instance()
        p.add_contact_detail(contact_type=ContactDetail.CONTACT_TYPES.email,
                             value=faker.email())
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

    def test_add_other_name(self):
        p = self.create_instance()
        p.add_other_name(
            name=faker.name(),
            note=faker.text(max_nb_chars=500),
            source=faker.uri()
        )
        self.assertEqual(p.other_names.count(), 1)

    def test_add_other_names(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append(
                {
                    'name': faker.name(),
                    'note': faker.text(max_nb_chars=500),
                    'source': faker.uri()
                }
            )
        p.add_other_names(objects)
        self.assertEqual(p.other_names.count(), 3)


    def test_add_identifier(self):
        p = self.create_instance()
        p.add_identifier(
            identifier=faker.numerify('OP_######'),
            scheme=faker.text(max_nb_chars=500),
            source=faker.uri()
        )
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_identifiers(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append(
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': faker.text(max_nb_chars=500),
                    'source': faker.uri()
                }
            )
        p.add_identifiers(objects)
        self.assertEqual(p.identifiers.count(), 3)

    def test_add_link(self):
        p = self.create_instance()
        p.add_link(
            url=faker.uri(),
            note=faker.text(max_nb_chars=500),
        )
        self.assertEqual(p.links.count(), 1)

    def test_add_links(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append(
                {
                    'url': faker.uri(),
                    'note': faker.text(max_nb_chars=500),
                }
            )
        p.add_links(objects)
        self.assertEqual(p.links.count(), 3)

    def test_add_source(self):
        p = self.create_instance()
        p.add_source(
            url=faker.uri(),
            note=faker.text(max_nb_chars=500),
        )
        self.assertEqual(p.sources.count(), 1)

    def test_add_sources(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append(
                {
                    'url': faker.uri(),
                    'note': faker.text(max_nb_chars=500),
                }
            )
        p.add_sources(objects)
        self.assertEqual(p.sources.count(), 3)






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
        p.links.create(url='http://link.example.org/', note='Note')
        p.sources.create(url='http://source.example.org/', note='Source note')
        self.assertEqual(p.links.count(), 1)
        self.assertEqual(
            p.sources.filter(url='http://link.example.org/').count(), 0)


class OrganizationTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Organization
    object_name = 'organization'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Organization.objects.create(**kwargs)

    def test_add_member(self):
        o = self.create_instance(name=faker.company())
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        o.add_member(p)
        self.assertEqual(o.memberships.count(), 1)

    def test_add_members(self):
        o = self.create_instance(name=faker.company())
        ps = [
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
        ]
        o.add_members(ps)
        self.assertEqual(o.memberships.count(), 3)

    def test_add_member_organization(self):
        o = self.create_instance(name=faker.company())
        om = Organization.objects.create(name=faker.company())
        o.add_member(om)
        self.assertEqual(o.memberships.count(), 1)

    def test_add_membership_to_organization(self):
        om = self.create_instance(name=faker.company())
        o = Organization.objects.create(name=faker.company())
        om.add_membership(o)
        self.assertEqual(o.memberships.count(), 1)

    def test_add_mixed_members(self):
        o = self.create_instance(name=faker.company())
        ms = [
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Organization.objects.create(name=faker.company(), founding_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
        ]
        o.add_members(ms)
        self.assertEqual(o.memberships.count(), 3)

    def test_read_mixed_members(self):
        o = self.create_instance(name=faker.company())
        ms = [
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Organization.objects.create(name=faker.company(), founding_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
        ]
        o.add_members(ms)

        for membership in o.memberships.all():
            self.assertTrue(
                any((
                    isinstance(membership.member, Person),
                    isinstance(membership.member, Organization)
                ))
            )

    def test_add_wrong_member_type(self):
        o = self.create_instance(name=faker.company())
        a = Area.objects.create(
            name=faker.city(),
            identifier=faker.numerify("####"),
            classification=faker.word()
        )
        with self.assertRaises(Exception):
            o.add_member(a)


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
        # it is not set to start_date until saved
        self.assertIsNone(o.start_date)
        o.save()
        self.assertEqual(o.start_date, o.founding_date)

    def test_it_copies_the_dissolution_date_to_end_date(self):
        o = Organization(name=faker.company(), dissolution_date=faker.year())
        # it is not set to start_date until saved
        self.assertIsNone(o.end_date)
        o.save()
        self.assertEqual(o.end_date, o.dissolution_date)


class PostTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = Post

    def create_instance(self, **kwargs):
        if 'label' not in kwargs:
            kwargs.update({'label': u'test instance'})
        if 'other_label' not in kwargs:
            kwargs.update({'other_label': u'TI,TEST'})

        if 'organization' not in kwargs:
            o = Organization.objects.create(name=faker.company())
            kwargs.update({'organization': o})
        return Post.objects.create(**kwargs)

    def test_add_person(self):
        r = self.create_instance(
            label=u'Chief Executive Officer',
            other_label=u'CEO,AD'
        )
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        r.add_person(p)
        self.assertEqual(r.memberships.count(), 1)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_person_on_behalf_of(self):
        r = self.create_instance(
            label=u'Director',
            other_label=u'DIR'
        )

        o2 = Organization.objects.create(name=faker.company())
        p = Person.objects.create(
            name=faker.name(), birth_date=faker.year()
        )
        r.add_person_on_behalf_of(p, o2)
        self.assertEqual(r.memberships.first().on_behalf_of, o2)

