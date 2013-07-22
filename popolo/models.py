from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from model_utils import Choices
from model_utils.managers import PassThroughManager
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .behaviors.models import Permalinkable, Timestampable, Dateframeable, GenericRelatable
from .querysets import PostQuerySet, OtherNameQuerySet, ContactDetailQuerySet, MembershipQuerySet, OrganizationQuerySet, PersonQuerySet


class Person(Dateframeable, Timestampable, Permalinkable, models.Model):
    """
    A real person, alive or dead
    """
    GENDERS = Choices(
        (0, 'female', _('Female')),
        (1, 'male', _('Male')),
    )

    name = models.CharField(_("name"), max_length=128, help_text=_("A person's preferred full name"))
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
    gender = models.IntegerField(_('gender'), choices=GENDERS, null=True, blank=True, help_text=_("A gender"))
    birth_date = models.CharField(_("birth date"), max_length=10, blank=True, help_text=_("A date of birth"))
    death_date = models.CharField(_("death date"), max_length=10, blank=True, help_text=_("A date of death"))
    summary = models.CharField(_("summary"), max_length=512, blank=True, help_text=_("A one-line account of a person's life"))
    biography = models.TextField(_("biography"), blank=True, help_text=_("An extended account of a person's life"))
    image = models.URLField(_("image"), blank=True, null=True, help_text=_("A URL of a head shot"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents about the person")

    # array of items referencing "http://popoloproject.com/schemas/membership.json#"
    @property
    def memberships(self):
        return self.membership_set.all()

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Link', help_text="URLs to source documents about the person", related_name='source_person_set')

    @property
    def slug_source(self):
        return self.name

    url_name = 'person-detail'
    objects = PassThroughManager.for_queryset_class(PersonQuerySet)()

    def add_membership(self, organization):
        m = Membership(person=self, organization=organization)
        m.save()

    def add_memberships(self, organizations):
       for o in organizations:
           self.add_membership(o)

    def add_role(self, post):
        m = Membership(person=self, post=post)
        m.save()

    def add_contact_detail(self, **kwargs):
        c = ContactDetail(content_object=self, **kwargs)
        c.save()



class Organization(Dateframeable, Timestampable, Permalinkable, models.Model):
    """
    A group with a common purpose or reason for existence that goes beyond the set of people belonging to it
    """

    name = models.CharField(_("name"), max_length=128, help_text=_("A primary name, e.g. a legally recognized name"))
    # array of items referencing "http://popoloproject.com/schemas/other_name.json#"
    other_names = generic.GenericRelation('OtherName', help_text="Alternate or former names")
    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    identifiers = generic.GenericRelation('Identifier', help_text="Issued identifiers")
    classification = models.CharField(_("classification"), max_length=128, blank=True, help_text=_("An organization category, e.g. committee"))
    # reference to "http://popoloproject.com/schemas/organization.json#"
    parent_id = models.CharField(_("parent id"), max_length=128, blank=True, help_text=_("The ID of the organization that contains this organization"))
    founding_date = models.CharField(_("founding date"), max_length=10, blank=True, help_text=_("A date of founding"))
    dissolution_date = models.CharField(_("dissolution date"), max_length=10, blank=True, help_text=_("A date of dissolution"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents about the person")

    # array of items referencing "http://popoloproject.com/schemas/membership.json#"
    @property
    def memberships(self):
        return self.membership_set.all()

    # array of items referencing "http://popoloproject.com/schemas/post.json#"
    @property
    def posts(self):
        return self.post_set.all()

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Link', help_text="URLs to source documents about the person", related_name='source_organization_set')

    @property
    def slug_source(self):
        return self.name

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


class Post(Dateframeable, Timestampable, Permalinkable, models.Model):
    """
    A position that exists independent of the person holding it
    """

    label = models.CharField(_("label"), max_length=128, help_text=_("A label describing the post"))
    role = models.CharField(_("role"), max_length=128, blank=True, help_text=_("The function that the holder of the post fulfills"))

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey('Organization',
                                     blank=True, null=True,
                                     help_text=_("The organization in which the post is held"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents about the person")

    # array of items referencing "http://popoloproject.com/schemas/membership.json#"
    @property
    def memberships(self):
        return self.membership_set.all()

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Link', help_text="URLs to source documents about the person", related_name='source_post_set')

    @property
    def slug_source(self):
        return self.label

    objects = PassThroughManager.for_queryset_class(PostQuerySet)()

    def add_person(self, person):
        m = Membership(post=self, person=person)
        m.save()

class Membership(Dateframeable, Timestampable, models.Model):
    """
    A relationship between a person and an organization
    """

    label = models.CharField(_("label"), max_length=128, blank=True, help_text=_("A label describing the membership"))
    role = models.CharField(_("role"), max_length=128, blank=True, help_text=_("The role that the person fulfills in the organization"))

    # reference to "http://popoloproject.com/schemas/person.json#"
    person = models.ForeignKey('Person',
                                     blank=True, null=True,
                                     help_text=_("The person who is a party to the relationship"))

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey('Organization',
                                     blank=True, null=True,
                                     help_text=_("The organization that is a party to the relationship"))

    # reference to "http://popoloproject.com/schemas/post.json#"
    post = models.ForeignKey('Post',
                                     blank=True, null=True,
                                     help_text=_("The post held by the person in the organization through this membership"))

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = generic.GenericRelation('ContactDetail', help_text="Means of contacting the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = generic.GenericRelation('Link', help_text="URLs to documents about the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Link', help_text="URLs to source documents about the person", related_name='source_membership_set')

    @property
    def slug_source(self):
        return self.label

    objects = PassThroughManager.for_queryset_class(MembershipQuerySet)()


class ContactDetail(Timestampable, Dateframeable, GenericRelatable,  models.Model):
    """
    A means of contacting an entity
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

    label = models.CharField(_("label"), max_length=128, blank=True, help_text=_("A human-readable label for the contact detail"))
    contact_type = models.CharField(_("type"), max_length=12, choices=CONTACT_TYPES, help_text=_("A type of medium, e.g. 'fax' or 'email'"))
    value = models.CharField(_("value"), max_length=128, help_text=_("A value, e.g. a phone number or email address"))
    note = models.CharField(_("note"), max_length=128, blank=True, help_text=_("A note, e.g. for grouping contact details by physical location"))


    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = generic.GenericRelation('Link', help_text="URLs to source documents about the person")

    objects = PassThroughManager.for_queryset_class(ContactDetailQuerySet)()


class OtherName(Dateframeable, GenericRelatable, models.Model):
    """
    An alternate or former name
    """
    name = models.CharField(_("name"), max_length=128, help_text=_("An alternate or former name"))
    note = models.CharField(_("note"), max_length=256, blank=True, help_text=_("A note, e.g. 'Birth name'"))

    objects = PassThroughManager.for_queryset_class(OtherNameQuerySet)()

    def __unicode__(self):
        return self.name


class Identifier(GenericRelatable, models.Model):
    """
    An issued identifier
    """

    identifier = models.CharField(_("identifier"), max_length=128, help_text=_("An issued identifier, e.g. a DUNS number"))
    scheme = models.CharField(_("scheme"), max_length=128, blank=True, help_text=_("An identifier scheme, e.g. DUNS"))


class Link(GenericRelatable, models.Model):
    """
    A URL
    """
    url = models.URLField(_("url"), help_text=_("A URL"))
    note = models.CharField(_("note"), max_length=128, blank=True, help_text=_("A note, e.g. 'Wikipedia page'"))

##
## signals
##


## copy birth and death dates into start and end dates,
## so that Person can extend the abstract Dateframeable behavior
## (it's way easier than dynamic field names)
@receiver(pre_save, sender=Person)
def copy_date_fields(sender, **kwargs):
    obj = kwargs['instance']

    if obj.birth_date:
        obj.start_date = obj.birth_date
    if obj.death_date:
        obj.end_date = obj.death_date

## copy founding and dissolution dates into start and end dates,
## so that Organization can extend the abstract Dateframeable behavior
## (it's way easier than dynamic field names)
@receiver(pre_save, sender=Organization)
def copy_date_fields(sender, **kwargs):
    obj = kwargs['instance']

    if obj.founding_date:
        obj.start_date = obj.founding_date
    if obj.dissolution_date:
        obj.end_date = obj.dissolution_date


## all instances are validated before being saved
@receiver(pre_save)
def validate_date_fields(sender, **kwargs):
    obj = kwargs['instance']
    obj.full_clean()
