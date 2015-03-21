from autoslug import AutoSlugField
from autoslug.utils import slugify
from django.contrib.contenttypes import generic
from django.core.validators import RegexValidator
from django.db import models
from model_utils import Choices
from model_utils.managers import PassThroughManager
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .behaviors.models import Permalinkable, Timestampable, Dateframeable, GenericRelatable
from .querysets import PostQuerySet, OtherNameQuerySet, ContactDetailQuerySet, MembershipQuerySet, OrganizationQuerySet, PersonQuerySet


@python_2_unicode_compatible
class Person(Dateframeable, Timestampable, models.Model):
    """
    A real person, alive or dead
    see schema at http://popoloproject.com/schemas/person.json#
    """

    json_ld_context = "http://popoloproject.com/contexts/person.jsonld"
    json_ld_type = "http://www.w3.org/ns/person#Person"

    id = AutoSlugField(
        populate_from=lambda instance: instance.slug_source,
        primary_key=True, max_length=256,
        slugify=slugify
    )

    name = models.CharField(_("name"), max_length=512, help_text=_("A person's preferred full name"))

    # array of items referencing "http://popoloproject.com/schemas/other_name.json#"
    other_names = generic.GenericRelation('OtherName', help_text="Alternate or former names")

    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    identifiers = generic.GenericRelation('Identifier', help_text="Issued identifiers")

    family_name = models.CharField(_("family name"), max_length=128, blank=True, help_text=_("One or more family names"))
    given_name = models.CharField(_("given name"), max_length=128, blank=True, help_text=_("One or more primary given names"))
    additional_name = models.CharField(_("additional name"), max_length=128, blank=True, help_text=_("One or more secondary given names"))
    honorific_prefix = models.CharField(_("honorific prefix"), max_length=128, blank=True, help_text=_("One or more honorifics preceding a person's name"))
    honorific_suffix = models.CharField(_("honorific suffix"), max_length=128, blank=True, help_text=_("One or more honorifics following a person's name"))
    patronymic_name = models.CharField(_("patronymic name"), max_length=128, blank=True, help_text=_("One or more patronymic names"))
    sort_name = models.CharField(_("sort name"), max_length=128, blank=True, help_text=_("A name to use in an lexicographically ordered list"))
    email = models.EmailField(_("email"), blank=True, null=True, help_text=_("A preferred email address"))
    gender = models.CharField(_('gender'), max_length=128, blank=True, help_text=_("A gender"))
    birth_date = models.CharField(_("birth date"), max_length=10, blank=True, help_text=_("A date of birth"))
    death_date = models.CharField(_("death date"), max_length=10, blank=True, help_text=_("A date of death"))
    image = models.URLField(_("image"), blank=True, null=True, help_text=_("A URL of a head shot"))
    summary = models.CharField(_("summary"), max_length=1024, blank=True, help_text=_("A one-line account of a person's life"))
    biography = models.TextField(_("biography"), blank=True, help_text=_("An extended account of a person's life"))
    national_identity = models.CharField(_("national identity"), max_length=128, blank=True, null=True, help_text=_("A national identity"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents related to the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Source', help_text="URLs to source documents about the person")

    @property
    def slug_source(self):
        return u"{0} {1}".format(self.name, self.birth_date)

    url_name = 'person-detail'
    objects = PassThroughManager.for_queryset_class(PersonQuerySet)()

    def add_membership(self, organization):
        m = Membership(person=self, organization=organization)
        m.save()

    def add_memberships(self, organizations):
       for o in organizations:
           self.add_membership(o)

    def add_role(self, post):
        m = Membership(person=self, post=post, organization=post.organization)
        m.save()

    def add_contact_detail(self, **kwargs):
        c = ContactDetail(content_object=self, **kwargs)
        c.save()

    def add_contact_details(self, contacts):
        for c in contacts:
            self.add_contact_detail(**c)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Organization(Dateframeable, Timestampable, Permalinkable, models.Model):
    """
    A group with a common purpose or reason for existence that goes beyond the set of people belonging to it
    see schema at http://popoloproject.com/schemas/organization.json#
    """
    id = AutoSlugField(
        populate_from=lambda instance: instance.slug_source,
        primary_key=True, max_length=256,
        slugify=slugify
    )

    @property
    def slug_source(self):
        return self.name

    name = models.CharField(_("name"), max_length=512, help_text=_("A primary name, e.g. a legally recognized name"))

    # array of items referencing "http://popoloproject.com/schemas/other_name.json#"
    other_names = generic.GenericRelation('OtherName', help_text="Alternate or former names")

    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    identifiers = generic.GenericRelation('Identifier', help_text="Issued identifiers")
    classification = models.CharField(_("classification"), max_length=512, blank=True, help_text=_("An organization category, e.g. committee"))

    # reference to "http://popoloproject.com/schemas/organization.json#"
    parent = models.ForeignKey('Organization', blank=True, null=True, related_name='children',
                               help_text=_("The organization that contains this organization"))

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey('Area', blank=True, null=True, related_name='organizations',
                               help_text=_("The geographic area to which this organization is related"))

    dissolution_date = models.CharField(_("dissolution date"), max_length=10, blank=True, validators=[
                    RegexValidator(
                        regex='^[0-9]{4}(-[0-9]{2}){0,2}$',
                        message='dissolution date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$',
                        code='invalid_dissolution_date'
                    )
                ], help_text=_("A date of dissolution"))
    founding_date = models.CharField(_("founding date"), max_length=10, blank=True, validators=[
                    RegexValidator(
                        regex='^[0-9]{4}(-[0-9]{2}){0,2}$',
                        message='founding date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$',
                        code='invalid_founding_date'
                    )
                ], help_text=_("A date of founding"))
    image = models.URLField(_("image"), blank=True, null=True, help_text=_("A URL of an image, to identify the organization visually"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the organization")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents about the organization")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Source', help_text="URLs to source documents about the organization")

    url_name = 'organization-detail'
    objects = PassThroughManager.for_queryset_class(OrganizationQuerySet)()

    def add_member(self, person):
        m = Membership(organization=self, person=person)
        m.save()

    def add_members(self, persons):
        for p in persons:
            self.add_member(p)

    def add_post(self, **kwargs):
        p = Post(organization=self, **kwargs)
        p.save()

    def add_posts(self, posts):
        for p in posts:
            self.add_post(**p)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Post(Dateframeable, Timestampable, models.Model):
    """
    A position that exists independent of the person holding it
    see schema at http://popoloproject.com/schemas/json#
    """
    id = AutoSlugField(
        populate_from=lambda instance: instance.slug_source,
        primary_key=True, max_length=256,
        slugify=slugify
    )

    @property
    def slug_source(self):
        return self.label

    label = models.CharField(_("label"), max_length=512, blank=True, help_text=_("A label describing the post"))
    other_label = models.CharField(_("other label"), max_length=512, blank=True, null=True, help_text=_("An alternate label, such as an abbreviation"))

    role = models.CharField(_("role"), max_length=512, blank=True, help_text=_("The function that the holder of the post fulfills"))

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey('Organization', related_name='posts',
                                     help_text=_("The organization in which the post is held"))

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey('Area', blank=True, null=True, related_name='posts',
                               help_text=_("The geographic area to which the post is related"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the holder of the post")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents about the post")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Source', help_text="URLs to source documents about the post")

    objects = PassThroughManager.for_queryset_class(PostQuerySet)()

    def add_person(self, person):
        m = Membership(post=self, person=person, organization=self.organization)
        m.save()

    def __str__(self):
        return self.label

@python_2_unicode_compatible
class Membership(Dateframeable, Timestampable, models.Model):
    """
    A relationship between a person and an organization
    see schema at http://popoloproject.com/schemas/membership.json#
    """

    label = models.CharField(_("label"), max_length=512, blank=True, help_text=_("A label describing the membership"))
    role = models.CharField(_("role"), max_length=512, blank=True, help_text=_("The role that the person fulfills in the organization"))

    # reference to "http://popoloproject.com/schemas/person.json#"
    person = models.ForeignKey('Person', to_field="id", related_name='memberships',
                               help_text=_("The person who is a party to the relationship"))

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey('Organization', blank=True, null=True,
                                     related_name='memberships',
                                     help_text=_("The organization that is a party to the relationship"))
    on_behalf_of = models.ForeignKey('Organization', blank=True, null=True,
                                     related_name='memberships_on_behalf_of',
                                     help_text=_("The organization on whose behalf the person is a party to the relationship"))

    # reference to "http://popoloproject.com/schemas/post.json#"
    post = models.ForeignKey('Post', blank=True, null=True, related_name='memberships',
                             help_text=_("The post held by the person in the organization through this membership"))

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey('Area', blank=True, null=True, related_name='memberships',
                               help_text=_("The geographic area to which the post is related"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the member of the organization")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents about the membership")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Source', help_text="URLs to source documents about the membership")

    @property
    def slug_source(self):
        return self.label

    objects = PassThroughManager.for_queryset_class(MembershipQuerySet)()

    def __str__(self):
        return self.label

@python_2_unicode_compatible
class ContactDetail(Timestampable, Dateframeable, GenericRelatable,  models.Model):
    """
    A means of contacting an entity
    see schema at http://popoloproject.com/schemas/contact-detail.json#
    """

    CONTACT_TYPES = Choices(
        ('FAX', 'fax', _('Fax')),
        ('PHONE', 'phone', _('Telephone')),
        ('MOBILE', 'mobile', _('Mobile')),
        ('EMAIL', 'email', _('Email')),
        ('MAIL', 'mail', _('Snail mail')),
        ('TWITTER', 'twitter', _('Twitter')),
        ('FACEBOOK', 'facebook', _('Facebook')),
    )

    label = models.CharField(_("label"), max_length=512, blank=True, help_text=_("A human-readable label for the contact detail"))
    contact_type = models.CharField(_("type"), max_length=12, choices=CONTACT_TYPES, help_text=_("A type of medium, e.g. 'fax' or 'email'"))
    value = models.CharField(_("value"), max_length=512, help_text=_("A value, e.g. a phone number or email address"))
    note = models.CharField(_("note"), max_length=512, blank=True, help_text=_("A note, e.g. for grouping contact details by physical location"))

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Source', help_text="URLs to source documents about the contact detail")

    objects = PassThroughManager.for_queryset_class(ContactDetailQuerySet)()

    def __str__(self):
        return u"{0} - {1}".format(self.value, self.contact_type)


@python_2_unicode_compatible
class OtherName(Dateframeable, GenericRelatable, models.Model):
    """
    An alternate or former name
    see schema at http://popoloproject.com/schemas/name-component.json#
    """
    name = models.CharField(_("name"), max_length=512, help_text=_("An alternate or former name"))
    note = models.CharField(_("note"), max_length=1024, blank=True, help_text=_("A note, e.g. 'Birth name'"))

    objects = PassThroughManager.for_queryset_class(OtherNameQuerySet)()

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Identifier(GenericRelatable, models.Model):
    """
    An issued identifier
    see schema at http://popoloproject.com/schemas/identifier.json#
    """
    identifier = models.CharField(_("identifier"), max_length=512, help_text=_("An issued identifier, e.g. a DUNS number"))
    scheme = models.CharField(_("scheme"), max_length=128, blank=True, help_text=_("An identifier scheme, e.g. DUNS"))

    def __str__(self):
        return "{0}: {1}".format(self.scheme, self.identifier)


@python_2_unicode_compatible
class Link(GenericRelatable, models.Model):
    """
    A URL
    see schema at http://popoloproject.com/schemas/link.json#
    """
    url = models.URLField(_("url"), max_length=350, help_text=_("A URL"))
    note = models.CharField(_("note"), max_length=512, blank=True, help_text=_("A note, e.g. 'Wikipedia page'"))

    def __str__(self):
        return self.url


@python_2_unicode_compatible
class Source(GenericRelatable, models.Model):
    """
    A URL for referring to sources of information
    see schema at http://popoloproject.com/schemas/link.json#
    """
    url = models.URLField(_("url"), help_text=_("A URL"))
    note = models.CharField(_("note"), max_length=512, blank=True, help_text=_("A note, e.g. 'Parliament website'"))

    def __str__(self):
        return self.url



@python_2_unicode_compatible
class Language(models.Model):
    """
    Maps languages, with names and 2-char iso 639-1 codes.
    Taken from http://dbpedia.org, using a sparql query
    """
    dbpedia_resource = models.CharField(max_length=255,
        help_text=_("DbPedia URI of the resource"), unique=True)
    iso639_1_code = models.CharField(max_length=2)
    name = models.CharField(max_length=128,
        help_text=_("English name of the language"))

    def __str__(self):
        return u"{0} ({1})".format(self.name, self.iso639_1_code)

@python_2_unicode_compatible
class Area(GenericRelatable, Timestampable, models.Model):
    """
    An area is a geographic area whose geometry may change over time.
    see schema at http://popoloproject.com/schemas/area.json#
    """
    name = models.CharField(_("name"), max_length=256, blank=True, help_text=_("A primary name"))
    identifier = models.CharField(_("identifier"), max_length=512, blank=True, help_text=_("An issued identifier"))
    classification = models.CharField(_("identifier"), max_length=512, blank=True, help_text=_("An area category, e.g. city"))

    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    other_identifiers = generic.GenericRelation('Identifier', blank=True, null=True, help_text="Other issued identifiers (zip code, other useful codes, ...)")

    # reference to "http://popoloproject.com/schemas/area.json#"
    parent = models.ForeignKey('Area', blank=True, null=True, related_name='children',
                               help_text=_("The area that contains this area"))

    # geom property, as text (GeoJson, KML, GML)
    geom = models.TextField(_("geom"), null=True, blank=True, help_text="A geometry")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Source', blank=True, null=True, help_text="URLs to source documents about the contact detail")

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class AreaI18Name(models.Model):
    """
    Internationalized name for an Area.
    Contains references to language and area.
    """
    area = models.ForeignKey('Area', related_name='i18n_names')
    language = models.ForeignKey('Language')
    name = models.CharField(_("name"), max_length=255)

    def __str__(self):
        return "{0} - {1}".format(self.language, self.name)

    class Meta:
        verbose_name = 'I18N Name'
        verbose_name_plural = 'I18N Names'
        unique_together = ('area', 'language', 'name')



##
## signals
##

## copy founding and dissolution dates into start and end dates,
## so that Organization can extend the abstract Dateframeable behavior
## (it's way easier than dynamic field names)
@receiver(pre_save, sender=Organization)
def copy_organization_date_fields(sender, **kwargs):
    obj = kwargs['instance']

    if obj.founding_date:
        obj.start_date = obj.founding_date
    if obj.dissolution_date:
        obj.end_date = obj.dissolution_date

## copy birth and death dates into start and end dates,
## so that Person can extend the abstract Dateframeable behavior
## (it's way easier than dynamic field names)
@receiver(pre_save, sender=Person)
def copy_person_date_fields(sender, **kwargs):
    obj = kwargs['instance']

    if obj.birth_date:
        obj.start_date = obj.birth_date
    if obj.death_date:
        obj.end_date = obj.death_date


## all instances are validated before being saved
@receiver(pre_save, sender=Person)
@receiver(pre_save, sender=Organization)
@receiver(pre_save, sender=Post)
def validate_date_fields(sender, **kwargs):
    obj = kwargs['instance']
    obj.full_clean()
