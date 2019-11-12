#!/usr/bin/env python
import sys

import django
from django.conf import settings


if not settings.configured:
    settings.configure(
        SPATIALITE_LIBRARY_PATH='mod_spatialite',
        DATABASES={
            'default': {
                'ENGINE': 'django.contrib.gis.db.backends.spatialite',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=(
            'django.contrib.contenttypes',
            'popolo',
        ),
        SITE_ID=1,
        SECRET_KEY='this-is-just-for-tests-so-not-that-secret',
        ROOT_URLCONF='popolo.urls',
    )


from django.test.utils import get_runner


def runtests():
    if django.VERSION[:2] >= (1, 7):
        django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True, failfast=False)
    failures = test_runner.run_tests(['popolo', ])
    sys.exit(failures)


if __name__ == '__main__':
    runtests()

