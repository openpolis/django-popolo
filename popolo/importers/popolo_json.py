from __future__ import print_function

from contextlib import contextmanager
import json
import sys

from django.utils.six import text_type

from django.apps import apps

NEW_COLLECTIONS = ('organization', 'post', 'person', 'membership', 'area')


@contextmanager
def show_data_on_error(variable_name, data):
    """A context manager to output problematic data on any exception

    If there's an error when importing a particular person, says, it's
    useful to have in the error output that particular structure that
    caused problems. If you wrap the code that processes some data
    structure (a dictionary called 'my_data', say) with this:

        with show_data_on_error('my_data', my_data'):
            ...
            process(my_data)
            ...

    ... then if any exception is thrown in the 'with' block you'll see
    the data that was being processed when it was thrown."""

    try:
        yield
    except:
        message = 'An exception was thrown while processing {0}:'
        print(message.format(variable_name), file=sys.stderr)
        print(json.dumps(data, indent=4, sort_keys=True))
        raise


class PopoloJSONImporter(object):
    """This class helps you to import data from Popolo JSON into django-popolo

    You can use an intance of this class to import data from a Popolo
    JSON file to django-popolo models.  This is useful, for example,
    for importing data from EveryPolitician or from PopIt instances
    (using the /api/v0.1/export.json API endpoint).

    This importer will create Identifier objects that let you access
    the instances of Django models via their IDs in the source data.
    You can customize the prefix used in the scheme of the Identifier
    objects with the id_prefix argument to this class's initializer.
    e.g. if you use id_prefix="popolo:" then each Person will have an
    Identifier with scheme "popolo:person" with their ID from the
    source.  (The default for id_prefix is "popit-".)

    This is designed to be easy to subclass to extend its
    behaviour. For example:

    * If you need to use this importer in a migration, you can
      override the initializer and get_popolo_model_class to return
      the unfrozen model classes instead of the real current model
      classes.

    * If you need to preprocess the data being added you can override
      the methods that transform PopIt to django-popolo data (e.g. you
      could override make_link_dict to truncate excessively long
      URLs.)

    * If you're using multi-table inheritance or explicit one-to-one
      fields to add extra attributes to the django-popolo models, then
      you can add that data by overriding one or more of
      update_person, update_membership, etc.

    """

    TRUNCATE_OPTIONS = {'yes', 'warn', 'exception'}

    def __init__(self, id_prefix=None, truncate='exception', **kwargs):
        super(PopoloJSONImporter, self).__init__()
        if id_prefix is None:
            self.id_prefix = 'popit-'
        else:
            self.id_prefix = id_prefix
        if truncate not in PopoloJSONImporter.TRUNCATE_OPTIONS:
            msg = "Unknown option for truncate '{0}'; it must be one of: {1}"
            raise ValueError(msg.format(
                truncate, PopoloJSONImporter.TRUNCATE_OPTIONS))
        self.truncate = truncate
        # By default we preserve the ID schemes used to identify
        # previously imported data:
        self.id_schemes_to_preserve = {
            'person': {self.id_prefix + 'person'},
            'organization': {self.id_prefix + 'organization'},
            'area': {self.id_prefix + 'area'},
        }
        # And if any extra ID schemes have been requested for
        # preservation, keep them too:
        if kwargs.get('id_schemes_to_preserve'):
            self.add_id_schemes_to_preserve(kwargs['id_schemes_to_preserve'])
        self.observers = []

    def add_id_schemes_to_preserve(self, id_schemes_to_preserve):
        for collection, schemes in id_schemes_to_preserve.items():
            if collection not in NEW_COLLECTIONS:
                raise Exception("Unknown collection: '{}'".format(collection))
            self.id_schemes_to_preserve.setdefault(collection, {})
            self.id_schemes_to_preserve[collection].update(schemes)

    def add_observer(self, observer):
        self.observers.append(observer)

    def notify_observers(self, collection, django_object, created, popolo_data):
        for o in self.observers:
            o.notify(collection, django_object, created, popolo_data)

    def get_popolo_model_class(self, model_name):
        """A default implementation for getting the Popolo model class"""
        return self.get_model_class('popolo', model_name)

    def get_model_class(self, app_label, model_name):
        return apps.get_model(app_label, model_name)

    def get_truncated(self, django_object_or_model_class, field_name, value):
        meta = django_object_or_model_class._meta
        max_length = meta.get_field(field_name).max_length
        # If there's no max_length on the field, just set the value
        if max_length is not None:
            # If an exception is wanted, we just try setting the value as normal
            if self.truncate != 'exception':
                if value:
                    if self.truncate == 'warn' and len(value) > max_length:
                        msg = "Warning: truncating {0} to a length of {1}"
                        print(msg.format(value, max_length), file=sys.stderr)
                    value = value[:max_length]
        return value

    def set(self, django_object, field_name, value):
        possibly_truncated_value = self.get_truncated(
            django_object, field_name, value)
        setattr(django_object, field_name, possibly_truncated_value)

    def import_from_export_json_data(self, data):
        """Update or create django-popolo models from a PopIt export

        You can run this multiple times to update the django-popolo
        models after the initial import. This version of the method takes
        the JSON data after parsing; i.e. as Python lists, dicts, etc."""

        # Keep track of all areas that are found, so that we can later
        # iterate over them and make sure their 'parent' property is
        # correctly set.
        area_id_to_django_object = {}
        area_id_to_parent_area_id = {}

        def update_optional_area(object_data):
            area_data = object_data.get('area')
            area_id = object_data.get('area_id')
            area = None
            if area_data:
                if not area_data.get('id'):
                    msg = 'Found inline area data, but with no "id" attribute'
                    raise ValueError(msg)
                with show_data_on_error('area_data', area_data):
                    area_id, area = self.update_area(area_data)
                    area_id_to_django_object[area_id] = area
                area_parent_id = area_data.get('parent_id')
                if area_parent_id:
                    area_id_to_parent_area_id[area_id] = area_parent_id
            elif area_id:
                # if we have an area_id instead of an inline area
                area = self.get_existing_django_object('area', area_id)
            return area

        self.events = {}
        # store events in a temp local dict:
        for event_data in data.get('events', []):
            self.events[event_data['id']] = event_data

        # Create all areas:
        for area_data in data.get('areas', []):
            with show_data_on_error('area_data', area_data):
                area_id, area = self.update_area(area_data)
                area_parent_id = area_data.get('parent_id')
                if area_parent_id:
                    area_id_to_parent_area_id[area_id] = area_parent_id
                area_id_to_django_object[area_id] = area

        # Do one pass through the organizations:
        org_id_to_django_object = {}
        for org_data in data.get('organizations', []):
            with show_data_on_error('org_data', org_data):
                area = update_optional_area(org_data)
                popit_id, organization = self.update_organization(org_data,
                                                                  area)
                org_id_to_django_object[popit_id] = organization
        # Then go through the organizations again to set the parent
        # organization:
        for org_data in data.get('organizations', []):
            with show_data_on_error('org_data', org_data):
                org = org_id_to_django_object[org_data['id']]
                parent_id = org_data.get('parent_id')
                if parent_id:
                    org_parent = org_id_to_django_object[parent_id]
                    self.set(org, 'parent', org_parent)
                    org.save()
        # Create all posts (dependent on organizations already existing)
        post_id_to_django_object = {}
        for post_data in data.get('posts', []):
            with show_data_on_error('post_data', post_data):
                area = update_optional_area(post_data)
                popit_id, post = \
                    self.update_post(post_data, area, org_id_to_django_object)
                post_id_to_django_object[popit_id] = post
        # Create all people:
        person_id_to_django_object = {}
        inline_memberships = []
        for person_data in data.get('persons', []):
            with show_data_on_error('person_data', person_data):
                inline_memberships += person_data.pop('memberships', [])
                popit_id, person = \
                    self.update_person(person_data)
                person_id_to_django_object[popit_id] = person
        # Now create all memberships to tie the people, organizations
        # and posts together:
        membership_id_to_django_object = {}
        all_memberships = data.get('memberships', []) + inline_memberships
        for membership_data in all_memberships:
            with show_data_on_error('membership_data', membership_data):
                area = update_optional_area(membership_data)
                membership_id, membership = \
                    self.update_membership(
                        membership_data,
                        area,
                        org_id_to_django_object,
                        post_id_to_django_object,
                        person_id_to_django_object,
                    )
                membership_id_to_django_object[membership_id] = membership

        # Finally set any parent area relationships on areas:
        for area_id, parent_area_id in area_id_to_parent_area_id.items():
            area = area_id_to_django_object[area_id]
            parent_area = area_id_to_django_object[parent_area_id]
            self.set(area, 'parent', parent_area)
            area.save()

    def import_from_export_json(self, json_filename):
        """Update or create django-popolo models from a PopIt export

        You can run this multiple times to update the django-popolo
        models after the initial import. This version of the method takes
        a filename"""

        with open(json_filename) as f:
            data = json.load(f)

        self.import_from_export_json_data(data)

    def get_existing_django_object(self, popit_collection, popit_id):
        Identifier = self.get_popolo_model_class('Identifier')
        if popit_collection not in NEW_COLLECTIONS:
            raise Exception("Unknown collection '{collection}'".format(
                collection=popit_collection
            ))
        try:
            i = Identifier.objects.get(
                scheme=(self.id_prefix + popit_collection),
                identifier=popit_id
            )
            # Following i.content_object doesn't work in a migration, so use
            # a slightly more long-winded way to find the referenced object:
            model_class = self.get_popolo_model_class(i.content_type.model)
            return model_class.objects.get(pk=i.object_id)
        except Identifier.DoesNotExist:
            return None

    def update_organization(self, org_data, area):
        Organization = self.get_popolo_model_class('Organization')
        existing = self.get_existing_django_object('organization',
                                                   org_data['id'])
        if existing is None:
            result = Organization()
        else:
            result = existing
        self.set(result, 'name', org_data['name'])
        self.set(result, 'classification', org_data.get('classification', ''))
        self.set(result, 'dissolution_date',
                 org_data.get('dissolution_date', ''))
        self.set(result, 'founding_date', org_data.get('founding_date', ''))
        self.set(result, 'image', org_data.get('image') or None)
        self.set(result, 'area', area)
        result.save()
        # Create an identifier with the PopIt ID:
        if not existing:
            self.create_identifier('organization', org_data['id'], result)

        # Update other identifiers:
        self.update_related_objects(
            Organization,
            self.get_popolo_model_class('Identifier'),
            self.make_identifier_dict,
            org_data.get('identifiers', []),
            result,
        )
        # Update contact details:
        self.update_related_objects(
            Organization,
            self.get_popolo_model_class('ContactDetail'),
            self.make_contact_detail_dict,
            org_data.get('contact_details', []),
            result
        )
        # Update links:
        self.update_related_objects(
            Organization,
            self.get_popolo_model_class('Link'),
            self.make_link_dict,
            org_data.get('links', []),
            result
        )
        # Update sources:
        self.update_related_objects(
            Organization,
            self.get_popolo_model_class('Source'),
            self.make_source_dict,
            org_data.get('sources', []),
            result
        )
        # Update other names:
        self.update_related_objects(
            Organization,
            self.get_popolo_model_class('OtherName'),
            self.make_other_name_dict,
            org_data.get('other_names', []),
            result
        )
        self.notify_observers('organization', result, existing is None,
                              org_data)
        return org_data['id'], result

    def update_post(self, post_data, area, org_id_to_django_object):
        Post = self.get_popolo_model_class('Post')
        existing = self.get_existing_django_object('post', post_data['id'])
        if existing is None:
            result = Post()
        else:
            result = existing
        self.set(result, 'label', post_data['label'])
        self.set(result, 'role', post_data['role'])
        self.set(result, 'organization',
                 org_id_to_django_object[post_data['organization_id']])
        self.set(result, 'area', area)
        result.save()
        # Create an identifier with the PopIt ID:
        if not existing:
            self.create_identifier('post', post_data['id'], result)
        # Update contact details:
        self.update_related_objects(
            Post,
            self.get_popolo_model_class('ContactDetail'),
            self.make_contact_detail_dict,
            post_data.get('contact_details', []),
            result
        )
        # Update links:
        self.update_related_objects(
            Post,
            self.get_popolo_model_class('Link'),
            self.make_link_dict,
            post_data.get('links', []),
            result
        )
        # Update sources:
        self.update_related_objects(
            Post,
            self.get_popolo_model_class('Source'),
            self.make_source_dict,
            post_data.get('sources', []),
            result
        )
        self.notify_observers('post', result, existing is None, post_data)
        return post_data['id'], result

    def update_person(self, person_data):
        Person = self.get_popolo_model_class('Person')
        existing = self.get_existing_django_object('person', person_data['id'])
        if existing is None:
            result = Person()
        else:
            result = existing
        self.set(result, 'name', person_data['name'])
        self.set(result, 'family_name', person_data.get('family_name') or '')
        self.set(result, 'given_name', person_data.get('given_name') or '')
        self.set(result, 'additional_name',
                 person_data.get('additional_name') or '')
        self.set(result, 'honorific_prefix',
                 person_data.get('honorific_prefix') or '')
        self.set(result, 'honorific_suffix',
                 person_data.get('honorific_suffix') or '')
        self.set(result, 'patronymic_name',
                 person_data.get('patronymic_name') or '')
        self.set(result, 'sort_name', person_data.get('sort_name') or '')
        self.set(result, 'email', person_data.get('email') or None)
        self.set(result, 'gender', person_data.get('gender') or '')
        self.set(result, 'birth_date', person_data.get('birth_date') or '')
        self.set(result, 'death_date', person_data.get('death_date') or '')
        self.set(result, 'summary', person_data.get('summary') or '')
        self.set(result, 'biography', person_data.get('biography') or '')
        self.set(result, 'national_identity',
                 person_data.get('national_identity') or None)
        self.set(result, 'image', person_data.get('image') or None)
        result.save()
        # Create an identifier with the PopIt ID:
        if not existing:
            self.create_identifier('person', person_data['id'], result)

        # Update other_names:
        self.update_related_objects(
            Person,
            self.get_popolo_model_class('OtherName'),
            self.make_other_name_dict,
            person_data.get('other_names', []),
            result
        )
        # Update other identifiers:
        self.update_related_objects(
            Person,
            self.get_popolo_model_class('Identifier'),
            self.make_identifier_dict,
            person_data.get('identifiers', []),
            result,
        )
        # Update contact details:
        self.update_related_objects(
            Person,
            self.get_popolo_model_class('ContactDetail'),
            self.make_contact_detail_dict,
            person_data.get('contact_details', []),
            result
        )
        # Update links:
        self.update_related_objects(
            Person,
            self.get_popolo_model_class('Link'),
            self.make_link_dict,
            person_data.get('links', []),
            result
        )
        # Update sources:
        self.update_related_objects(
            Person,
            self.get_popolo_model_class('Source'),
            self.make_source_dict,
            person_data.get('sources', []),
            result
        )
        self.notify_observers('person', result, existing is None, person_data)
        return person_data['id'], result

    def update_membership(
            self,
            membership_data,
            area,
            org_id_to_django_object,
            post_id_to_django_object,
            person_id_to_django_object,
    ):
        def generate_membership_id(membership_data):
            # construct an 'id' based on data that should be unique_together
            new_id = ''
            new_id += membership_data.get('legislative_period_id',
                                          'missing') + "_"
            new_id += membership_data.get('organization_id', 'missing') + "_"
            new_id += membership_data.get('area_id', 'missing') + "_"
            new_id += membership_data.get('role', 'missing') + "_"
            new_id += membership_data.get('on_behalf_of_id', 'missing') + "_"
            new_id += membership_data.get('person_id', 'missing')
            return new_id

        Membership = self.get_popolo_model_class('Membership')

        if 'id' not in membership_data:
            membership_data['id'] = generate_membership_id(membership_data)

        existing = self.get_existing_django_object('membership',
                                                   membership_data['id'])
        if existing is None:
            result = Membership()
        else:
            result = existing
        self.set(result, 'label', membership_data.get('label') or '')
        self.set(result, 'role', membership_data.get('role') or '')
        self.set(result, 'person',
                 person_id_to_django_object[membership_data['person_id']])
        organization_id = membership_data.get('organization_id')
        if organization_id:
            self.set(result, 'organization',
                     org_id_to_django_object[organization_id])
        on_behalf_of_id = membership_data.get('on_behalf_of_id')
        if on_behalf_of_id:
            self.set(result, 'on_behalf_of',
                     org_id_to_django_object[on_behalf_of_id])
        post_id = membership_data.get('post_id')
        if post_id:
            self.set(result, 'post', post_id_to_django_object[post_id])
        self.set(result, 'area', area)
        self.set(result, 'start_date', membership_data.get('start_date', ''))
        self.set(result, 'end_date', membership_data.get('end_date', ''))
        if 'legislative_period_id' in membership_data:
            # Strictly speaking there may be cases where it would not
            # be correct to use the leglislative period's start and
            # end dates as defaults for the membership start and end
            # dates. Ideally, django-popolo would support Popolo
            # events, so we could just associate the membership with
            # one of them and omit the start / end dates as in the
            # original data. However, until events have been added
            # this is a useful default for people importing data where
            # memberships have a legislative period but no start / end
            # date.
            period_data = self.events[membership_data['legislative_period_id']]
            if not result.start_date:
                self.set(result, 'start_date',
                         period_data.get('start_date', ''))
            if not result.end_date:
                self.set(result, 'end_date', period_data.get('end_date', ''))

        result.save()
        # Create an identifier with the PopIt ID:
        if not existing:
            self.create_identifier('membership', membership_data['id'], result)

        # Update contact details:
        self.update_related_objects(
            Membership,
            self.get_popolo_model_class('ContactDetail'),
            self.make_contact_detail_dict,
            membership_data.get('contact_details', []),
            result
        )
        # Update links:
        self.update_related_objects(
            Membership,
            self.get_popolo_model_class('Link'),
            self.make_link_dict,
            membership_data.get('links', []),
            result
        )
        # Update sources:
        self.update_related_objects(
            Membership,
            self.get_popolo_model_class('Source'),
            self.make_source_dict,
            membership_data.get('sources', []),
            result
        )
        self.notify_observers('membership', result, existing is None,
                              membership_data)
        return membership_data['id'], result

    def update_area(self, area_data):
        Area = self.get_popolo_model_class('Area')
        existing = self.get_existing_django_object('area', area_data['id'])
        if existing is None:
            result = Area()
        else:
            result = existing
        self.set(result, 'name', area_data.get('name') or '')
        self.set(result, 'identifier', area_data.get('identifier') or '')
        self.set(result, 'classification',
                 area_data.get('classification') or '')
        self.set(result, 'geom', area_data.get('geom') or None)
        self.set(result, 'inhabitants', area_data.get('inhabitants'))
        result.save()
        # Create an identifier with the PopIt ID:
        if not existing:
            self.create_identifier('area', area_data['id'], result)
        # Update other_identifiers:
        self.update_related_objects(
            Area,
            self.get_popolo_model_class('Identifier'),
            self.make_identifier_dict,
            area_data.get('other_identifiers', []),
            result,
        )
        # Update sources:
        self.update_related_objects(
            Area,
            self.get_popolo_model_class('Source'),
            self.make_source_dict,
            area_data.get('sources', []),
            result
        )
        self.notify_observers('area', result, existing is None, area_data)
        return area_data['id'], result

    def create_identifier(self, popit_collection, popit_id, django_object):
        if popit_collection not in NEW_COLLECTIONS:
            raise Exception("Unknown collection '{collection}'".format(
                collection=popit_collection
            ))
        ContentType = self.get_model_class('contenttypes', 'ContentType')
        content_type = ContentType.objects.get_for_model(django_object)
        self.get_popolo_model_class('Identifier').objects.create(
            object_id=django_object.id,
            content_type_id=content_type.id,
            scheme=(self.id_prefix + popit_collection),
            identifier=popit_id,
        )

    def should_preserve_related(self, django_main_model, related_object):
        # We only have rules for preserving identifiers, so ignore
        # other types of related object:
        if type(related_object).__name__ == 'Identifier':
            schemes_to_preserve = self.id_schemes_to_preserve.get(
                django_main_model.__name__.lower(), set())
            if related_object.scheme in schemes_to_preserve:
                return True

    def update_related_objects(
            self,
            django_main_model,
            django_related_model,
            popit_to_django_attributes_method,
            popit_related_objects_data,
            django_object,
    ):
        # Find the unchanged related objects so we don't unnecessarily
        # recreate objects.
        ContentType = self.get_model_class('contenttypes', 'ContentType')
        main_content_type = ContentType.objects.get_for_model(django_main_model)
        new_objects = []
        old_objects_to_preserve = [
            o for o in django_related_model.objects.filter(
                content_type_id=main_content_type.id,
                object_id=django_object.id
            )
            if self.should_preserve_related(django_main_model, o)
        ]
        for object_data in popit_related_objects_data:
            wanted_attributes = popit_to_django_attributes_method(
                object_data
            )
            # We might need to truncate these in order for them to
            # match the objects already in the database:
            wanted_attributes = {
                k: self.get_truncated(django_related_model, k, v)
                for k, v in wanted_attributes.items()
            }
            wanted_attributes['content_type_id'] = main_content_type.id
            wanted_attributes['object_id'] = django_object.id
            existing = django_related_model.objects.filter(**wanted_attributes)
            if existing.exists():
                old_objects_to_preserve += existing
            else:
                new_objects.append(
                    django_related_model.objects.create(**wanted_attributes)
                )
        object_ids_to_preserve = set(c.id for c in new_objects)
        object_ids_to_preserve.update(c.id for c in old_objects_to_preserve)
        django_related_model.objects.filter(
            content_type_id=main_content_type.id,
            object_id=django_object.id
        ).exclude(pk__in=object_ids_to_preserve).delete()

    def make_contact_detail_dict(self, contact_detail_data):
        contact_type = contact_detail_data.get('type') or \
                       contact_detail_data.get('contact_type')
        return {
            'label': contact_detail_data.get('label') or '',
            'contact_type': contact_type,
            'value': contact_detail_data['value'],
            'note': contact_detail_data.get('note') or '',
            'start_date': contact_detail_data.get('valid_from') or '',
            'end_date': contact_detail_data.get('valid_until') or '',
        }

    def make_link_dict(self, link_data):
        return {
            'note': link_data.get('note') or '',
            'url': link_data['url'],
        }

    def make_source_dict(self, source_data):
        return {
            'url': source_data['url'],
            'note': source_data.get('note') or '',
        }

    def make_other_name_dict(self, other_name_data):
        return {
            'name': other_name_data.get('name') or '',
            'note': other_name_data.get('note') or '',
            'start_date': other_name_data.get('start_date') or '',
            'end_date': other_name_data.get('end_date') or '',
        }

    def make_identifier_dict(self, identifier_data):
        return {
            'identifier': identifier_data['identifier'],
            'scheme': identifier_data['scheme'],
        }
