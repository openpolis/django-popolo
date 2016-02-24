from __future__ import print_function

from contextlib import contextmanager
import json
import sys

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

class PopItImporter(object):

    """This class helps you to import data from PopIt into django-popolo

    If you instantiate this class, you can call
    import_from_export_json on that importer object with data from
    PopIt's /api/v0.1/export.json API endpoint.  That will import the
    core Popolo data from that PopIt export into django-popolo's
    Django models.

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

    def get_popolo_model_class(self, model_name):
        """A default implementation for getting the Popolo model class"""
        return self.get_model_class('popolo', model_name)

    def get_model_class(self, app_label, model_name):
        return apps.get_model(app_label, model_name)

    def import_from_export_json(self, json_filename):
        """Update or create django-popolo models from a PopIt export

        You can run this multiple times to update the django-popolo
        models after the initial import."""

        with open(json_filename) as f:
            data = json.load(f)

        # Keep track of all areas that are found, so that we can later
        # iterate over them and make sure their 'parent' property is
        # correctly set.
        area_id_to_django_object = {}
        area_id_to_parent_area_id = {}
        def update_optional_area(object_data):
            area_data = object_data.get('area')
            area = None
            if area_data:
                if not area_data.get('id'):
                    return None
                area_parent_id = area_data.get('parent_id')
                if area_parent_id:
                    area_id_to_parent_area_id
                with show_data_on_error('area_data', area_data):
                    area_id, area = self.update_area(area_data)
                    area_id_to_django_object[area_id] = area
            return area

        # Do one pass through the organizations:
        org_id_to_django_object = {}
        for org_data in data['organizations']:
            with show_data_on_error('org_data', org_data):
                area = update_optional_area(org_data)
                popit_id, organization = self.update_organization(org_data, area)
                org_id_to_django_object[popit_id] = organization
        # Then go through the organizations again to set the parent
        # organization:
        for org_data in data['organizations']:
            with show_data_on_error('org_data', org_data):
                org = org_id_to_django_object[org_data['id']]
                parent_id = org_data.get('parent_id')
                if parent_id:
                    org_parent = org_id_to_django_object[parent_id]
                    org.parent = org_parent
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
        for person_data in data['persons']:
            with show_data_on_error('person_data', person_data):
                popit_id, person = \
                    self.update_person(person_data)
                person_id_to_django_object[popit_id] = person
        # Now create all memberships to tie the people, organizations
        # and posts together:
        membership_id_to_django_object = {}
        for membership_data in data['memberships']:
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
            area = area_id_to_parent_area_id[area_id]
            parent_area = area_id_to_parent_area_id[parent_area_id]
            area.parent = parent_area
            area.save()

    def get_existing_django_object(self, popit_collection, popit_id):
        Identifier = self.get_popolo_model_class('Identifier')
        if popit_collection not in NEW_COLLECTIONS:
            raise Exception("Unknown collection '{collection}'".format(
                collection=popit_collection
            ))
        try:
            i = Identifier.objects.get(
                scheme=('popit-' + popit_collection),
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
        existing = self.get_existing_django_object('organization', org_data['id'])
        if existing is None:
            result = Organization()
        else:
            result = existing
        result.name = org_data['name']
        result.classification = org_data.get('classification', '')
        result.dissolution_date = org_data.get('dissolution_date', '')
        result.founding_date = org_data.get('founding_date', '')
        result.image = org_data.get('image') or None
        result.area = area
        result.save()
        # Create an identifier with the PopIt ID:
        if not existing:
            self.create_identifier('organization', org_data['id'], result)

        # Update other identifiers:
        self.update_related_objects(
            Organization,
            self.get_popolo_model_class('Identifier'),
            self.make_identifier_dict,
            org_data['identifiers'],
            result,
            preserve_predicate=lambda i: i.scheme == 'popit-organization',
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
        return org_data['id'], result

    def update_post(self, post_data, area, org_id_to_django_object):
        Post = self.get_popolo_model_class('Post')
        existing = self.get_existing_django_object('post', post_data['id'])
        if existing is None:
            result = Post()
        else:
            result = existing
        result.label = post_data['label']
        result.role = post_data['role']
        result.organization = org_id_to_django_object[post_data['organization_id']]
        result.area = area
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
        return post_data['id'], result

    def update_person(self, person_data):
        Person = self.get_popolo_model_class('Person')
        existing = self.get_existing_django_object('person', person_data['id'])
        if existing is None:
            result = Person()
        else:
            result = existing
        result.name = person_data['name']
        result.family_name = person_data.get('family_name') or ''
        result.given_name = person_data.get('given_name') or ''
        result.additional_name = person_data.get('additional_name') or ''
        result.honorific_prefix = person_data.get('honorific_prefix') or ''
        result.honorific_suffix = person_data.get('honorific_suffix') or ''
        result.patronymic_name = person_data.get('patronymic_name') or ''
        result.sort_name = person_data.get('sort_name') or ''
        result.email = person_data.get('email') or None
        result.gender = person_data.get('gender') or ''
        result.birth_date = person_data.get('birth_date') or ''
        result.death_date = person_data.get('death_date') or ''
        result.summary = person_data.get('summary') or ''
        result.biography = person_data.get('biography') or ''
        result.national_identitiy = person_data.get('national_identity') or None
        result.image = person_data.get('image') or None
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
            person_data['identifiers'],
            result,
            preserve_predicate=lambda i: i.scheme == 'popit-person',
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
        return person_data['id'], result

    def update_membership(
            self,
            membership_data,
            area,
            org_id_to_django_object,
            post_id_to_django_object,
            person_id_to_django_object,
    ):
        Membership = self.get_popolo_model_class('Membership')
        existing = self.get_existing_django_object('membership', membership_data['id'])
        if existing is None:
            result = Membership()
        else:
            result = existing
        result.label = membership_data.get('label') or ''
        result.role = membership_data.get('role') or ''
        result.person = person_id_to_django_object[membership_data['person_id']]
        organization_id = membership_data.get('organization_id')
        if organization_id:
            result.organization = org_id_to_django_object[organization_id]
        on_behalf_of_id = membership_data.get('on_behalf_of_id')
        if on_behalf_of_id:
            result.on_behalf_of = org_id_to_django_object[on_behalf_of_id]
        post_id = membership_data.get('post_id')
        if post_id:
            result.post = post_id_to_django_object[post_id]
        result.area = area
        result.start_date = membership_data.get('start_date', '')
        result.end_date = membership_data.get('end_date', '')
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
        return membership_data['id'], result

    def update_area(self, area_data):
        Area = self.get_popolo_model_class('Area')
        existing = self.get_existing_django_object('area', area_data['id'])
        if existing is None:
            result = Area()
        else:
            result = existing
        result.name = area_data.get('name') or ''
        result.identifier = area_data.get('identifier') or ''
        result.classification = area_data.get('classification') or ''
        result.geom = area_data.get('geom') or None
        result.inhabitants = area_data.get('inhabitants')
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
            preserve_predicate=lambda i: i.scheme == 'popit-area',
        )
        # Update sources:
        self.update_related_objects(
            Area,
            self.get_popolo_model_class('Source'),
            self.make_source_dict,
            area_data.get('sources', []),
            result
        )
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
            scheme=('popit-' + popit_collection),
            identifier=popit_id,
        )

    def update_related_objects(
            self,
            django_main_model,
            django_related_model,
            popit_to_django_attributes_method,
            popit_related_objects_data,
            django_object,
            preserve_predicate=lambda o: False,
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
            if preserve_predicate(o)
        ]
        for object_data in popit_related_objects_data:
            wanted_attributes = popit_to_django_attributes_method(
                object_data
            )
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
        return {
            'label': contact_detail_data.get('label') or '',
            'contact_type': contact_detail_data['type'],
            'value': contact_detail_data['value'],
            'note': contact_detail_data.get('note') or '',
            'start_date': contact_detail_data.get('valid_from') or '',
            'end_date': contact_detail_data.get('valid_until') or '',
        }

    def make_link_dict(self, link_data):
        return {
            'note': link_data['note'],
            'url': link_data['url'],
        }

    def make_source_dict(self, source_data):
        return {
            'url': source_data['url'],
            'note': source_data['note'],
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
