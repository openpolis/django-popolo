#!/usr/bin/env python
from setuptools import setup

import popolo

setup(
    name="django-popolo",
    version=popolo.__version__,
    author="Guglielmo Celata",
    author_email="guglielmo@openpolis.it",
    packages=["popolo"],
    include_package_data=True,
    url="http://github.com/openpolis/django-popolo",
    license="AGPL-3.0",
    description=popolo.__doc__,
    classifiers=[
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.2",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
    ],
    long_description=open("./README.md").read(),
    long_description_content_type="text/markdown",
    zip_safe=False,
    install_requires=(
        # Package requirements (pin major versions)
        "django<3.3",  # Django 3.2 LTS - https://github.com/django/django
        "django-autoslug<2",  # https://github.com/justinmayer/django-autoslug
        "django-model-utils<5",  # https://github.com/jazzband/django-model-utils
    ),
    extras_require={
        "test": (
            # Test requirements
            "faker",  # https://github.com/joke2k/faker
            "factory_boy",  # https://github.com/FactoryBoy/factory_boy
        ),
        "dev": (
            # Development requirements
            "black",  # https://github.com/psf/black
            "coverage",  # https://github.com/nedbat/coveragepy
        ),
    },
)
