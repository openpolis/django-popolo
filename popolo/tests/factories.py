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

    il = list(map(lambda x: x[0], Area.ISTAT_CLASSIFICATIONS))

    name = factory.Faker('city')
    identifier = factory.Faker('pystr', max_chars=4)
    classification = factory.Faker('pystr', max_chars=5)
    istat_classification = random.choice(il),
    inhabitants = factory.Faker('pyint')
