# -*- coding: utf-8 -*-

"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo, or with python".
"""
from datetime import datetime, timedelta
from django.test import TestCase
from popolo.behaviors.tests import TimestampableTests, DateframeableTests, \
    PermalinkableTests
from popolo.models import Person, Organization, Post, ContactDetail, Area, \
    Membership, Ownership, PersonalRelationship, ElectoralEvent, \
    ElectoralResult, Language, Identifier, OverlappingIntervalError, \
    Classification, ClassificationRel, Source, SourceRel, Link, LinkRel
from faker import Factory

faker = Factory.create('it_IT')  # a factory to create fake names for tests


class ContactDetailTestsMixin(object):
    """Mixin with methods to test contact_details
    """

    def test_add_contact_detail(self):
        i = self.create_instance()
        i.add_contact_detail(contact_type=ContactDetail.CONTACT_TYPES.email,
                             value=faker.email())
        self.assertEqual(i.contact_details.count(), 1)

    def test_add_contact_details(self):
        i = self.create_instance()
        contacts = [
            {'contact_type': ContactDetail.CONTACT_TYPES.email,
             'value': faker.email()},
            {'contact_type': ContactDetail.CONTACT_TYPES.phone,
             'value': faker.phone_number()},

        ]
        i.add_contact_details(contacts)
        self.assertEqual(i.contact_details.count(), 2)


class OtherNameTestsMixin(object):

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

    def test_add_three_change_name_events(self):
        # a change name event signal the end of validity for a name
        # when two successive events are added, date intervals must be
        # interpolated
        p = self.create_instance()
        name_type = 'FOR'
        day_1 = faker.date_time_between('-2y', '-1y')

        p.add_other_name(
            name=faker.city(),
            othername_type=name_type,
            source=faker.uri(),
            start_date=None,
            end_date=day_1.strftime('%Y-%m-%d')
        )
        try:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=None,
                end_date=(day_1 + timedelta(50)).strftime('%Y-%m-%d')
            )
        except OverlappingIntervalError as e:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=e.overlapping.end_date,
                end_date=(day_1 + timedelta(50)).strftime('%Y-%m-%d')
            )
        try:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=None,
                end_date=(day_1 + timedelta(100)).strftime('%Y-%m-%d')
            )
        except OverlappingIntervalError as e:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=e.overlapping.end_date,
                end_date=(day_1 + timedelta(100)).strftime('%Y-%m-%d')
            )

        self.assertEqual(p.other_names.count(), 3)

    def test_add_three_change_name_events_wrong_order(self):
        # a change name event signal the end of validity for a name
        # when two successive events are added, date intervals must be
        # interpolated
        p = self.create_instance()
        name_type = 'FOR'
        source = faker.uri()
        day_1 = faker.date_time_between('-2y', '-1y')

        with self.assertRaises(Exception):
            p.add_other_names([
                {
                    'name': faker.city(),
                    'othername_type': name_type,
                    'source': faker.uri(),
                    'start_date': None,
                    'end_date': day_1.strftime('%Y-%m-%d')
                },
                {
                    'name': faker.city(),
                    'othername_type': name_type,
                    'source': faker.uri(),
                    'start_date': None,
                    'end_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d')
                },
                {
                    'name': faker.city(),
                    'othername_type': name_type,
                    'source': faker.uri(),
                    'start_date': None,
                    'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
                },
            ])
            self.assertEqual(p.other_names.count(), 2)


class IdentifierTestsMixin(object):

    def test_add_identifier(self):
        p = self.create_instance()
        i = p.add_identifier(
            identifier=faker.numerify('OP_######'),
            scheme=faker.text(max_nb_chars=128),
            source=faker.uri()
        )
        self.assertEqual(isinstance(i, Identifier), True)
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_identifier_twice_null_dates(self):
        # adding the same identifier twice to
        # an object, with null start and end validity dates
        p = self.create_instance()
        identifier = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)

        p.add_identifiers([
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri()
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri()
            },
        ])
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_non_overlapping_identifiers(self):
        # same scheme, different identifier values
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        p.add_identifiers([
            {
                'identifier': faker.numerify('OP_######'),
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': day_1.strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
            },
            {
                'identifier': faker.numerify('OP_######'),
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(150)).strftime('%Y-%m-%d')
            },
            {
                'identifier': faker.numerify('OP_######'),
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(250)).strftime('%Y-%m-%d')
            },
        ])
        self.assertEqual(p.identifiers.count(), 3)

    def test_add_three_overlapping_identifiers(self):
        # same scheme, different identifiers, overlapping dates
        # starting from the first
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        with self.assertRaises(Exception):
            p.add_identifiers([
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': day_1.strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(40)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(120)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
                },
            ])
        self.assertEqual(p.identifiers.count(), 2)

    def test_add_three_overlapping_identifiers_different_order(self):
        # same scheme, different identifiers, overlapping dates
        # starting from the second
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        with self.assertRaises(Exception):
            p.add_identifiers([
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(40)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(120)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': day_1.strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
                },
            ])
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_overlapping_identifiers_one_forever(self):
        # same scheme, different identifiers, overlapping dates
        # starting from the first,
        # the second is from forever
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        with self.assertRaises(Exception):
            p.add_identifiers([
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': day_1.strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': None,
                    'end_date': (day_1 + timedelta(120)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
                },
            ])
        self.assertEqual(p.identifiers.count(), 2)

    def test_add_three_extending_identifiers(self):
        # same scheme, same identifiers, overlapping dates
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        p.add_identifiers([
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(40)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(120)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': day_1.strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
            },
        ])
        self.assertEqual(p.identifiers.count(), 1)


    def test_add_three_connected_identifiers(self):
        # same scheme, same identifiers, connected dates
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        p.add_identifiers([
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': day_1.strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
            },
        ])
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_two_connected_identifiers_one_null(self):
        # same scheme, same identifiers, connected dates
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        p.add_identifiers([
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': day_1.strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d'),
                'end_date': None
            },
        ])
        self.assertEqual(p.identifiers.count(), 1)


    def test_add_three_disconnected_identifiers(self):
        # same scheme, same identifiers, 2 connected dates and 1 disconn.
        # will result in two identifiers
        p = self.create_instance()
        identifier = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        p.add_identifiers([
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': day_1.strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(101)).strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
            },
        ])
        self.assertEqual(p.identifiers.count(), 2)

    def test_add_two_extending_identifiers_one_forever(self):
        # same scheme, same identifiers, extending, one lasts forever
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        p.add_identifiers([
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': day_1.strftime('%Y-%m-%d'),
                'end_date': (day_1 + timedelta(50)).strftime('%Y-%m-%d')
            },
            {
                'identifier': identifier,
                'scheme': scheme,
                'source': faker.uri(),
                'start_date': (day_1 + timedelta(30)).strftime('%Y-%m-%d'),
                'end_date': None
            },
        ])
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_overlapping_extending_identifiers(self):
        # same scheme, same identifiers, an identifier A that overlaps
        # with two extending identifiers B
        # will result only in A if it's inserted first
        p = self.create_instance()
        identifierA = faker.numerify('OP_######')
        identifierB = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        with self.assertRaises(Exception):
            p.add_identifiers([
                {
                    'identifier': identifierA,
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(60)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': identifierB,
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': day_1.strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(90)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': identifierB,
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(80)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
                },
            ])
        self.assertEqual(p.identifiers.count(), 1)
        self.assertEqual(p.identifiers.first().identifier, identifierA)

    def test_add_three_overlapping_extending_identifiers_different_order(self):
        # same scheme, same identifiers, an identifier A that overlaps
        # with two extending identifiers B
        # will result only in B if it's inserted first
        p = self.create_instance()
        identifierA = faker.numerify('OP_######')
        identifierB = faker.numerify('OP_######')
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between('-2y', '-1y')

        with self.assertRaises(Exception):
            p.add_identifiers([
                {
                    'identifier': identifierB,
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': day_1.strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(90)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': identifierA,
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(60)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(100)).strftime('%Y-%m-%d')
                },
                {
                    'identifier': identifierB,
                    'scheme': scheme,
                    'source': faker.uri(),
                    'start_date': (day_1 + timedelta(80)).strftime('%Y-%m-%d'),
                    'end_date': (day_1 + timedelta(200)).strftime('%Y-%m-%d')
                },
            ])
        self.assertEqual(p.identifiers.count(), 1)
        self.assertEqual(p.identifiers.first().identifier, identifierB)


    def test_add_identifiers_different_schemes(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append(
                {
                    'identifier': faker.numerify('OP_######'),
                    'scheme': faker.text(max_nb_chars=128),
                    'source': faker.uri()
                }
            )
        p.add_identifiers(objects)
        self.assertEqual(p.identifiers.count(), 3)

    def test_add_identifiers_custom(self):
        p = self.create_instance()
        identifierA = faker.numerify('OP_######')
        identifierB = faker.numerify('OP_######')

        p.add_identifiers([
            {
                'identifier': identifierA,
                'scheme': 'ISTAT_CODE_COM',
                'start_date': '1995-01-01',
                'end_date': '2006-01-01',
            },
            {
                'identifier': identifierB,
                'scheme': 'ISTAT_CODE_COM',
                'start_date': '2010-01-01',
            },
            {
                'identifier': identifierA,
                'scheme': 'ISTAT_CODE_COM',
                'start_date': '2006-01-01',
                'end_date': '2010-01-01'
            }
        ])
        self.assertEqual(p.identifiers.count(), 2)


class ClassificationTestsMixin(object):

    def test_add_classification(self):
        p = self.create_instance()
        c = p.add_classification(
            scheme=faker.text(max_nb_chars=128),
            code=faker.text(max_nb_chars=12),
            descr=faker.text(max_nb_chars=256)
        )
        self.assertEqual(isinstance(c, Classification), True)
        self.assertEqual(isinstance(p.classifications.first(), ClassificationRel), True)
        self.assertEqual(p.classifications.count(), 1)

    def test_add_three_classifications(self):
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=12)

        p.add_classifications([
            {
                'scheme': scheme,
                'code': faker.text(max_nb_chars=12),
                'descr': faker.text(max_nb_chars=128)
            },
            {
                'scheme': scheme,
                'code': faker.text(max_nb_chars=12),
                'descr': faker.text(max_nb_chars=128)
            },
            {
                'scheme': scheme,
                'code': faker.text(max_nb_chars=12),
                'descr': faker.text(max_nb_chars=128)
            }
        ])
        self.assertEqual(p.classifications.count(), 3)

    def test_add_classification_twice_counts_as_one(self):
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=12)
        code = faker.text(max_nb_chars=12)
        descr = faker.text(max_nb_chars=128)

        p.add_classifications([
            {
                'scheme': scheme,
                'code': code,
                'descr': descr
            },
            {
                'scheme': scheme,
                'code': code,
                'descr': descr
            }
        ])
        self.assertEqual(p.classifications.count(), 1)



class LinkTestsMixin(object):

    def test_add_link(self):
        p = self.create_instance()
        l = p.add_link(
            url=faker.uri(),
            note=faker.text(max_nb_chars=500),
        )
        self.assertEqual(p.links.count(), 1)
        self.assertEqual(isinstance(l, Link), True)
        self.assertEqual(isinstance(p.links.first(), LinkRel), True)

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

    def test_add_same_link_twice_counts_as_one(self):
        p = self.create_instance()
        url = faker.uri()
        note = faker.text(max_nb_chars=500)

        p.add_links([
            {
                'url': url,
                'note': note,
            },
            {
                'url': url,
                'note': note,
            }
        ])
        self.assertEqual(p.links.count(), 1)

class SourceTestsMixin(object):

    def test_add_source(self):
        p = self.create_instance()
        s = p.add_source(
            url=faker.uri(),
            note=faker.text(max_nb_chars=500),
        )
        self.assertEqual(p.sources.count(), 1)
        self.assertEqual(isinstance(s, Source), True)
        self.assertEqual(isinstance(p.sources.first(), SourceRel), True)

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

    def test_add_same_source_twice_counts_as_one(self):
        p = self.create_instance()
        url = faker.uri()
        note = faker.text(max_nb_chars=500)

        p.add_sources([
            {
                'url': url,
                'note': note,
            },
            {
                'url': url,
                'note': note,
            }
        ])
        self.assertEqual(p.sources.count(), 1)

class PersonTestCase(
    ContactDetailTestsMixin,
    OtherNameTestsMixin, IdentifierTestsMixin,
    LinkTestsMixin, SourceTestsMixin,
    DateframeableTests, TimestampableTests, PermalinkableTests, TestCase
    ):
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

    def test_add_multiple_memberships(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        os = [Organization.objects.create(name=faker.company())] * 3
        p.add_memberships(os)
        self.assertEqual(p.memberships.count(), 3)
        self.assertEqual(p.organizations_memberships.count(), 3)

    def test_add_role(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = Organization.objects.create(name=faker.company())
        r = Post.objects.create(label=u'CEO', organization=o)
        p.add_role(r)
        self.assertEqual(p.memberships.count(), 1)
        self.assertEqual(p.roles.count(), 1)

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

    def test_add_relationship(self):
        p1 = self.create_instance()
        p2 = self.create_instance()
        p1.add_relationship(
            dest_person=p2,
            classification='FRIENDSHIP',
            weight=PersonalRelationship.WEIGHTS.negative
        )
        self.assertEqual(p1.related_persons.count(), 1)
        self.assertEqual(p1.related_persons.first(), p2)


class OrganizationTestCase(
    ContactDetailTestsMixin,
    OtherNameTestsMixin, IdentifierTestsMixin,
    ClassificationTestsMixin,
    LinkTestsMixin, SourceTestsMixin,
    DateframeableTests, TimestampableTests, TestCase
):
    model = Organization
    object_name = 'organization'

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({'name': u'test instance'})
        return Organization.objects.create(**kwargs)

    def test_add_member(self):
        o = self.create_instance(name=faker.company())
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        o.add_member(p, start_date=faker.year())
        self.assertEqual(o.person_members.count(), 1)
        self.assertEqual(len(o.members), 1)

    def test_add_members(self):
        o = self.create_instance(name=faker.company())
        ps = [
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
        ]
        o.add_members(ps)
        self.assertEqual(o.person_members.count(), 3)
        self.assertEqual(len(o.members), 3)

    def test_add_member_organization(self):
        o = self.create_instance(name=faker.company())
        om = Organization.objects.create(name=faker.company())
        o.add_member(om)
        self.assertEqual(o.organization_members.count(), 1)
        self.assertEqual(o.memberships.count(), 1)
        self.assertEqual(len(o.members), 1)

    def test_add_membership_to_organization(self):
        om = self.create_instance(name=faker.company())
        o = Organization.objects.create(name=faker.company())
        om.add_membership(o)
        self.assertEqual(om.organizations_memberships.count(), 1)
        self.assertEqual(len(o.members), 1)

    def test_add_mixed_members(self):
        o = self.create_instance(name=faker.company())
        ms = [
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
            Organization.objects.create(
                name=faker.company(), founding_date=faker.year()
            ),
            Person.objects.create(name=faker.name(), birth_date=faker.year()),
        ]
        o.add_members(ms)
        self.assertEqual(len(o.members), 3)

    def test_add_owner_person(self):
        o = self.create_instance(name=faker.company())
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        o.add_owner(p, percentage=0.1503)
        self.assertEqual(o.person_owners.count(), 1)
        self.assertEqual(p.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

    def test_add_owner_organization(self):
        o = self.create_instance(name=faker.company())
        om = Organization.objects.create(name=faker.company())
        o.add_owner(om, percentage=0.1705)
        self.assertEqual(o.organization_owners.count(), 1)
        self.assertEqual(om.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

    def test_add_ownership_to_organization(self):
        o = self.create_instance(name=faker.company())
        om = self.create_instance(name=faker.company())
        om.add_ownership(o, percentage=0.2753)
        self.assertEqual(om.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

    def test_add_ownership_to_person(self):
        o = self.create_instance(name=faker.company())
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        p.add_ownership(o, percentage=0.51)
        self.assertEqual(p.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

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
        o = self.create_instance(name=faker.company())
        o.add_post(label=u'CEO')
        self.assertEqual(o.posts.count(), 1)

    def test_add_posts(self):
        o = self.create_instance(name=faker.company())
        o.add_posts([
            {'label': u'Presidente'},
            {'label': u'Vicepresidente'},
        ])
        self.assertEqual(o.posts.count(), 2)

    def test_add_wrong_owner_type(self):
        o = self.create_instance(name=faker.company())
        a = Area.objects    .create(name=faker.city())
        with self.assertRaises(Exception):
            o.add_owner(a)

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

    def test_merge_from_list(self):
        o1 = self.create_instance(start_date='1962')
        o2 = self.create_instance(start_date='1978')
        o = self.create_instance()

        self.assertEqual(o1.is_active_now, True)
        self.assertEqual(o.is_active_now, True)
        self.assertEqual(o.old_orgs.count(), 0)
        self.assertEqual(o1.new_orgs.count(), 0)

        o.merge_from(o1, o2, moment='2014-04-23')
        self.assertEqual(o.is_active_now, True)
        self.assertEqual(o1.is_active_now, False)
        self.assertEqual(o.old_orgs.count(), 2)
        self.assertEqual(o1.new_orgs.count(), 1)
        self.assertEqual(o.start_date, '2014-04-23')

    def test_split_into_list(self):
        o = self.create_instance(start_date='1968')
        o1 = self.create_instance()
        o2 = self.create_instance()

        self.assertEqual(o1.is_active_now, True)
        self.assertEqual(o.is_active_now, True)
        self.assertEqual(o.old_orgs.count(), 0)
        self.assertEqual(o1.new_orgs.count(), 0)

        o.split_into(o1, o2, moment='2014-04-23')
        self.assertEqual(o.is_active_now, False)
        self.assertEqual(o1.is_active_now, True)
        self.assertEqual(o1.old_orgs.count(), 1)
        self.assertEqual(o.new_orgs.count(), 2)
        self.assertEqual(o.end_date, '2014-04-23')
        self.assertEqual(o1.start_date, '2014-04-23')


class PostTestCase(
    ContactDetailTestsMixin,
    LinkTestsMixin, SourceTestsMixin,
    DateframeableTests, TimestampableTests, TestCase
):
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
            other_label=u'CEO,AD',
            organization=Organization.objects.create(name=faker.company())
        )
        p = Person.objects.create(name=faker.name(), birth_date=faker.year())
        r.add_person(p, start_date=faker.year())
        self.assertEqual(r.holders.count(), 1)
        self.assertEqual(p.roles.count(), 1)

    def test_add_person_on_behalf_of(self):
        r = self.create_instance(
            label=u'Director',
            other_label=u'DIR',
            organization=Organization.objects.create(name=faker.company())
        )

        o2 = Organization.objects.create(name=faker.company())
        p = Person.objects.create(
            name=faker.name(), birth_date=faker.year()
        )
        r.add_person_on_behalf_of(p, o2)
        self.assertEqual(r.memberships.first().on_behalf_of, o2)

    def test_add_appointer(self):
        r = self.create_instance(
            label=u'Director',
            other_label=u'DIR',
            organization=Organization.objects.create(name=faker.company())
        )
        o2 = Organization.objects.create(name=faker.company())
        r1 = o2.add_post(
            label='President',
            other_label='PRES',
        )
        r.add_appointer(r1)
        self.assertEqual(r.appointed_by, r1)
        self.assertIn(r, list(r1.appointees.all()))


class MembershipTestCase(
    ContactDetailTestsMixin,
    LinkTestsMixin, SourceTestsMixin,
    DateframeableTests, TimestampableTests, TestCase
):
    model = Membership

    def create_instance(self, **kwargs):
        if 'person' not in kwargs:
            p = Person.objects.create(name=faker.name())
            kwargs.update({'person': p})
        if 'organization' not in kwargs:
            o = Organization.objects.create(name=faker.company())
            kwargs.update({'organization': o})

        m = Membership.objects.create(**kwargs)
        return m

    def test_missing_organization(self):
        p = Person.objects.create(name=faker.name())
        m = Membership(
            person=p,
            label=faker.word()
        )
        with self.assertRaises(Exception):
            m.save()

    def test_missing_member(self):
        o = Organization.objects.create(name=faker.company())
        m = Membership(
            organization=o,
            label=faker.word()
        )
        with self.assertRaises(Exception):
            m.save()


class OwnershipTestCase(
    SourceTestsMixin,
    DateframeableTests, TimestampableTests, TestCase
):
    model = Ownership

    def create_instance(self, **kwargs):
        if 'person' not in kwargs:
            p = Person.objects.create(name=faker.name())
            kwargs.update({'owner_person': p})
        if 'organization' not in kwargs:
            o = Organization.objects.create(name=faker.company())
            kwargs.update({'organization': o})
        if 'percentage' not in kwargs:
            kwargs.update({'percentage': 0.42})

        return Ownership.objects.create(**kwargs)

    def test_missing_organization(self):
        p = Person.objects.create(name=faker.name())
        m = Ownership(
            owner_person=p,
            percentage=0.42
        )
        with self.assertRaises(Exception):
            m.save()

    def test_missing_owner(self):
        o = Organization.objects.create(name=faker.company())
        m = Ownership(
            organization=o,
            percentage=0.42
        )
        with self.assertRaises(Exception):
            m.save()


class ElectoralEventTestCase(
    SourceTestsMixin, LinkTestsMixin,
    DateframeableTests, TimestampableTests,
    TestCase
):
    model = ElectoralEvent

    def create_instance(self, **kwargs):
        if 'classification' not in kwargs:
            kwargs.update({
                'classification': ElectoralEvent.CLASSIFICATIONS.local
            })
        if 'name' not in kwargs:
            kwargs.update({
                'name': 'Elezioni amministrative 2017'
            })
        if 'electoral_system' not in kwargs:
            kwargs.update({
                'electoral_system': 'Maggioritario a doppio turno'
            })
        return ElectoralEvent.objects.create(**kwargs)

    def test_add_general_result(self):
        e = self.create_instance()
        general_result = {
            'n_eligible_voters': 58623,
            'n_ballots': 48915,
            'perc_turnout': 48915 / 58623,
            'perc_valid_votes': 0.84,
            'perc_null_votes': 0.11,
            'perc_blank_votes': 0.05,
        }
        e.add_result(
            organization=Organization.objects.create(name=faker.company())
,
            **general_result
        )
        self.assertEqual(e.results.count(), 1)
        self.assertLess(e.results.first().perc_turnout, 0.90)


    def test_add_general_result_in_constituency(self):
        e = self.create_instance()
        general_result = {
            'n_eligible_voters': 58623,
            'n_ballots': 48915,
            'perc_turnout': 48915 / 58623,
            'perc_valid_votes': 0.84,
            'perc_null_votes': 0.11,
            'perc_blank_votes': 0.05,
        }
        e.add_result(
            organization=Organization.objects.create(name=faker.company()),
            constituency=Area.objects.create(
                name='Circoscrizione Lazio 1 della Camera',
                identifier='LAZIO1-CAMERA',
                classification='Circoscrizione elettorale',
            ),
            **general_result
        )
        self.assertEqual(e.results.count(), 1)
        self.assertLess(e.results.first().perc_turnout, 0.90)
        self.assertIsInstance(e.results.first().constituency, Area)


    def test_add_list_result(self):
        e = self.create_instance()
        list_result = {
            'n_preferences': 1313,
            'perc_preferences': 0.13
        }
        e.add_result(
            organization=Organization.objects.create(name=faker.company()),
            list=Organization.objects.create(name=faker.company()),
            **list_result
        )
        self.assertEqual(e.results.count(), 1)
        self.assertIsInstance(e.results.first().list, Organization)

    def test_add_candidate_result(self):
        e = self.create_instance()
        candidate_result = {
            'n_preferences': 1563,
            'perc_preferences': 0.16,
            'is_elected': True
        }
        e.add_result(
            organization=Organization.objects.create(name=faker.company()),
            list=Organization.objects.create(name=faker.company()),
            candidate=Person.objects.create(name=faker.name()),
            **candidate_result
        )
        self.assertEqual(e.results.count(), 1)
        self.assertIsInstance(e.results.first().list, Organization)
        self.assertIsInstance(e.results.first().candidate, Person)


class ElectoralResultTestCase(
    SourceTestsMixin, LinkTestsMixin,
    PermalinkableTests, TimestampableTests, TestCase
):
    model = ElectoralResult

    def create_instance(self, **kwargs):
        e = ElectoralEvent.objects.create(
            classification=ElectoralEvent.CLASSIFICATIONS.general,
            event_type=ElectoralEvent.EVENT_TYPES.firstround,
            name='Local elections 2016',
            electoral_system='Maggioritario a doppio turno'
        )
        return ElectoralResult.objects.create(
            event=e,
            organization=Organization.objects.create(name=faker.company()),
            **kwargs
        )


class AreaTestCase(
    SourceTestsMixin, LinkTestsMixin,
    OtherNameTestsMixin, IdentifierTestsMixin,
    PermalinkableTests, DateframeableTests, TimestampableTests,
    TestCase
):
    model = Area

    def create_instance(self, **kwargs):
        if 'name' not in kwargs:
            kwargs.update({
                'name': faker.city()
            })
        if 'classification' not in kwargs:
            kwargs.update({
                'classification': 'ADM3'
            })
        if 'identifier' not in kwargs:
            kwargs.update({
                'identifier': faker.sha1()
            })
        return Area.objects.create(**kwargs)

    def test_add_i18n_name(self):
        a = self.create_instance(
            name='Bolzano-Bozen',
            classification='city',
            identifier='021008'
        )

        it_language = Language.objects.create(
            name='Italian',
            iso639_1_code='it'
        )
        de_language = Language.objects.create(
            name='German',
            iso639_1_code='de'
        )

        a.add_i18n_name(
            'Bolzano', it_language
        )
        a.add_i18n_name(
            'Bozen', de_language
        )
        self.assertEqual(
            a.i18n_names.get(language=it_language).name, 'Bolzano'
        )
        self.assertEqual(
            a.i18n_names.get(language=de_language).name, 'Bozen'
        )

    def test_merge_from_list(self):
        a1 = self.create_instance(start_date='1962')
        a2 = self.create_instance(start_date='1978')
        a = self.create_instance()

        self.assertEqual(a1.is_active_now, True)
        self.assertEqual(a.is_active_now, True)
        self.assertEqual(a.old_places.count(), 0)
        self.assertEqual(a1.new_places.count(), 0)

        a.merge_from(a1, a2, moment='2014-04-23')
        self.assertEqual(a.is_active_now, True)
        self.assertEqual(a1.is_active_now, False)
        self.assertEqual(a.old_places.count(), 2)
        self.assertEqual(a1.new_places.count(), 1)
        self.assertEqual(a.start_date, '2014-04-23')

    def test_split_into_list(self):
        a = self.create_instance(start_date='1968')
        a1 = self.create_instance()
        a2 = self.create_instance()

        self.assertEqual(a1.is_active_now, True)
        self.assertEqual(a.is_active_now, True)
        self.assertEqual(a.old_places.count(), 0)
        self.assertEqual(a1.new_places.count(), 0)

        a.split_into(a1, a2, moment='2014-04-23')
        self.assertEqual(a.is_active_now, False)
        self.assertEqual(a1.is_active_now, True)
        self.assertEqual(a1.old_places.count(), 1)
        self.assertEqual(a.new_places.count(), 2)
        self.assertEqual(a.end_date, '2014-04-23')
        self.assertEqual(a1.start_date, '2014-04-23')

