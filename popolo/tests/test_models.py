# -*- coding: utf-8 -*-

"""
Implements tests specific to the popolo module.
Run with "manage.py test popolo, or with python".
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from faker import Factory

from popolo.behaviors.tests import TimestampableTests, DateframeableTests, PermalinkableTests
from popolo.models import (
    Person,
    Organization,
    Post,
    ContactDetail,
    Area,
    Membership,
    Ownership,
    PersonalRelationship,
    KeyEvent,
    Language,
    Identifier,
    OverlappingIntervalError,
    Classification,
    ClassificationRel,
    Source,
    SourceRel,
    Link,
    LinkRel,
    OriginalProfession,
    KeyEventRel,
)
from popolo.tests.factories import (
    OriginalProfessionFactory,
    PersonFactory,
    OrganizationFactory,
    ClassificationFactory,
    LegislatureEventFactory,
    ElectoralEventFactory,
    XadmEventFactory,
)

faker = Factory.create("it_IT")  # a factory to create fake names for tests


class ContactDetailTestsMixin(object):
    """Mixin with methods to test contact_details
    """

    def test_add_contact_detail(self):
        i = self.create_instance()
        i.add_contact_detail(contact_type=ContactDetail.CONTACT_TYPES.email, value=faker.email())
        self.assertEqual(i.contact_details.count(), 1)

    def test_add_contact_details(self):
        i = self.create_instance()
        contacts = [
            {"contact_type": ContactDetail.CONTACT_TYPES.email, "value": faker.email()},
            {"contact_type": ContactDetail.CONTACT_TYPES.phone, "value": faker.phone_number()},
        ]
        i.add_contact_details(contacts)
        self.assertEqual(i.contact_details.count(), 2)

    def test_update_contact_details(self):
        i = self.create_instance()

        contacts = [
            {"contact_type": ContactDetail.CONTACT_TYPES.email, "value": faker.email()},
            {"contact_type": ContactDetail.CONTACT_TYPES.phone, "value": faker.phone_number()},
        ]
        i.add_contact_details(contacts)
        self.assertEqual(i.contact_details.count(), 2)

        # update one contact
        test_value = "test@email.com"
        contacts[0]["value"] = test_value

        # remove one object
        contacts.pop()

        # append two objects
        contacts.append({"contact_type": ContactDetail.CONTACT_TYPES.address, "value": faker.address()})
        contacts.append({"contact_type": ContactDetail.CONTACT_TYPES.url, "value": faker.uri()})

        # update contacts
        i.update_contact_details(contacts)

        # test total number (2 - 1 + 2 == 3)
        self.assertEqual(i.contact_details.count(), 3)

        # test modified name is there
        self.assertTrue(test_value in i.contact_details.values_list("value", flat=True))


class OtherNameTestsMixin(object):
    def test_add_other_name(self):
        p = self.create_instance()
        p.add_other_name(name=faker.name(), note=faker.text(max_nb_chars=500), source=faker.uri())
        self.assertEqual(p.other_names.count(), 1)

    def test_add_other_names(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append({"name": faker.name(), "note": faker.text(max_nb_chars=500), "source": faker.uri()})
        p.add_other_names(objects)
        self.assertEqual(p.other_names.count(), 3)

    def test_add_three_change_name_events(self):
        # a change name event signal the end of validity for a name
        # when two successive events are added, date intervals must be
        # interpolated
        p = self.create_instance()
        name_type = "FOR"
        day_1 = faker.date_time_between("-2y", "-1y")

        p.add_other_name(
            name=faker.city(),
            othername_type=name_type,
            source=faker.uri(),
            start_date=None,
            end_date=day_1.strftime("%Y-%m-%d"),
        )
        try:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=None,
                end_date=(day_1 + timedelta(50)).strftime("%Y-%m-%d"),
            )
        except OverlappingIntervalError as e:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=e.overlapping.end_date,
                end_date=(day_1 + timedelta(50)).strftime("%Y-%m-%d"),
            )
        try:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=None,
                end_date=(day_1 + timedelta(100)).strftime("%Y-%m-%d"),
            )
        except OverlappingIntervalError as e:
            p.add_other_name(
                name=faker.city(),
                othername_type=name_type,
                source=faker.uri(),
                start_date=e.overlapping.end_date,
                end_date=(day_1 + timedelta(100)).strftime("%Y-%m-%d"),
            )

        self.assertEqual(p.other_names.count(), 3)

    def test_add_three_change_name_events_wrong_order(self):
        # a change name event signal the end of validity for a name
        # when two successive events are added, date intervals must be
        # interpolated
        p = self.create_instance()
        name_type = "FOR"
        source = faker.uri()
        day_1 = faker.date_time_between("-2y", "-1y")

        with self.assertRaises(Exception):
            p.add_other_names(
                [
                    {
                        "name": faker.city(),
                        "othername_type": name_type,
                        "source": faker.uri(),
                        "start_date": None,
                        "end_date": day_1.strftime("%Y-%m-%d"),
                    },
                    {
                        "name": faker.city(),
                        "othername_type": name_type,
                        "source": faker.uri(),
                        "start_date": None,
                        "end_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    },
                    {
                        "name": faker.city(),
                        "othername_type": name_type,
                        "source": faker.uri(),
                        "start_date": None,
                        "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    },
                ]
            )
            self.assertEqual(p.other_names.count(), 2)

    def test_update_names(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append({"name": faker.name(), "note": faker.text(max_nb_chars=500), "source": faker.uri()})
        p.add_other_names(objects)
        self.assertEqual(p.other_names.count(), 3)

        # update one identifier
        test_value = "TESTING"
        objects[0]["name"] = test_value

        # remove one object
        objects.pop()

        # append two objects
        objects.append({"name": faker.name(), "note": faker.text(max_nb_chars=500), "source": faker.uri()})
        objects.append({"name": faker.name(), "note": faker.text(max_nb_chars=500), "source": faker.uri()})

        # update identifiers
        p.update_other_names(objects)

        # test total number (3 - 1 + 2 == 4)
        self.assertEqual(p.other_names.count(), 4)

        # test modified name is there
        self.assertTrue(test_value in p.other_names.values_list("name", flat=True))


class IdentifierTestsMixin(object):
    def test_add_identifier(self):
        p = self.create_instance()
        i = p.add_identifier(
            identifier=faker.numerify("OP_######"), scheme=faker.text(max_nb_chars=128), source=faker.uri()
        )
        self.assertEqual(isinstance(i, Identifier), True)
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_identifier_twice_null_dates(self):
        # adding the same identifier twice to
        # an object, with null start and end validity dates
        p = self.create_instance()
        identifier = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)

        p.add_identifiers(
            [
                {"identifier": identifier, "scheme": scheme, "source": faker.uri()},
                {"identifier": identifier, "scheme": scheme, "source": faker.uri()},
            ]
        )
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_non_overlapping_identifiers(self):
        # same scheme, different identifier values
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        p.add_identifiers(
            [
                {
                    "identifier": faker.numerify("OP_######"),
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": faker.numerify("OP_######"),
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(150)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": faker.numerify("OP_######"),
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(250)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.identifiers.count(), 3)

    def test_add_three_overlapping_identifiers(self):
        # same scheme, different identifiers, overlapping dates
        # starting from the first
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        with self.assertRaises(Exception):
            p.add_identifiers(
                [
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": day_1.strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                    },
                ]
            )
        self.assertEqual(p.identifiers.count(), 2)

    def test_add_three_overlapping_identifiers_different_order(self):
        # same scheme, different identifiers, overlapping dates
        # starting from the second
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        with self.assertRaises(Exception):
            p.add_identifiers(
                [
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": day_1.strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                    },
                ]
            )
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_overlapping_identifiers_one_forever(self):
        # same scheme, different identifiers, overlapping dates
        # starting from the first,
        # the second is from forever
        p = self.create_instance()
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        with self.assertRaises(Exception):
            p.add_identifiers(
                [
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": day_1.strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": None,
                        "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": faker.numerify("OP_######"),
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                    },
                ]
            )
        self.assertEqual(p.identifiers.count(), 2)

    def test_add_three_extending_identifiers(self):
        # same scheme, same identifiers, overlapping dates
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        p.add_identifiers(
            [
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_connected_identifiers(self):
        # same scheme, same identifiers, connected dates
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        p.add_identifiers(
            [
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_two_connected_identifiers_one_null(self):
        # same scheme, same identifiers, connected dates
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        p.add_identifiers(
            [
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    "end_date": None,
                },
            ]
        )
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_disconnected_identifiers(self):
        # same scheme, same identifiers, 2 connected dates and 1 disconn.
        # will result in two identifiers
        p = self.create_instance()
        identifier = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        p.add_identifiers(
            [
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(101)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.identifiers.count(), 2)

    def test_add_two_extending_identifiers_one_forever(self):
        # same scheme, same identifiers, extending, one lasts forever
        # will result in a single identifier
        p = self.create_instance()
        identifier = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        p.add_identifiers(
            [
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
                {
                    "identifier": identifier,
                    "scheme": scheme,
                    "source": faker.uri(),
                    "start_date": (day_1 + timedelta(30)).strftime("%Y-%m-%d"),
                    "end_date": None,
                },
            ]
        )
        self.assertEqual(p.identifiers.count(), 1)

    def test_add_three_overlapping_extending_identifiers(self):
        # same scheme, same identifiers, an identifier A that overlaps
        # with two extending identifiers B
        # will result only in A if it's inserted first
        p = self.create_instance()
        identifierA = faker.numerify("OP_######")
        identifierB = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        with self.assertRaises(Exception):
            p.add_identifiers(
                [
                    {
                        "identifier": identifierA,
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(60)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": identifierB,
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": day_1.strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(90)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": identifierB,
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(80)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                    },
                ]
            )
        self.assertEqual(p.identifiers.count(), 1)
        self.assertEqual(p.identifiers.first().identifier, identifierA)

    def test_add_three_overlapping_extending_identifiers_different_order(self):
        # same scheme, same identifiers, an identifier A that overlaps
        # with two extending identifiers B
        # will result only in B if it's inserted first
        p = self.create_instance()
        identifierA = faker.numerify("OP_######")
        identifierB = faker.numerify("OP_######")
        scheme = faker.text(max_nb_chars=128)
        day_1 = faker.date_time_between("-2y", "-1y")

        with self.assertRaises(Exception):
            p.add_identifiers(
                [
                    {
                        "identifier": identifierB,
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": day_1.strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(90)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": identifierA,
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(60)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    },
                    {
                        "identifier": identifierB,
                        "scheme": scheme,
                        "source": faker.uri(),
                        "start_date": (day_1 + timedelta(80)).strftime("%Y-%m-%d"),
                        "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                    },
                ]
            )
        self.assertEqual(p.identifiers.count(), 1)
        self.assertEqual(p.identifiers.first().identifier, identifierB)

    def test_add_identifiers_different_schemes(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append(
                {
                    "identifier": faker.numerify("OP_######"),
                    "scheme": faker.text(max_nb_chars=128),
                    "source": faker.uri(),
                }
            )
        p.add_identifiers(objects)
        self.assertEqual(p.identifiers.count(), 3)

    def test_add_identifiers_custom(self):
        p = self.create_instance()
        identifierA = faker.numerify("OP_######")
        identifierB = faker.numerify("OP_######")

        p.add_identifiers(
            [
                {
                    "identifier": identifierA,
                    "scheme": "ISTAT_CODE_COM",
                    "start_date": "1995-01-01",
                    "end_date": "2006-01-01",
                },
                {"identifier": identifierB, "scheme": "ISTAT_CODE_COM", "start_date": "2010-01-01"},
                {
                    "identifier": identifierA,
                    "scheme": "ISTAT_CODE_COM",
                    "start_date": "2006-01-01",
                    "end_date": "2010-01-01",
                },
            ]
        )
        self.assertEqual(p.identifiers.count(), 2)

    def test_update_identifiers(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append(
                {
                    "identifier": faker.text(max_nb_chars=128),
                    "scheme": faker.text(max_nb_chars=32),
                    "source": faker.uri(),
                }
            )
        p.add_identifiers(objects)
        self.assertEqual(p.identifiers.count(), 3)

        # update one identifier
        test_value = "TESTING"
        objects[0]["identifier"] = test_value

        # remove one object
        objects.pop()

        # append two objects
        objects.append(
            {"identifier": faker.text(max_nb_chars=128), "scheme": faker.text(max_nb_chars=32), "source": faker.uri()}
        )
        objects.append(
            {"identifier": faker.text(max_nb_chars=128), "scheme": faker.text(max_nb_chars=32), "source": faker.uri()}
        )

        # update identifiers
        p.update_identifiers(objects)

        # test total number (3 - 1 + 2 == 4)
        self.assertEqual(p.identifiers.count(), 4)

        # test modified identifier is there
        self.assertTrue(test_value in p.identifiers.values_list("identifier", flat=True))


class ClassificationTestsMixin(object):
    def test_add_classification(self):
        c = ClassificationFactory.create()
        p = self.create_instance()
        p.add_classification_rel(c.id)

        self.assertEqual(isinstance(p.classifications.first(), ClassificationRel), True)
        self.assertEqual(p.classifications.count(), 1)

    def test_add_three_classifications(self):
        scheme = faker.text(max_nb_chars=12)
        new_classifications = []
        for i in range(0, 3):
            cl = ClassificationFactory.create()
            new_classifications.append({"classification": cl.id})

        p = self.create_instance()
        p.add_classifications(new_classifications)
        self.assertEqual(p.classifications.count(), 3)

    def test_add_same_classification_many_times_counts_as_one(self):
        scheme = faker.text(max_nb_chars=12)
        code = faker.text(max_nb_chars=12)
        descr = faker.text(max_nb_chars=256)

        cl = Classification.objects.create(scheme=scheme, code=code, descr=descr)

        classifications = [{"classification": cl.id}, {"classification": cl.id}]
        p = self.create_instance()
        p.add_classifications(classifications)

        p.add_classification(scheme=scheme, code=code, descr=descr)

        self.assertEqual(p.classifications.count(), 1)

    def test_update_classifications(self):
        scheme = faker.text(max_nb_chars=12)
        new_classifications = []
        for _ in range(3):
            cl = ClassificationFactory.create()
            new_classifications.append({"classification": cl.id})
        p = self.create_instance()
        p.update_classifications(new_classifications)
        self.assertEqual(p.classifications.count(), 3)

        # remove one object
        objects = list(p.classifications.values())[:-1]
        for obj in objects:
            obj["classification"] = obj.pop("classification_id")
        p.update_classifications(objects)
        self.assertEqual(p.classifications.count(), 2)

        # append one object
        cl = Classification.objects.create(
            scheme=scheme, code=faker.text(max_nb_chars=12), descr=faker.text(max_nb_chars=256)
        )
        objects.append({"classification": cl.id})
        p.update_classifications(objects)
        self.assertEqual(p.classifications.count(), 3)


class LinkTestsMixin(object):
    def test_add_link(self):
        p = self.create_instance()
        l = p.add_link(url=faker.uri(), note=faker.text(max_nb_chars=500))
        self.assertEqual(p.links.count(), 1)
        self.assertEqual(isinstance(l, Link), True)
        self.assertEqual(isinstance(p.links.first(), LinkRel), True)

    def test_add_links(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append({"url": faker.uri(), "note": faker.text(max_nb_chars=500)})
        p.add_links(objects)
        self.assertEqual(p.links.count(), 3)

    def test_add_same_link_twice_counts_as_one(self):
        p = self.create_instance()
        url = faker.uri()
        note = faker.text(max_nb_chars=500)

        p.add_links([{"url": url, "note": note}, {"url": url, "note": note}])
        self.assertEqual(p.links.count(), 1)

    def test_update_links(self):
        p = self.create_instance()
        objects = []
        for n in range(3):
            objects.append({"url": faker.uri(), "note": faker.text(max_nb_chars=500)})
        p.add_links(objects)
        self.assertEqual(p.links.count(), 3)

        # transform the current objects
        # to be used in upload_links method
        objects = list(p.links.values())
        for obj in objects:
            link = Link.objects.get(pk=obj.pop("link_id"))
            obj["link"] = {"id": link.id, "url": link.url, "note": link.note}

        # delete one object
        deleted = objects.pop()

        # update one link
        test_note = "TEST"
        objects[0]["link"]["note"] = test_note

        # add two new links
        objects.append({"link": {"note": faker.paragraph(2), "url": faker.uri()}})
        objects.append({"link": {"note": faker.paragraph(2), "url": faker.uri()}})

        # now call update_links
        p.update_links(objects)

        self.assertEqual(p.links.count(), 5)
        self.assertTrue(test_note in p.links.values_list("link__note", flat=True))


class SourceTestsMixin(object):
    def test_add_source(self):
        p = self.create_instance()
        s = p.add_source(url=faker.uri(), note=faker.text(max_nb_chars=500))
        self.assertEqual(p.sources.count(), 1)
        self.assertEqual(isinstance(s, Source), True)
        self.assertEqual(isinstance(p.sources.first(), SourceRel), True)

    def test_add_sources(self):
        p = self.create_instance()

        objects = []
        for n in range(3):
            objects.append({"url": faker.uri(), "note": faker.text(max_nb_chars=500)})
        p.add_sources(objects)
        self.assertEqual(p.sources.count(), 3)

    def test_add_same_source_twice_counts_as_one(self):
        p = self.create_instance()
        url = faker.uri()
        note = faker.text(max_nb_chars=500)

        p.add_sources([{"url": url, "note": note}, {"url": url, "note": note}])
        self.assertEqual(p.sources.count(), 1)

    def test_update_sources(self):
        p = self.create_instance()
        objects = []
        for _ in range(3):
            objects.append({"url": faker.uri(), "note": faker.text(max_nb_chars=500)})
        p.add_sources(objects)
        p.save()
        self.assertEqual(p.sources.count(), 3)

        # transform the current objects
        # to be used in upload_sources method
        objects = list(p.sources.values())
        for obj in objects:
            source = Source.objects.get(pk=obj.pop("source_id"))
            obj["source"] = {"id": source.id, "url": source.url, "note": source.note}

        # delete one object
        deleted = objects.pop()

        # update one source
        test_note = "TEST"
        objects[0]["source"]["note"] = test_note

        # add two new sources
        objects.append({"source": {"note": faker.paragraph(2), "url": faker.uri()}})
        objects.append({"source": {"note": faker.paragraph(2), "url": faker.uri()}})

        # now call update_sources
        p.update_sources(objects)

        self.assertEqual(p.sources.count(), 5)
        self.assertTrue(test_note in p.sources.values_list("source__note", flat=True))


class PersonTestCase(
    ContactDetailTestsMixin,
    OtherNameTestsMixin,
    IdentifierTestsMixin,
    LinkTestsMixin,
    SourceTestsMixin,
    DateframeableTests,
    TimestampableTests,
    PermalinkableTests,
    TestCase,
):
    model = Person
    object_name = "person"

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": u"test instance"})
        if "start_date" in kwargs:
            kwargs.update({"birth_date": kwargs["start_date"]})
        if "end_date" in kwargs:
            kwargs.update({"death_date": kwargs["end_date"]})
        p = PersonFactory.create(**kwargs)
        return p

    def test_add_membership(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        p.add_membership(o)
        self.assertEqual(p.memberships.count(), 1)

    def test_add_membership_with_electoral_event(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()

        day_1 = faker.date_time_between("-2y", "-1y")
        start_date = day_1.strftime("%Y-%m-%d")
        election_date = (day_1 - timedelta(15)).strftime("%Y-%m-%d")
        election_date_fmt = (day_1 - timedelta(15)).strftime("%d/%m/%Y")
        electoral_event = KeyEventTestCase().create_instance(
            name="Elezioni comunali del {0}".format(election_date_fmt), start_date=election_date
        )

        p.add_membership(o, start_date=start_date, electoral_event=electoral_event)
        m = p.memberships.first()
        self.assertEqual(m.start_date, start_date)
        self.assertEqual(m.electoral_event.start_date, election_date)

    def test_add_membership_with_date(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()

        start_date = faker.date()
        p.add_membership(o, start_date=start_date)
        m = p.memberships.first()
        self.assertEqual(m.start_date, start_date)

    def test_add_membership_with_dates(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()

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
        o = OrganizationFactory.create()

        start_date = faker.date()
        end_date = faker.date()
        if start_date < end_date:
            start_date, end_date = end_date, start_date

        with self.assertRaises(Exception):
            p.add_membership(o, start_date=start_date, end_date=end_date)

    def test_add_multiple_memberships_donot_duplicate(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        ms = [{"organization": o}] * 3
        p.add_memberships(ms)
        self.assertEqual(p.memberships.count(), 1)
        self.assertEqual(p.organizations_memberships.count(), 1)
        self.assertEqual(o.memberships.count(), 1)

    def test_add_multiple_overlapping_memberships_donot_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()

        p.add_memberships(
            [
                {
                    "organization": o,
                    "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "organization": o,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
                {
                    "organization": o,
                    "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 1)

    def test_add_multiple_overlapping_memberships_do_duplicate_if_allowed(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()

        p.add_memberships(
            [
                {
                    "organization": o,
                    "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "organization": o,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    "allow_overlap": True,
                },
                {
                    "organization": o,
                    "start_date": (day_1 + timedelta(100)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 2)

    def test_add_multiple_nonoverlapping_memberships_do_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()

        p.add_memberships(
            [
                {
                    "organization": o,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(30)).strftime("%Y-%m-%d"),
                },
                {
                    "organization": o,
                    "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(90)).strftime("%Y-%m-%d"),
                },
                {
                    "organization": o,
                    "start_date": (day_1 + timedelta(90)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 3)

    def test_add_specific_role(self):
        pe = self.create_instance(name=faker.name(), birth_date=faker.year())
        org = OrganizationFactory.create()
        po = Post.objects.create(label=u"CEO", organization=org)
        pe.add_role(po)
        self.assertEqual(pe.memberships.count(), 1)
        self.assertEqual(pe.roles_held.count(), 1)
        self.assertEqual(org.posts_available.count(), 1)

    def test_add_generic_role(self):
        pe = self.create_instance(name=faker.name(), birth_date=faker.year())
        org = OrganizationFactory.create()
        po = Post.objects.create(label=u"CEO")
        pe.add_role(po, organization=org)
        self.assertEqual(pe.memberships.count(), 1)
        self.assertEqual(pe.roles_held.count(), 1)
        self.assertEqual(org.posts_available.count(), 1)

    def test_add_specific_role_fails_if_no_organization_in_post(self):
        """A generic Post cannot be used to add a specific role"""
        pe = self.create_instance(name=faker.name(), birth_date=faker.year())
        po = Post.objects.create(label=u"CEO")
        with self.assertRaises(Exception):
            pe.add_role(po)

    def test_add_generic_role_fails_if_organization_in_post(self):
        """A specific Post cannot be used to add a generic role"""
        pe = self.create_instance(name=faker.name(), birth_date=faker.year())
        org1 = OrganizationFactory.create()
        org2 = OrganizationFactory.create()
        po = Post.objects.create(label=u"CEO", organization=org1)
        with self.assertRaises(Exception):
            pe.add_role(po, organization=org2)

    def test_add_role_returns_none_if_role_not_added(self):
        pe = self.create_instance(name=faker.name(), birth_date=faker.year())
        org = OrganizationFactory.create()
        po = Post.objects.create(label=u"CEO", organization=org)

        # the first time add_role returns the membership
        m = pe.add_role(po)
        self.assertEqual(isinstance(m, Membership), True)

        # when the role exists, no new membership is generated and returned
        m = pe.add_role(po)
        self.assertIsNone(m)

    def test_add_multiple_overlapping_roles_donot_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate")

        p.add_roles(
            [
                {
                    "post": po,
                    "organization": o,
                    "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "organization": o,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 1)

    def test_add_multiple_overlapping_roles_do_duplicate_if_allowed(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate")

        p.add_roles(
            [
                {
                    "post": po,
                    "organization": o,
                    "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "organization": o,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                    "allow_overlap": True,
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 2)

    def test_add_multiple_nonoverlapping_roles_do_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate")

        p.add_roles(
            [
                {
                    "post": po,
                    "organization": o,
                    "start_date": (day_1 + timedelta(125)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(140)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "organization": o,
                    "start_date": (day_1 + timedelta(75)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "organization": o,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(75)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 3)

    def test_add_multiple_overlapping_specific_roles_donot_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate", organization=o)

        p.add_roles(
            [
                {
                    "post": po,
                    "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 1)

    def test_add_multiple_overlapping_roles_with_null_end_dates_donot_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = PersonFactory()
        o = OrganizationFactory()
        po = Post.objects.create(label=u"Associate", organization=o)

        p.add_role(po, start_date=(day_1 + timedelta(40)).strftime("%Y-%m-%d"), end_date=None)
        p.add_role(po, start_date=(day_1).strftime("%Y-%m-%d"), end_date=None)
        p.add_role(po, start_date=(day_1 + timedelta(80)).strftime("%Y-%m-%d"), end_date=None)
        self.assertEqual(p.memberships.count(), 1)
        self.assertEqual(p.memberships.first().start_date, (day_1 + timedelta(40)).strftime("%Y-%m-%d"))

    def test_add_multiple_nonoverlapping_specific_roles_do_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate", organization=o)

        p.add_roles(
            [
                {
                    "post": po,
                    "start_date": (day_1 + timedelta(72)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(72)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "start_date": (day_1 + timedelta(122)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(140)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 3)

    def test_add_multiple_overlapping_roles_with_different_labels_do_duplicate_when_check_label_is_true(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate", organization=o)

        p.add_roles(
            [
                {
                    "post": po,
                    "label": faker.sentence(nb_words=3),
                    "start_date": (day_1 + timedelta(72)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                    "check_label": True,
                },
                {
                    "post": po,
                    "label": faker.sentence(nb_words=3),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                    "check_label": True,
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 2)

    def test_add_multiple_overlapping_roles_with_different_labels_do_not_duplicate_when_check_label_is_false(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate", organization=o)

        p.add_roles(
            [
                {
                    "post": po,
                    "label": faker.sentence(nb_words=3),
                    "start_date": (day_1 + timedelta(72)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "label": faker.sentence(nb_words=3),
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 1)

    def test_add_multiple_overlapping_roles_with_same_labels_do_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate", organization=o)
        label = faker.sentence(nb_words=3)

        p.add_roles(
            [
                {
                    "post": po,
                    "label": label,
                    "start_date": (day_1 + timedelta(72)).strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
                },
                {
                    "post": po,
                    "label": label,
                    "start_date": day_1.strftime("%Y-%m-%d"),
                    "end_date": (day_1 + timedelta(200)).strftime("%Y-%m-%d"),
                },
            ]
        )
        self.assertEqual(p.memberships.count(), 1)

    def test_add_role_on_behalf_of(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o1 = OrganizationFactory.create()
        o2 = OrganizationFactory.create()
        r = o1.add_post(label=u"Director", other_label=u"DIR")
        p.add_role_on_behalf_of(r, o2)
        self.assertEqual(p.memberships.first().on_behalf_of, o2)

    def test_add_multiple_overlapping_roles_onbehalfof_donot_duplicate(self):
        day_1 = faker.date_time_between("-2y", "-1y")
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        o = OrganizationFactory.create()
        ob = OrganizationFactory.create()
        po = Post.objects.create(label=u"Associate")
        r1 = {
            "post": po,
            "organization": o,
            "behalf_organization": ob,
            "start_date": (day_1 + timedelta(40)).strftime("%Y-%m-%d"),
            "end_date": (day_1 + timedelta(120)).strftime("%Y-%m-%d"),
        }
        r2 = {
            "post": po,
            "organization": o,
            "behalf_organization": ob,
            "start_date": day_1.strftime("%Y-%m-%d"),
            "end_date": (day_1 + timedelta(50)).strftime("%Y-%m-%d"),
        }
        p.add_role_on_behalf_of(**r1)
        p.add_role_on_behalf_of(**r2)
        self.assertEqual(p.memberships.count(), 1)

    def test_post_organizations(self):
        p = self.create_instance(name=faker.name(), birth_date=faker.year())
        for i in range(3):
            o = OrganizationFactory.create()
            r = Post.objects.create(label=faker.word().title(), organization=o)
            p.add_role(r)

        self.assertEqual(p.organizations_has_role_in().count(), 3)

    def test_it_copies_birth_date_after_saving(self):
        given_name = faker.first_name()
        family_name = faker.last_name()
        name = "{0} {1}".format(given_name, family_name)
        pr = Person(given_name=given_name, family_name=family_name, name=name, birth_date=faker.year())
        self.assertIsNone(pr.start_date)
        pr.save()
        self.assertEqual(pr.start_date, pr.birth_date)

    def test_it_copies_death_date_after_saving(self):
        given_name = faker.first_name()
        family_name = faker.last_name()
        name = "{0} {1}".format(given_name, family_name)
        pr = Person(given_name=given_name, family_name=family_name, name=name, birth_date=faker.year())
        self.assertIsNone(pr.end_date)
        pr.save()
        self.assertEqual(pr.end_date, pr.death_date)

    def test_add_relationship(self):
        p1 = self.create_instance()
        p2 = self.create_instance()
        p1.add_relationship(dest_person=p2, classification="FRIENDSHIP", weight=PersonalRelationship.WEIGHTS.negative)
        self.assertEqual(p1.related_persons.count(), 1)
        self.assertEqual(p1.related_persons.first(), p2)


class OrganizationTestCase(
    ContactDetailTestsMixin,
    OtherNameTestsMixin,
    IdentifierTestsMixin,
    ClassificationTestsMixin,
    LinkTestsMixin,
    SourceTestsMixin,
    DateframeableTests,
    TimestampableTests,
    TestCase,
):
    model = Organization
    object_name = "organization"

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": u"test instance"})
        if "start_date" in kwargs:
            kwargs.update({"founding_date": kwargs["start_date"]})
        if "end_date" in kwargs:
            kwargs.update({"dissolution_date": kwargs["end_date"]})
        return Organization.objects.create(**kwargs)

    def test_add_key_event(self):
        o = self.create_instance()
        ke = LegislatureEventFactory()
        ke_ret = o.add_key_event_rel(ke.id)
        self.assertEqual(o.key_events.count(), 1)
        self.assertEqual(isinstance(ke_ret, KeyEventRel), True)
        self.assertEqual(isinstance(o.key_events.first(), KeyEventRel), True)
        self.assertEqual(isinstance(o.key_events.first().key_event, KeyEvent), True)
        self.assertEqual(o.key_events.first().key_event, ke)

    def test_add_key_events(self):
        o = self.create_instance()
        objects = [
            {"key_event": LegislatureEventFactory().id},
            {"key_event": ElectoralEventFactory().id},
            {"key_event": XadmEventFactory().id},
        ]
        o.add_key_events(objects)
        self.assertEqual(o.key_events.count(), 3)

    def test_add_key_event_twice_fails(self):
        with self.assertRaises(ValidationError):
            event_a = LegislatureEventFactory()
            event_b = LegislatureEventFactory(start_date=event_a.start_date)

    def test_update_key_events(self):
        o = self.create_instance()
        objects = [
            {"key_event": LegislatureEventFactory().id},
            {"key_event": LegislatureEventFactory().id},
            {"key_event": LegislatureEventFactory().id},
        ]
        o.add_key_events(objects)
        self.assertEqual(o.key_events.count(), 3)

        # delete one object
        objects.pop()

        # append two objects
        objects.append({"key_event": LegislatureEventFactory().id})
        objects.append({"key_event": LegislatureEventFactory().id})

        # update identifiers
        o.update_key_events(objects)

        # test total number of KeyEvents related to o (3 - 1 + 2 == 4)
        self.assertEqual(o.key_events.count(), 4)

        # test total number of KeyEvents in DB (3 + 2 == 5)
        self.assertEqual(KeyEvent.objects.count(), 5)

    def test_add_member(self):
        o = self.create_instance(name=faker.company())
        p = PersonFactory.create()
        o.add_member(p, start_date=faker.year())
        self.assertEqual(o.person_members.count(), 1)
        self.assertEqual(len(o.members), 1)

    def test_add_members(self):
        o = self.create_instance(name=faker.company())
        ps = [PersonFactory.create(), PersonFactory.create(), PersonFactory.create()]
        o.add_members(ps)
        self.assertEqual(o.person_members.count(), 3)
        self.assertEqual(len(o.members), 3)

    def test_add_member_organization(self):
        o = self.create_instance(name=faker.company())
        om = OrganizationFactory.create()
        o.add_member(om)
        self.assertEqual(o.memberships.count(), 1)
        self.assertEqual(om.organizations_memberships.count(), 1)
        self.assertEqual(len(o.members), 1)
        self.assertEqual(o.organization_members.count(), 1)

    def test_add_member_organization_twice(self):
        o = self.create_instance(name=faker.company())
        om = OrganizationFactory.create()
        o.add_member(om)
        o.add_member(om)
        self.assertEqual(o.memberships.count(), 1)
        self.assertEqual(om.organizations_memberships.count(), 1)
        self.assertEqual(len(o.members), 1)
        self.assertEqual(o.organization_members.count(), 1)

    def test_add_membership_to_organization(self):
        om = self.create_instance(name=faker.company())
        o = OrganizationFactory.create()
        om.add_membership(o)
        self.assertEqual(om.organizations_memberships.count(), 1)
        self.assertEqual(len(o.members), 1)

    def test_add_mixed_members(self):
        o = self.create_instance(name=faker.company())
        ms = [
            PersonFactory.create(),
            Organization.objects.create(name=faker.company(), founding_date=faker.year()),
            PersonFactory.create(),
        ]
        o.add_members(ms)
        self.assertEqual(len(o.members), 3)

    def test_add_owner_person(self):
        o = self.create_instance(name=faker.company())
        p = PersonFactory.create()
        o.add_owner(p, percentage=0.1503)
        self.assertEqual(o.person_owners.count(), 1)
        self.assertEqual(p.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

    def test_add_owner_organization(self):
        o = self.create_instance(name=faker.company())
        om = OrganizationFactory.create()
        o.add_owner(om, percentage=0.1705)
        self.assertEqual(o.organization_owners.count(), 1)
        self.assertEqual(om.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

    def test_add_ownership_to_organization(self):
        o = self.create_instance(name=faker.company())
        om = self.create_instance(name=faker.company())
        om.add_ownership(o, percentage=0.2753)
        self.assertEqual(o.organization_owners.count(), 1)
        self.assertEqual(om.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

    def test_add_ownership_to_person(self):
        o = self.create_instance(name=faker.company())
        p = PersonFactory.create()
        p.add_ownership(o, percentage=0.51)
        self.assertEqual(p.ownerships.count(), 1)
        self.assertEqual(len(o.owners), 1)

    def test_add_wrong_member_type(self):
        o = self.create_instance(name=faker.company())
        a = Area.objects.create(name=faker.city(), identifier=faker.numerify("####"), classification=faker.word())
        with self.assertRaises(Exception):
            o.add_member(a)

    def test_add_post(self):
        o = self.create_instance(name=faker.company())
        o.add_post(label=u"CEO")
        self.assertEqual(o.posts.count(), 1)

    def test_add_posts(self):
        o = self.create_instance(name=faker.company())
        o.add_posts([{"label": u"Presidente"}, {"label": u"Vicepresidente"}])
        self.assertEqual(o.posts.count(), 2)

    def test_add_wrong_owner_type(self):
        o = self.create_instance(name=faker.company())
        a = Area.objects.create(name=faker.city())
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
        o1 = self.create_instance(start_date="1962")
        o2 = self.create_instance(start_date="1978")
        o = self.create_instance()

        self.assertEqual(o1.is_active_now, True)
        self.assertEqual(o.is_active_now, True)
        self.assertEqual(o.old_orgs.count(), 0)
        self.assertEqual(o1.new_orgs.count(), 0)

        o.merge_from(o1, o2, moment="2014-04-23")
        self.assertEqual(o.is_active_now, True)
        self.assertEqual(o1.is_active_now, False)
        self.assertEqual(o.old_orgs.count(), 2)
        self.assertEqual(o1.new_orgs.count(), 1)
        self.assertEqual(o.start_date, "2014-04-23")

    def test_split_into_list(self):
        o = self.create_instance(start_date="1968")
        o1 = self.create_instance()
        o2 = self.create_instance()

        self.assertEqual(o1.is_active_now, True)
        self.assertEqual(o.is_active_now, True)
        self.assertEqual(o.old_orgs.count(), 0)
        self.assertEqual(o1.new_orgs.count(), 0)

        o.split_into(o1, o2, moment="2014-04-23")
        self.assertEqual(o.is_active_now, False)
        self.assertEqual(o1.is_active_now, True)
        self.assertEqual(o1.old_orgs.count(), 1)
        self.assertEqual(o.new_orgs.count(), 2)
        self.assertEqual(o.end_date, "2014-04-23")
        self.assertEqual(o1.start_date, "2014-04-23")


class PostTestCase(
    ContactDetailTestsMixin, LinkTestsMixin, SourceTestsMixin, DateframeableTests, TimestampableTests, TestCase
):
    model = Post

    def create_instance(self, **kwargs):
        if "label" not in kwargs:
            kwargs.update({"label": u"test instance"})
        if "other_label" not in kwargs:
            kwargs.update({"other_label": u"TI,TEST"})

        return Post.objects.create(**kwargs)

    def test_add_person(self):
        r = self.create_instance(
            label=u"Chief Executive Officer", other_label=u"CEO,AD", organization=OrganizationFactory.create()
        )
        p = PersonFactory.create()
        r.add_person(p, start_date=faker.year())
        self.assertEqual(r.holders.count(), 1)
        self.assertEqual(p.roles_held.count(), 1)

    def test_add_person_on_behalf_of(self):
        r = self.create_instance(label=u"Director", other_label=u"DIR", organization=OrganizationFactory.create())

        o2 = OrganizationFactory.create()
        p = PersonFactory.create(birth_date=faker.year())
        r.add_person_on_behalf_of(p, o2)
        self.assertEqual(r.memberships.first().on_behalf_of, o2)

    def test_add_appointer(self):
        r = self.create_instance(label=u"Director", other_label=u"DIR", organization=OrganizationFactory.create())
        o2 = OrganizationFactory.create()
        r1 = o2.add_post(label="President", other_label="PRES")
        r.add_appointer(r1)
        self.assertEqual(r.appointed_by, r1)
        self.assertIn(r, list(r1.appointees.all()))


class MembershipTestCase(
    ContactDetailTestsMixin, LinkTestsMixin, SourceTestsMixin, DateframeableTests, TimestampableTests, TestCase
):
    model = Membership

    def create_instance(self, **kwargs):
        if "person" not in kwargs:
            p = PersonFactory.create()
            kwargs.update({"person": p})
        if "organization" not in kwargs:
            o = OrganizationFactory.create()
            kwargs.update({"organization": o})

        m = Membership.objects.create(**kwargs)
        return m

    def test_missing_organization(self):
        p = PersonFactory.create()
        m = Membership(person=p, label=faker.word())
        with self.assertRaises(Exception):
            m.save()

    def test_missing_member(self):
        o = OrganizationFactory.create()
        m = Membership(organization=o, label=faker.word())
        with self.assertRaises(Exception):
            m.save()


class OwnershipTestCase(SourceTestsMixin, DateframeableTests, TimestampableTests, TestCase):
    model = Ownership

    def create_instance(self, **kwargs):
        if "owner_person" not in kwargs:
            p = PersonFactory.create()
            kwargs.update({"owner_person": p})
        if "owned_organization" not in kwargs:
            o = OrganizationFactory.create()
            kwargs.update({"owned_organization": o})
        if "percentage" not in kwargs:
            kwargs.update({"percentage": 0.42})

        return Ownership.objects.create(**kwargs)

    def test_missing_organization(self):
        p = PersonFactory.create()
        m = Ownership(owner_person=p, percentage=0.42)
        with self.assertRaises(Exception):
            m.save()

    def test_missing_owner(self):
        o = OrganizationFactory.create()
        m = Ownership(owned_organization=o, percentage=0.42)
        with self.assertRaises(Exception):
            m.save()


class KeyEventTestCase(DateframeableTests, TimestampableTests, TestCase):
    model = KeyEvent

    def __init__(self, methodName="runTest"):
        """Create an instance of the class that will use the named test
           method when executed. Raises a ValueError if the instance does
           not have a method with the specified name.
        """
        self._testMethodName = methodName
        self._testMethodDoc = "No test"
        try:
            super(KeyEventTestCase, self).__init__(methodName)
        except ValueError:
            try:
                testMethod = getattr(self, methodName)
            except AttributeError:
                if methodName != "runTest":
                    # we allow instantiation with no explicit method name
                    # but not an *incorrect* or missing method name
                    raise ValueError("no such test method in %s: %s" % (self.__class__, methodName))
            else:
                self._testMethodDoc = testMethod.__doc__

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": "Elezioni amministrative 2017"})
        return KeyEvent.objects.create(**kwargs)

    def test_add_general_result(self):
        e = self.create_instance()
        general_result = {
            "n_eligible_voters": 58623,
            "n_ballots": 48915,
            "perc_turnout": 48915 / 58623,
            "perc_valid_votes": 0.84,
            "perc_null_votes": 0.11,
            "perc_blank_votes": 0.05,
        }
        e.add_result(organization=OrganizationFactory.create(), **general_result)
        self.assertEqual(e.results.count(), 1)
        self.assertLess(e.results.first().perc_turnout, 0.90)

    def test_add_general_result_in_constituency(self):
        e = self.create_instance()
        general_result = {
            "n_eligible_voters": 58623,
            "n_ballots": 48915,
            "perc_turnout": 48915 / 58623,
            "perc_valid_votes": 0.84,
            "perc_null_votes": 0.11,
            "perc_blank_votes": 0.05,
        }
        e.add_result(
            organization=OrganizationFactory.create(),
            constituency=Area.objects.create(
                name="Circoscrizione Lazio 1 della Camera",
                identifier="LAZIO1-CAMERA",
                classification="Circoscrizione elettorale",
            ),
            **general_result
        )
        self.assertEqual(e.results.count(), 1)
        self.assertLess(e.results.first().perc_turnout, 0.90)
        self.assertIsInstance(e.results.first().constituency, Area)

    def test_add_list_result(self):
        e = self.create_instance()
        list_result = {"n_preferences": 1313, "perc_preferences": 0.13}
        e.add_result(organization=OrganizationFactory.create(), list=OrganizationFactory.create(), **list_result)
        self.assertEqual(e.results.count(), 1)
        self.assertIsInstance(e.results.first().list, Organization)

    def test_add_candidate_result(self):
        e = self.create_instance()
        candidate_result = {"n_preferences": 1563, "perc_preferences": 0.16, "is_elected": True}
        e.add_result(
            organization=OrganizationFactory.create(),
            list=OrganizationFactory.create(),
            candidate=PersonFactory.create(),
            **candidate_result
        )
        self.assertEqual(e.results.count(), 1)
        self.assertIsInstance(e.results.first().list, Organization)
        self.assertIsInstance(e.results.first().candidate, Person)


class AreaTestCase(
    SourceTestsMixin,
    LinkTestsMixin,
    OtherNameTestsMixin,
    IdentifierTestsMixin,
    PermalinkableTests,
    DateframeableTests,
    TimestampableTests,
    TestCase,
):
    model = Area

    def create_instance(self, **kwargs):
        if "name" not in kwargs:
            kwargs.update({"name": faker.city()})
        if "classification" not in kwargs:
            kwargs.update({"classification": "ADM3"})
        if "istat_classification" not in kwargs:
            kwargs.update({"istat_classification": "COM"})
        if "identifier" not in kwargs:
            kwargs.update({"identifier": faker.sha1()})
        return Area.objects.create(**kwargs)

    def test_add_i18n_name(self):
        a = self.create_instance(name="Bolzano-Bozen", classification="city", identifier="021008")

        it_language = Language.objects.create(name="Italian", iso639_1_code="it")
        de_language = Language.objects.create(name="German", iso639_1_code="de")

        a.add_i18n_name("Bolzano", it_language)
        a.add_i18n_name("Bozen", de_language)
        self.assertEqual(a.i18n_names.get(language=it_language).name, "Bolzano")
        self.assertEqual(a.i18n_names.get(language=de_language).name, "Bozen")

    def test_merge_from_list(self):
        a1 = self.create_instance(start_date="1962")
        a2 = self.create_instance(start_date="1978")
        a = self.create_instance()

        self.assertEqual(a1.is_active_now, True)
        self.assertEqual(a.is_active_now, True)
        self.assertEqual(a.old_places.count(), 0)
        self.assertEqual(a1.new_places.count(), 0)

        a.merge_from(a1, a2, moment="2014-04-23")
        self.assertEqual(a.is_active_now, True)
        self.assertEqual(a1.is_active_now, False)
        self.assertEqual(a.old_places.count(), 2)
        self.assertEqual(a1.new_places.count(), 1)
        self.assertEqual(a.start_date, "2014-04-23")

    def test_split_into_list(self):
        a = self.create_instance(start_date="1968")
        a1 = self.create_instance()
        a2 = self.create_instance()

        self.assertEqual(a1.is_active_now, True)
        self.assertEqual(a.is_active_now, True)
        self.assertEqual(a.old_places.count(), 0)
        self.assertEqual(a1.new_places.count(), 0)

        a.split_into(a1, a2, moment="2014-04-23")
        self.assertEqual(a.is_active_now, False)
        self.assertEqual(a1.is_active_now, True)
        self.assertEqual(a1.old_places.count(), 1)
        self.assertEqual(a.new_places.count(), 2)
        self.assertEqual(a.end_date, "2014-04-23")
        self.assertEqual(a1.start_date, "2014-04-23")


class OriginalProfessionTestCase(TestCase):
    model = OriginalProfession

    def test_person_with_orig_prof_has_no_prof(self):
        or_pro = OriginalProfessionFactory()
        person = PersonFactory()
        person.original_profession = or_pro
        person.save()

        self.assertEqual(person.profession is None, True)
        self.assertEqual(or_pro.persons_with_this_original_profession.count() > 0, True)

    # def test_normalized_profession_is_cached_by_signal(self):
    #     pro = ProfessionFactory()
    #     or_pro = OriginalProfessionFactory()
    #     person = PersonFactory(original_profession=or_pro)
    #     self.assertEqual(person.profession is None, True)
    #
    #     or_pro.normalized_profession = pro
    #     or_pro.save()
    #     self.assertEqual(person.profession is None, False)
