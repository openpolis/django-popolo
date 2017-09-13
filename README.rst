popolo
========================


.. image:: https://travis-ci.org/openpolis/django-popolo.svg?branch=master
  :target: https://travis-ci.org/openpolis/django-popolo

.. image:: https://coveralls.io/repos/github/openpolis/django-popolo/badge.svg?branch=master
  :target: https://coveralls.io/github/openpolis/django-popolo?branch=master


Welcome to the documentation for django-popolo!


**django-popolo** is a django-based implementation of the
`Popolo's open government data specifications <http://popoloproject.com/>`_.

It is developed as a django application to be deployed directly within django projects.

It will allow web developers using it to manage and store data according to Popolo's specifications.

The standard sql-oriented django ORM will be used.

Project is under way and any help is welcome.


Installation
------------
To install ``django-popolo`` as a third party app within a django project,
you need to add it to the django project's requirements.txt.
You can do this from GitHub in the usual way, or using the
``django-popolo`` package on PyPI.


Compatibility
-------------


Running the Tests
-----------------

Set up the tests with::

    pip install -r tests_requirements.txt
    python setup.py install

You can run the tests with::

    python setup.py test

or::

    python runtests.py

Notes on mysociety's fork
-------------------------
mysociety/django-popolo is a fork of this project where integer ID's are used
instead of slugs. Otherwise the two projects are functionally equivalent.

