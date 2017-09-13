from __future__ import print_function

import re

from django.core.management.base import BaseCommand, CommandError

from popolo.importers.popolo_json import PopoloJSONImporter


class Command(PopoloJSONImporter, BaseCommand):
    def __init__(self, *args, **kwargs):
        # django-popolo has restricted lengths for various fields,
        # whereas PopIt has no such aritrary limits; so, for the
        # import not to fail, we need to truncate them.
        kwargs['truncate'] = 'yes'
        super(Command, self).__init__(*args, **kwargs)

    # This is so that this command works on Django 1.8 as well as
    # earlier versions. See "Changed in Django 1.8" here:
    # https://docs.djangoproject.com/en/1.8/howto/custom-management-commands/
    def add_arguments(self, parser):
        parser.add_argument('args', nargs='+')

    def handle(self, *args, **options):

        if len(args) != 1:
            message = "You must supply a filename with exported PopIt JSON"
            raise CommandError(message)

        popit_export_filename = args[0]

        self.import_from_export_json(popit_export_filename)

    # ------------------------------------------------------------------------
    # This overridden method deals with an awkward incompatability
    # between what PopIt and django-popolo allow.

    def update_person(self, person_data):
        new_person_data = person_data.copy()
        # Surprisingly, quite a lot of PopIt email addresses have
        # extraneous whitespace in them, so strip any out to avoid
        # the 'Enter a valid email address' ValidationError on saving:
        email = person_data.get('email') or None
        if email:
            email = re.sub(r'\s*', '', email)
        new_person_data['email'] = email
        return super(Command, self).update_person(new_person_data)
