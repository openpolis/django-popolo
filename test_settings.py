"""
Basic Django settings for running tests.
"""

SPATIALITE_LIBRARY_PATH = "mod_spatialite"
DATABASES = {"default": {"ENGINE": "django.contrib.gis.db.backends.spatialite", "NAME": ":memory:"}}
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.gis",
    "popolo.apps.PopoloNoAdminConfig",
]

SITE_ID = 1
SECRET_KEY = "this-is-just-for-tests-so-not-that-secret"
ROOT_URLCONF = "popolo.urls"
