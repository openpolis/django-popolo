# coding=utf-8
import factory
import random

from popolo.models import Area


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'popolo.Person'

    gender = random.choice(['M', 'F'])
    given_name = factory.Faker('first_name')
    family_name = factory.Faker('last_name')
    name = factory.LazyAttribute(lambda o: o.given_name + ' ' + o.family_name)
    birth_date = factory.Faker('date', pattern="%Y-%m-%d", end_datetime="-27y")
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
