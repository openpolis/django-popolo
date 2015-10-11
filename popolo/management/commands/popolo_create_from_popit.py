from __future__ import print_function

import re

from django.core.management.base import BaseCommand, CommandError

from popolo.importers.popit import PopItImporter

class Command(PopItImporter, BaseCommand):

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
    # These overridden methods deal with common incompatabilities
    # between what PopIt and django-popolo allow. Those that truncate
    # fields that are too long (the majority of these things) should
    # be removed if the max_length of those fields are increased in
    # django-popolo in the future.

    def update_person(self, person_data):
        new_person_data = person_data.copy()
        # There are quite a lot of summary fields in PopIt that are
        # way longer than 1024 characters.
        new_person_data['summary'] = (person_data.get('summary') or '')[:1024]
        # Surprisingly, quite a lot of PopIt email addresses have
        # extraneous whitespace in them, so strip any out to avoid
        # the 'Enter a valid email address' ValidationError on saving:
        email = person_data.get('email') or None
        if email:
            email = re.sub(r'\s*', '', email)
        new_person_data['email'] = email
        return super(Command, self).update_person(new_person_data)

    def make_contact_detail_dict(self, contact_detail_data):
        new_contact_detail_data = contact_detail_data.copy()
        # There are some contact types that are used in PopIt that are
        # longer than 12 characters...
        new_contact_detail_data['type'] = contact_detail_data['type'][:12]
        return super(Command, self).make_contact_detail_dict(new_contact_detail_data)

    def make_link_dict(self, link_data):
        new_link_data = link_data.copy()
        # There are some really long URLs in PopIt, which exceed the
        # 200 character limit in django-popolo.
        new_link_data['url'] = new_link_data['url'][:200]
        return super(Command, self).make_link_dict(new_link_data)
