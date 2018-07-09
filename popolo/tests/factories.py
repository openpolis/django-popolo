# coding=utf-8
import factory
from faker import Factory
import random

from popolo.models import Area

faker = Factory.create('it_IT')  # a factory to create fake names for tests


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Person'

    gender = random.choice(['M', 'F'])
    given_name = factory.Faker('first_name')
    family_name = factory.Faker('last_name')
    name = factory.LazyAttribute(lambda o: o.given_name + ' ' + o.family_name)
    birth_date = factory.Faker('date', pattern="%Y-%m-%d", end_datetime="-27y")
    birth_location = factory.Faker('city')
    additional_name = factory.Faker('first_name')
    email = factory.Faker('ascii_safe_email')
    biography = factory.Faker('paragraph', nb_sentences=7, variable_nb_sentences=True, ext_word_list=None)


class AreaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Area'

    name = factory.Faker('city')
    identifier = factory.Faker('pystr', max_chars=4)
    classification = factory.Faker('pystr', max_chars=5)
    inhabitants = factory.Faker('pyint')

    @factory.lazy_attribute
    def istat_classification(self):
        return random.choice([a[0] for a in Area.ISTAT_CLASSIFICATIONS])


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Organization'

    name = factory.Faker('company')
    identifier = factory.Faker('pystr', max_chars=11)


class ElectoralEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.KeyEvent'

    name = factory.Faker('sentence')
    identifier = factory.Faker('pystr', max_chars=11)
    event_type = 'ELE'


class LegislatureEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.KeyEvent'

    name = factory.Faker('sentence')
    identifier = factory.Faker('pystr', max_chars=11)
    event_type = 'LEG'


class XadmEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.KeyEvent'

    name = factory.Faker('sentence')
    identifier = factory.Faker('pystr', max_chars=11)
    event_type = 'XAD'


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Membership'

    label = factory.Faker('sentence', nb_words=8)
    role = factory.Faker('sentence', nb_words=8)

    @factory.lazy_attribute
    def person(self):
        return PersonFactory.create()

    @factory.lazy_attribute
    def organization(self):
        return OrganizationFactory.create()

    @factory.lazy_attribute
    def start_date(self):
        return faker.date_between(start_date='-3y', end_date="-2y").strftime('%Y-%m-%d')

    @factory.lazy_attribute
    def end_date(self):
        return faker.date_between(start_date='-2y', end_date="-1y").strftime('%Y-%m-%d')


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Post'

    label = factory.Faker('sentence', nb_words=8)
    role = factory.Faker('sentence', nb_words=8)

    @factory.lazy_attribute
    def start_date(self):
        return faker.date_between(start_date='-3y', end_date="-2y").strftime('%Y-%m-%d')

    @factory.lazy_attribute
    def end_date(self):
        return faker.date_between(start_date='-2y', end_date="-1y").strftime('%Y-%m-%d')


class ClassificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Classification'

    scheme = factory.Faker('pystr', max_chars=16)
    code = factory.Faker('pystr', max_chars=8)
    descr = factory.Faker('sentence', nb_words=8)


class IdentifierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Identifier'

    scheme = factory.Faker('pystr', max_chars=32)
    identifier = factory.Faker('pystr', max_chars=64)
    source = factory.Faker('url')


class LinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Link'

    url = factory.Faker('url')
    note = factory.Faker('sentence', nb_words=10)


class SourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Source'

    url = factory.Faker('url')
    note = factory.Faker('sentence', nb_words=10)


class OriginalProfessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.OriginalProfession'

    name = factory.Faker('sentence', nb_words=7)


class ProfessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Profession'

    name = factory.Faker('sentence', nb_words=7)


class OriginalEducationLevelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.OriginalEducationLevel'

    name = factory.Faker('sentence', nb_words=7)


class EducationLevelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.EducationLevel'

    name = factory.Faker('sentence', nb_words=7)


class RoleTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.RoleType'

    label = factory.Faker('sentence', nb_words=7)
    priority = factory.Faker('pyint')

    @factory.lazy_attribute
    def classification(self):
        c = ClassificationFactory.create()
        c.scheme = 'FORMA_GIURIDICA_OP'
        return c
