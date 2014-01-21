popolo
========================


.. image:: https://travis-ci.org/ciudadanointeligente/django-popolo.png?branch=master
  :target: https://travis-ci.org/ciudadanointeligente/django-popolo

.. image:: https://coveralls.io/repos/ciudadanointeligente/django-popolo/badge.png
  :target: https://coveralls.io/r/ciudadanointeligente/django-popolo


Welcome to the documentation for django-popolo!


**django-popolo** is a django-based implementation of the
`Popolo's open government data specifications <http://popoloproject.com/>`_.

It is developed as a django application to be deployed directly within django projects.

It will allow web developers using it to manage and store data according to Popolo's specifications.

The standard sql-oriented django ORM will be used.

Project is under way and any help is welcome.


Installation
------------
To install ``django-popolo`` as a third party app within a django project, you need to add it to the django project's requirements.txt.
There is no public python package, yet, so you'll need to install this directly from github.

Since ``django-popolo`` requires ``django-model-utils`` and ``django-autoslug``, you need to put the requirement for ``django-popolo``
after the requirements for django::

    Django
    ...
    -e git+git@github.com:openpolis/django-popolo.git#egg=django_popolo-dev


Running the Tests
------------------------------------

You can run the tests with via::

    python setup.py test

or::

    python runtests.py
