# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .validators import validate_percentage

try:
    from django.contrib.contenttypes.fields import GenericRelation, \
    GenericForeignKey
except ImportError:
    # This fallback import is the version that was deprecated in
    # Django 1.7 and is removed in 1.9:
    from django.contrib.contenttypes.generic import GenericRelation, \
    GenericForeignKey

try:
    # PassTrhroughManager was removed in django-model-utils 2.4
    # see issue #22 at https://github.com/openpolis/django-popolo/issues/22
    from model_utils.managers import PassThroughManager
except ImportError:
    pass

from django.core.validators import RegexValidator
from django.db import models, IntegrityError, transaction
from model_utils import Choices
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .behaviors.models import (
    Permalinkable, Timestampable, Dateframeable,
    GenericRelatable
)
from .querysets import (
    PostQuerySet, OtherNameQuerySet, ContactDetailQuerySet,
    MembershipQuerySet, OwnershipQuerySet,
    OrganizationQuerySet, PersonQuerySet,
    PersonalRelationshipQuerySet, ElectoralEventQuerySet,
    ElectoralResultQuerySet, AreaQuerySet, IdentifierQuerySet,
    AreaRelationshipQuerySet, ClassificationQuerySet)


class ContactDetailsShortcutsMixin(object):

    def add_contact_detail(self, **kwargs):
        value = kwargs.pop('value')
        c, created = self.contact_details.get_or_create(
            value=value, defaults=kwargs
        )
        return c

    def add_contact_details(self, contacts):
        for c in contacts:
            self.add_contact_detail(**c)

class OtherNamesShortcutsMixin(object):

    def add_other_name(
        self,
        name, othername_type='ALT',
        overwrite_overlapping=False,
        extend_overlapping=True,
        **kwargs
    ):
        """Add other_name to the instance inheriting the mixin

        Names without dates specification may be added freely.

        A check for date interval overlaps is performed between the
        name that's to be added and all existing names that
        use the same scheme. Existing names are extracted ordered by
        ascending `start_date`.

        As soon as an overlap is found (first match):
        * if the name has the same value,
          then it is by default treated as an extension and date intervals
          are *extended*;
          this behaviour can be turned off by setting the
          `extend_overlapping` parameter to False, in which case the
          interval is not added and an exception is raised
        * if the name has a different value,
          then the interval is not added and an Exception is raised;
          this behaviour can be changed by setting `overwrite_overlapping` to
          True, in which case the new identifier overwrites the old one, both
          by value and dates

        Since **order matters**, multiple intervals need to be sorted by
        start date before being inserted.

        :param name:
        :param othername_type:
        :param overwrite_overlapping: overwrite first overlapping
        :param extend_overlapping: extend first overlapping (touching)
        :param kwargs:
        :return: the instance just added if successful
        """
        kwargs['name'] = name

        # names with no date interval specified are added immediately
        if 'start_date' not in kwargs and 'end_date' not in kwargs:
            i = self.other_names.create(
                othername_type=othername_type,
                **kwargs
            )
            return i
        else:
            # the type was used
            # check if dates intervals overlap
            from popolo.utils import PartialDatesInterval
            from popolo.utils import PartialDate

            # get names having the same type
            same_type_names = self.other_names.filter(
                othername_type=othername_type
            ).order_by('-end_date')

            # new name dates interval as PartialDatesInterval instance
            new_int = PartialDatesInterval(
                start=kwargs.get('start_date', None),
                end=kwargs.get('end_date', None)
            )

            is_overlapping_or_extending = False

            # loop over names of the same type
            for n in same_type_names:
                # existing name dates interval as PartialDatesInterval instance
                n_int = PartialDatesInterval(
                    start=n.start_date,
                    end=n.end_date
                )

                # compute overlap days
                #  > 0 means crossing
                # == 0 means touching
                #  < 0 meand not overlapping
                overlap = PartialDate.intervals_overlap(new_int, n_int)

                if overlap >= 0:
                    # detect "overlaps" and "extensions",

                    if n.name != name:
                        # only crossing dates is a proper overlap
                        if overlap > 0:
                            if overwrite_overlapping:
                                # overwrites existing identifier
                                n.start_date = kwargs['start_date']
                                n.end_date = kwargs['end_date']
                                n.identifier = kwargs['identifier']
                                n.source = kwargs['source']

                                # save i and exit the loop
                                n.save()
                                is_overlapping_or_extending = True
                                break
                            else:
                                # block insertion
                                raise OverlappingIntervalError(
                                    n,
                                    "Name could not be created, "
                                    "due to overlapping dates ({0} : {1})".format(
                                        new_int, n_int
                                    )
                                )

                    else:
                        if extend_overlapping:
                            # extension, get new dates for i
                            if new_int.start.date is None or \
                               n_int.start.date is None:
                                n.start_date = None
                            else:
                                n.start_date = min(
                                    n.start_date, new_int.start.date
                                )

                            if new_int.end.date is None or \
                               n_int.end.date is None:
                                n.end_date = None
                            else:
                                n.end_date = max(
                                    n.end_date, new_int.end.date
                                )

                            # save i and exit the loop
                            n.save()
                            is_overlapping_or_extending = True
                            break
                        else:
                            # block insertion
                            raise OverlappingIntervalError(
                                n,
                                "Name could not be created, "
                                "due to overlapping dates ({0} : {1})".format(
                                    new_int, n_int
                                )
                            )


            # no overlaps, nor extensions, the identifier can be created
            if not is_overlapping_or_extending:
                return self.other_names.create(
                    othername_type=othername_type,
                    **kwargs
                )

    def add_other_names(self, names):
        """add other static names

        :param names: list of dicts containing names' parameters
        :return:
        """
        for n in names:
            self.add_other_name(**n)


class IdentifierShortcutsMixin(object):

    def add_identifier(
        self, identifier, scheme,
        overwrite_overlapping=False,
        merge_overlapping=False,
        extend_overlapping=True,
        same_scheme_values_criterion=False,
        **kwargs
    ):
        """Add identifier to the instance inheriting the mixin

        A check for date interval overlaps is performed between the
        identifier that's to be added and all existing identifiers that
        use the same scheme. Existing identifiers are extracted ordered by
        ascending `start_date`.

        As soon as an overlap is found (first match):
        * if the identifier has the same value,
          then it is by default treated as an extension and date intervals
          are *extended*;
          this behaviour can be turned off by setting the
          `extend_overlapping` parameter to False, in which case the
          interval is not added and an exception is raised
        * if the identifier has a different value,
          then the interval is not added and an Exception is raised;
          this behaviour can be changed by setting `overwrite_overlapping` to
          True, in which case the new identifier overwrites the old one, both
          by value and dates

        Since **order matters**, multiple intervals need to be sorted by
        start date before being inserted.

        :param identifier:
        :param scheme:
        :param overwrite_overlapping: overwrite first overlapping
        :param extend_overlapping: extend first overlapping (touching)
        :param merge_overlapping: get last start_date and first end_date
        :parma same_scheme_values_criterion: True if overlap is computed
            only for identifiers with same scheme and values
            If set to False (default) overlapping is computed for
            identifiers having the same scheme.
        :param kwargs:
        :return: the instance just added if successful
        """

        kwargs['identifier'] = identifier

        # get identifiers having the same scheme,
        same_scheme_identifiers = self.identifiers.filter(scheme=scheme)

        # add identifier if the scheme is new
        if same_scheme_identifiers.count() == 0:
            i = self.identifiers.create(
                scheme=scheme,
                **kwargs
            )
            return i
        else:
            # the scheme is used
            # check if dates intervals overlap
            from popolo.utils import PartialDatesInterval
            from popolo.utils import PartialDate

            # new identifiere dates interval as PartialDatesInterval instance
            new_int = PartialDatesInterval(
                start=kwargs.get('start_date', None),
                end=kwargs.get('end_date', None)
            )

            is_overlapping_or_extending = False

            # loop over identifiers belonging to the same scheme
            for i in same_scheme_identifiers:

                # existing identifier interval as PartialDatesInterval instance
                i_int = PartialDatesInterval(
                    start=i.start_date,
                    end=i.end_date
                )

                # compute overlap days
                #  > 0 means crossing
                # == 0 means touching
                #  < 0 meand not overlapping
                overlap = PartialDate.intervals_overlap(new_int, i_int)

                if overlap >= 0:
                    # detect "overlaps" and "extensions"

                    if i.identifier != identifier:

                        # only crossing dates is a proper overlap
                        # when same
                        if not same_scheme_values_criterion and overlap > 0:
                            if overwrite_overlapping:
                                # overwrites existing identifier
                                i.start_date = kwargs['start_date']
                                i.end_date = kwargs['end_date']
                                i.identifier = kwargs['identifier']
                                i.source = kwargs['source']

                                # save i and exit the loop
                                i.save()

                                is_overlapping_or_extending = True
                                break
                            else:
                                # block insertion
                                raise OverlappingIntervalError(
                                    i,
                                    "Identifier could not be created, "
                                    "due to overlapping dates ({0} : {1})".format(
                                        new_int, i_int
                                    )
                                )
                    else:
                        # same values

                        # same scheme, same date intervals, skip
                        if i_int == new_int:
                            is_overlapping_or_extending = True
                            continue

                        # we can extend, merge or block
                        if extend_overlapping:
                            # extension, get new dates for i
                            if new_int.start.date is None or \
                               i_int.start.date is None:
                                i.start_date = None
                            else:
                                i.start_date = min(i.start_date, new_int.start.date)

                            if new_int.end.date is None or \
                               i_int.end.date is None:
                                i.end_date = None
                            else:
                                i.end_date = max(i.end_date, new_int.end.date)

                            # save i and break the loop
                            i.save()
                            is_overlapping_or_extending = True
                            break
                        elif merge_overlapping:
                            nonnull_start_dates = list(filter(
                                lambda x: x is not None,
                                [new_int.start.date, i_int.start.date]
                            ))
                            if len(nonnull_start_dates):
                                i.start_date = min(nonnull_start_dates)

                            nonnull_end_dates = list(filter(
                                lambda x: x is not None,
                                [new_int.end.date, i_int.end.date]
                            ))
                            if len(nonnull_end_dates):
                                i.end_date = max(nonnull_end_dates)

                            i.save()
                            is_overlapping_or_extending = True
                        else:
                            # block insertion
                            raise OverlappingIntervalError(
                                i,
                                "Identifier with same scheme could not be created, "
                                "due to overlapping dates ({0} : {1})".format(
                                    new_int, i_int
                                )
                            )

            # no overlaps, nor extensions, the identifier can be created
            if not is_overlapping_or_extending:
                return self.identifiers.create(
                    scheme=scheme,
                    **kwargs
                )

    def add_identifiers(self, identifiers, update=True):
        """ add identifiers and skip those that generate exceptions

        Exceptions generated when dates overlap are gathered in a
        pipe-separated array and returned.

        :param identifiers:
        :param update:
        :return:
        """
        exceptions = []
        for i in identifiers:
            try:
                self.add_identifier(**i)
            except Exception as e:
                exceptions.append(str(e))
                pass

        if len(exceptions):
            raise Exception(' | '.join(exceptions))


class ClassificationShortcutsMixin(object):

    def add_classification(self, code, descr, scheme, **kwargs):
        """Add classification to the instance inheriting the mixin

        :param code:   classification code, internal to the scheme
        :param descr:  classification textual description (brief)
        :param scheme: classification scheme (ATECO, LEGAL_FORM_IPA, ...)
        :param kwargs: other params as source, start_date, end_date, ...
        :return: the classification instance just added
        """
        # classifications having the same scheme, code and descr are considered
        # overlapping and will not be added

        # first create the Classification object,
        # or fetch an already existing one
        c, created = Classification.objects.get_or_create(
            scheme=scheme,
            code=code,
            descr=descr,
            defaults=kwargs
        )

        # then add the ClassificationRel to classifications
        self.classifications.get_or_create(
            classification=c
        )

        # and finally return the classification just added
        return c

    def add_classifications(self, classifications):
        """ add multiple classifications, skip those that generate exceptions

        Exceptions are gathered in a
        pipe-separated array and returned.

        :param classifications: classifications to be added (list of dicts)
        :param update: if successive colliding classifications should update
        :return:
        """
        exceptions = []
        for i in classifications:
            try:
                self.add_classification(**i)
            except Exception as e:
                exceptions.append(str(e))
                pass

        if len(exceptions):
            raise Exception(' | '.join(exceptions))


class Error(Exception):
    pass

class OverlappingIntervalError(Error):
    """Raised when date intervals overlap

    Attributes:
        overlapping -- the first entity whose date interval overlaps
        message -- the extended description of the error

    """
    def __init__(self, overlapping, message):
        self.overlapping = overlapping
        self.message = message

    def __str__(self):
        return repr(self.message)



class LinkShortcutsMixin(object):
    def add_link(self, url, **kwargs):
        l, created = Link.objects.get_or_create(
            url=url,
            defaults=kwargs
        )

        # then add the SourceRel to sources
        self.links.get_or_create(
            link=l
        )

        return l

    def add_links(self, links):
        for l in links:
            self.add_link(**l)


class SourceShortcutsMixin(object):
    def add_source(self, url, **kwargs):
        s, created = Source.objects.get_or_create(
            url=url,
            defaults=kwargs
        )

        # then add the SourceRel to sources
        self.sources.get_or_create(
            source=s
        )

        return s

    def add_sources(self, sources):
        for s in sources:
            self.add_source(**s)


@python_2_unicode_compatible
class Person(
    ContactDetailsShortcutsMixin,
    OtherNamesShortcutsMixin,
    IdentifierShortcutsMixin,
    LinkShortcutsMixin, SourceShortcutsMixin,
    Dateframeable, Timestampable, Permalinkable, models.Model
):
    """
    A real person, alive or dead
    see schema at http://popoloproject.com/schemas/person.json#
    """

    json_ld_context = "http://popoloproject.com/contexts/person.jsonld"
    json_ld_type = "http://www.w3.org/ns/person#Person"

    @property
    def slug_source(self):
        return u"{0} {1}".format(self.name, self.birth_date)


    name = models.CharField(
        _("name"),
        max_length=512,
        help_text=_("A person's preferred full name")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(
        'OtherName',
        help_text=_("Alternate or former names")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(
        'Identifier',
        help_text=_("Issued identifiers")
    )

    family_name = models.CharField(
        _("family name"),
        max_length=128, blank=True, null=True,
        help_text=_("One or more family names")
    )

    given_name = models.CharField(
        _("given name"),
        max_length=128, blank=True, null=True,
        help_text=_("One or more primary given names")
    )

    additional_name = models.CharField(
        _("additional name"),
        max_length=128, blank=True, null=True,
        help_text=_("One or more secondary given names")
    )

    honorific_prefix = models.CharField(
        _("honorific prefix"),
        max_length=32, blank=True, null=True,
        help_text=_("One or more honorifics preceding a person's name")
    )

    honorific_suffix = models.CharField(
        _("honorific suffix"),
        max_length=32, blank=True, null=True,
        help_text=_("One or more honorifics following a person's name")
    )

    patronymic_name = models.CharField(
        _("patronymic name"),
        max_length=128, blank=True, null=True,
        help_text=_("One or more patronymic names")
    )

    sort_name = models.CharField(
        _("sort name"),
        max_length=128, blank=True, null=True,
        help_text=_(
            "A name to use in an lexicographically "
            "ordered list"
        )
    )

    email = models.EmailField(
        _("email"),
        blank=True, null=True,
        help_text=_("A preferred email address")
    )

    gender = models.CharField(
        _('gender'),
        max_length=32, blank=True,
        help_text=_("A gender")
    )

    birth_date = models.CharField(
        _("birth date"),
        max_length=10, blank=True, null=True,
        help_text=_("A date of birth")
    )

    death_date = models.CharField(
        _("death date"),
        max_length=10, blank=True, null=True,
        help_text=_("A date of death")
    )

    image = models.URLField(
        _("image"),
        blank=True, null=True,
        help_text=_("A URL of a head shot")
    )

    summary = models.CharField(
        _("summary"),
        max_length=1024, blank=True, null=True,
        help_text=_("A one-line account of a person's life")
    )

    biography = models.TextField(
        _("biography"),
        blank=True, null=True,
        help_text=_(
            "An extended account of a person's life"
        )
    )

    national_identity = models.CharField(
        _("national identity"),
        max_length=128, blank=True, null=True,
        help_text=_("A national identity")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        'ContactDetail',
        help_text="Means of contacting the person"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        'LinkRel',
        help_text="URLs to documents related to the person"
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text="URLs to source documents about the person"
    )

    related_persons = models.ManyToManyField(
        'self',
        through='PersonalRelationship',
        through_fields=('source_person', 'dest_person'),
        symmetrical=False
    )
    url_name = 'person-detail'

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(PersonQuerySet)()
    except:
        objects = PersonQuerySet.as_manager()

    def add_membership(self, organization, **kwargs):
        """Add membership to Organization for member

        :param organization: Organization instance
        :param kwargs: membership parameters
        :return: added Membership
        """
        m = Membership(
            person=self, organization=organization,
            **kwargs
        )
        m.save()

        return m

    def add_memberships(self, organizations):
        """Add multiple *blank* memberships to person.

        :param organizations: list of Organization instance
        :return:
        """
        for o in organizations:
            self.add_membership(o)

    def add_role(self, post):
        """add a role (post) in an Organization

        A *role* is identified by the Membership to a given Post in an
        Organization.

        :param post: the post fullfilled
        :return: the Membership to rhe role
        """
        m = Membership(person=self, post=post, organization=post.organization)
        m.save()

        return m

    def add_role_on_behalf_of(self, post, organization):
        """add a role (post) in an Organization on behhalf of the given
        Organization

        :param post: the post fullfilled
        :param organiazione: the organization on behalf of which the Post
        is fullfilled
        :return: the Membership to rhe role
        """
        m = Membership(
            person=self,
            post=post, organization=post.organization,
            on_behalf_of=organization
        )
        m.save()

        return m

    def add_ownership(self, organization, **kwargs):
        """add this person as owner to the given `organization`

        :param organization: the organization this one will be a owner of
        :param kwargs: ownership parameters
        :return: the added Ownership
        """
        o = Ownership(
            organization=organization,
            owner_person=self,
            **kwargs
        )
        o.save()
        return o

    def add_relationship(self, dest_person, **kwargs):
        """add a personal relaationship to dest_person
        with parameters kwargs

        :param dest_person:
        :param kwargs:
        :return:
        """
        r = PersonalRelationship(
            source_person=self,
            dest_person=dest_person,
            **kwargs
        )
        r.save()
        return r

    def organizations_has_role_in(self):
        """get all organizations the person has a role in

        :return:
        """
        return Organization.objects.filter(
            posts__in=Post.objects.filter(memberships__person=self)
        )

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class PersonalRelationship(
    SourceShortcutsMixin,
    Dateframeable, Timestampable, models.Model
):
    """
    A relationship between two persons.
    Must be defined by a classification (type, ex: friendship, family, ...)

    This is an **extension** to the popolo schema
    """

    # person or organization that is a member of the organization

    source_person = models.ForeignKey(
        'Person',
        related_name='to_relationships',
        verbose_name=_("Source person"),
        help_text=_("The Person the relation starts from")
    )

    # reference to "http://popoloproject.com/schemas/person.json#"
    dest_person = models.ForeignKey(
        'Person',
        related_name='from_relationships',
        verbose_name=_("Destination person"),
        help_text=_("The Person the relationship ends to")
    )

    WEIGHTS = Choices(
        (-1, 'strongly_negative', _('Strongly negative')),
        (-2, 'negative', _('Negative')),
        (0,  'neutral', _('Neutral')),
        (1,  'positive', _('Positive')),
        (2,  'strongly_positive', _('Strongly positive')),
    )
    weight = models.IntegerField(
        _("weight"),
        default=0,
        choices=WEIGHTS,
        help_text=_(
            "The relationship weight, "
            "from strongly negative, to strongly positive"
        )
    )

    classification = models.CharField(
        max_length=255,
        help_text=_(
            "The relationship classification, ex: friendship, family, ..."
        )
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the relationship")
    )

    class Meta:
        verbose_name = _("Personal relationship")
        verbose_name_plural = _("Personal relationships")


    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(
            PersonalRelationshipQuerySet
        )()
    except:
        objects = PersonalRelationshipQuerySet.as_manager()

    def __str__(self):
        if self.label:
            return "{0} -[{1} ({2}]> {3}".format(
                self.source_person.name,
                self.classification,
                self.get_weight_display(),
                self.dest_person.name
            )


@python_2_unicode_compatible
class Organization(
    ContactDetailsShortcutsMixin,
    OtherNamesShortcutsMixin,
    IdentifierShortcutsMixin,
    ClassificationShortcutsMixin,
    LinkShortcutsMixin,
    SourceShortcutsMixin,
    Dateframeable, Timestampable, Permalinkable, models.Model
):
    """
    A group with a common purpose or reason for existence that goes beyond
    the set of people belonging to it
    see schema at http://popoloproject.com/schemas/organization.json#
    """

    @property
    def slug_source(self):
        return  "{0} {1}".format(
            self.name, self.identifier
        )

    name = models.CharField(
        _("name"),
        max_length=512,
        help_text=_("A primary name, e.g. a legally recognized name")
    )

    identifier = models.CharField(
        _("identifier"),
        max_length=32,
        blank=True, null=True, unique=True,
        help_text=_("The main issued identifier, or fiscal code, for organization")
    )

    classification = models.CharField(
        _("classification"),
        max_length=256,
        blank=True, null=True,
        help_text=_("The main classification, legal form in many cases")
    )

    classifications = GenericRelation(
        'ClassificationRel',
        help_text=_("ATECO, Legal Form and other classifications")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(
        'OtherName',
        help_text=_("Alternate or former names")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(
        'Identifier', help_text=_("Issued identifiers")
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    parent = models.ForeignKey(
        'Organization',
        blank=True, null=True,
        related_name='children',
        verbose_name=_("Parent"),
        help_text=_(
           "The organization that contains this "
           "organization"
        )
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        'Area',
        blank=True, null=True,
        related_name='organizations',
        help_text=_(
            "The geographic area to which this "
            "organization is related")
        )

    abstract = models.CharField(
        _("abstract"),
        max_length=256, blank=True, null=True,
        help_text=_("A one-line description of an organization")
    )

    description = models.TextField(
        _("biography"),
        blank=True, null=True,
        help_text=_("An extended description of an organization")
    )

    founding_date = models.CharField(
        _("founding date"),
        max_length=10,
        null=True, blank=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{4}(-[0-9]{2}){0,2}$',
                message='founding date must follow the given pattern: ^[0-9]{'
                '4}(-[0-9]{2}){0,2}$',
                code='invalid_founding_date'
            )
        ],
        help_text=_("A date of founding")
    )

    dissolution_date = models.CharField(
        _("dissolution date"),
        max_length=10,
        null=True, blank=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{4}(-[0-9]{2}){0,2}$',
                message='dissolution date must follow the given pattern: ^['
                '0-9]{4}(-[0-9]{2}){0,2}$',
                code='invalid_dissolution_date'
            )
        ],
        help_text=_("A date of dissolution")
    )

    image = models.URLField(
        _("image"),
        max_length=255,
        blank=True, null=True,
        help_text=_(
            "A URL of an image, to identify the organization visually"
        )
    )

    new_orgs = models.ManyToManyField(
        'Organization',
        blank=True,
        related_name='old_orgs', symmetrical=False,
        help_text=_(
            "Link to organization(s) after dissolution_date, "
            "needed to track mergers, acquisition, splits."
        )
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        'ContactDetail',
        help_text=_("Means of contacting the organization")

    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        'LinkRel',
        help_text=_("URLs to documents about the organization")
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the organization")
    )

    person_members = models.ManyToManyField(
        'Person',
        through='Membership',
        through_fields=('organization', 'person'),
        related_name='organizations_memberships'

    )

    organization_members = models.ManyToManyField(
        'Organization',
        through='Membership',
        through_fields=('organization', 'member_organization'),
        related_name='organizations_memberships'
    )

    @property
    def members(self):
        """Returns list of members (it's not a queryset)

        :return: list of Person or Organization instances
        """
        return \
            list(self.person_members.all()) + \
            list(self.organization_members.all())

    person_owners = models.ManyToManyField(
        'Person',
        through='Ownership',
        through_fields=('organization', 'owner_person'),
        related_name='organizations_ownerships'
    )

    organization_owners = models.ManyToManyField(
        'Organization',
        through='Ownership',
        through_fields=('organization', 'owner_organization'),
        related_name='organization_ownerships'
    )

    @property
    def owners(self):
        """Returns list of owners (it's not a queryset)

        :return: list of Person or Organization instances
        """
        return \
            list(self.person_owners.all()) + \
            list(self.organization_owners.all())

    url_name = 'organization-detail'

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(OrganizationQuerySet)()
    except:
        objects = OrganizationQuerySet.as_manager()

    def add_member(self, member, **kwargs):
        """add a member to this organization

        :param member: a Person or an Organization
        :param kwargs: membership parameters
        :return: the added member (be it Person or Organization)
        """
        if isinstance(member, Person):
            m = Membership(organization=self, person=member, **kwargs)
        elif isinstance(member, Organization):
            m = Membership(
                organization=self, member_organization=member, **kwargs
            )
        else:
            raise Exception(_(
                "Member must be Person or Organization"
            ))
        m.save()
        return m


    def add_members(self, members):
        """add multiple *blank* members to this organization

        :param members: list of Person/Organization to be added as members
        :return:
        """
        for m in members:
            self.add_member(m)

    def add_membership(self, organization, **kwargs):
        """add this organization as member to the given `organization`

        :param organization: the organization this one will be a member of
        :param kwargs: membership parameters
        :return: the added Membership
        """
        m = Membership(
            organization=organization,
            member_organization=self,
            **kwargs
        )
        m.save()
        return m

    def add_owner(self, owner, **kwargs):
        """add a owner to this organization

        :param owner: a Person or an Organization
        :param kwargs: ownership parameters
        :return: the added owner (be it Person or Organization)
        """
        if isinstance(owner, Person):
            o = Ownership(organization=self, owner_person=owner, **kwargs)
        elif isinstance(owner, Organization):
            o = Ownership(
                organization=self, owner_organization=owner, **kwargs
            )
        else:
            raise Exception(_(
                "Owner must be Person or Organization"
            ))
        o.save()
        return o


    def add_ownership(self, organization, **kwargs):
        """add this organization as owner to the given `organization`

        :param organization: the organization this one will be a owner of
        :param kwargs: ownership parameters
        :return: the added Membership
        """
        o = Ownership(
            organization=organization,
            owner_organization=self,
            **kwargs
        )
        o.save()
        return o

    def add_post(self, **kwargs):
        """add post, specified with kwargs to this organization

        :param kwargs: Post parameters
        :return: the added Post
        """
        p = Post(organization=self, **kwargs)
        p.save()
        return p

    def add_posts(self, posts):
        for p in posts:
            self.add_post(**p)

    def merge_from(self, *args, **kwargs):
        """merge a list of organizations into this one, creating relationships
        of new/old orgs

        :param args: elements to merge into
        :param kwargs: may contain the moment key
        :return:
        """
        moment = kwargs.get(
            'moment', datetime.strftime(datetime.now(), '%Y-%m-%d')
        )

        for i in args:
            i.close(
                moment=moment,
                reason=_("Merged into other organizations")
            )
            i.new_orgs.add(self)
        self.start_date = moment
        self.save()

    def split_into(self, *args, **kwargs):
        """split this organization into a list of other organizations, creating
        relationships of new/old orgs

        :param args: elements to be split into
        :param kwargs: keyword args that may contain moment
        :return:
        """
        moment = kwargs.get(
            'moment', datetime.strftime(datetime.now(), '%Y-%m-%d')
        )

        for i in args:
            i.start_date=moment
            i.save()
            self.new_orgs.add(i)
        self.close(moment=moment, reason=_("Split into other organiations"))


    def __str__(self):
        return self.name


@python_2_unicode_compatible
class ClassificationRel(
    GenericRelatable,
    Dateframeable,
    models.Model
):
    """
    The relation between a generic object and a Classification
    """
    classification = models.ForeignKey(
        'Classification',
        related_name='related_objects',
        help_text=_("A Classification instance assigned to this object")
    )

    def __str__(self):
        return self.content_object, self.classification


@python_2_unicode_compatible
class Classification(
    SourceShortcutsMixin,
    Dateframeable,
    models.Model
):
    """
    A generic, hierarchical classification usable in different contexts
    """
    scheme = models.CharField(
        _("scheme"),
        max_length=128, blank=True,
        help_text=_("A classification scheme, e.g. ATECO, or FORMA_GIURIDICA")
    )

    code = models.CharField(
        _("code"),
        max_length=128,
        help_text=_("An alphanumerical code in use within the scheme")
    )

    descr = models.CharField(
        _("description"),
        max_length=512,
        help_text=_("The extended, textual description of the classification")
    )

    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the classification")
    )

     # reference to "http://popoloproject.com/schemas/area.json#"
    parent = models.ForeignKey(
        'Classification',
        blank=True, null=True,
        related_name='children',
        help_text=_(
            "The parent classification."
        )
    )

    class Meta:
        verbose_name = _("Classification")
        verbose_name_plural = _("Classifications")
        unique_together = ('scheme', 'code', 'descr')

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(ClassificationQuerySet)()
    except:
        objects = ClassificationQuerySet.as_manager()

    def __str__(self):
        return "{0}: {1} - {2}".format(self.scheme, self.code, self.descr)


@python_2_unicode_compatible
class Post(
    ContactDetailsShortcutsMixin,
    LinkShortcutsMixin, SourceShortcutsMixin,
    Dateframeable, Timestampable, Permalinkable,
    models.Model
):
    """
    A position that exists independent of the person holding it
    see schema at http://popoloproject.com/schemas/json#
    """

    @property
    def slug_source(self):
        return self.label

    label = models.CharField(
        _("label"),
        max_length=256, blank=True,
        help_text=_("A label describing the post")
    )

    other_label = models.CharField(
        _("other label"),
        max_length=32, blank=True, null=True,
        help_text=_(
            "An alternate label, such as an abbreviation"
        )
    )

    role = models.CharField(
        _("role"),
        max_length=256, blank=True, null=True,
        help_text=_(
            "The function that the holder of the post fulfills"
        )
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey(
        'Organization',
        related_name='posts',
        verbose_name=_("Organization"),
        help_text=_("The organization in which the post is held")
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        'Area',
        blank=True, null=True,
        related_name='posts',
        verbose_name=_("Area"),
        help_text=_("The geographic area to which the post is related")
    )

    appointed_by = models.ForeignKey(
        'Post',
        blank=True, null=True,
        related_name='appointees',
        verbose_name=_("Appointed by"),
        help_text=_(
            "The Post that officially appoints members to this one, "
            "ex: Secr. of Defence is appointed by POTUS"
        )
    )

    holders = models.ManyToManyField(
        'Person',
        through='Membership',
        through_fields=('post', 'person'),
        related_name='roles'
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        'ContactDetail',
        help_text=_("Means of contacting the holder of the post")
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        'LinkRel',
        help_text=_("URLs to documents about the post")
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the post")
    )

    url_name = 'post-detail'

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(PostQuerySet)()
    except:
        objects = PostQuerySet.as_manager()

    def add_person(self, person, **kwargs):
        """add given person to this post (through membership)
        A person having a post is also an explicit member
        of the organization holding the post.

        :param person: person to add
        :param kwargs: membership parameters (label, dates, ...)
        :return:
        """
        m = Membership(
            post=self, person=person,
            organization=self.organization,
            **kwargs
        )
        m.save()

    def add_person_on_behalf_of(self, person, organization, **kwargs):
        """add given `person` to this post (through a membership)
        on behalf of given `organization`

        :param person:
        :param organization: the organization on behalf the post is taken
        :param kwargs: membership parameters (label, dates, ...)
        :return:
        """
        m = Membership(
            post=self,
            person=person, organization=self.organization,
            on_behalf_of=organization,
            **kwargs
        )
        m.save()

    def add_appointer(self, role):
        """add role that appoints members to this one

        :param role: The apponinter
        :return: the appointee
        """
        self.appointed_by = role
        self.save()
        return self

    def __str__(self):
        return self.label


@python_2_unicode_compatible
class Membership(
    ContactDetailsShortcutsMixin,
    LinkShortcutsMixin, SourceShortcutsMixin,
    Dateframeable, Timestampable, Permalinkable,
    models.Model
):
    """
    A relationship between a person and an organization
    see schema at http://popoloproject.com/schemas/membership.json#
    """

    @property
    def slug_source(self):
        return u"{0} {1}".format(
            self.member.name, self.organization.name, self.label
        )

    label = models.CharField(
        _("label"),
        max_length=256, blank=True, null=True,
        help_text=_("A label describing the membership")
    )

    role = models.CharField(
        _("role"),
        max_length=256, blank=True, null=True,
        help_text=_("The role that the member fulfills in the organization")
    )

    # person or organization that is a member of the organization
    member_organization = models.ForeignKey(
        'Organization',
        blank=True, null=True,
        related_name='memberships_as_member',
        verbose_name=_("Person"),
        help_text=_("The person who is a member of the organization")
    )

    # reference to "http://popoloproject.com/schemas/person.json#"
    person = models.ForeignKey(
        'Person',
        blank=True, null=True,
        related_name='memberships',
        verbose_name=_("Person"),
        help_text=_("The person who is a member of the organization")
    )

    @property
    def member(self):
        if self.member_organization:
            return self.member_organization
        else:
            return self.person

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey(
        'Organization',
        blank=True, null=True,
        related_name='memberships',
        verbose_name=_("Organization"),
        help_text=_(
             "The organization in which the person or organization is a member"
         )
     )

    on_behalf_of = models.ForeignKey(
        'Organization',
        blank=True, null=True,
        related_name='memberships_on_behalf_of',
        verbose_name=_("On behalf of"),
        help_text=_(
            "The organization on whose behalf the person "
            "is a member of the organization"
        )
    )

    # reference to "http://popoloproject.com/schemas/post.json#"
    post = models.ForeignKey(
        'Post',
        blank=True, null=True,
        related_name='memberships',
        verbose_name=_("Post"),
        help_text=_(
            "The post held by the person in the "
            "organization through this membership"
        )
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        'Area',
        blank=True, null=True,
        related_name='memberships',
        verbose_name=_("Area"),
        help_text=_("The geographic area to which the post is related")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        'ContactDetail',
        help_text=_("Means of contacting the member of the organization")
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        'LinkRel',
        help_text=_("URLs to documents about the membership")
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the membership")
    )

    url_name = 'membership-detail'

    class Meta:
        verbose_name = _("Membership")
        verbose_name_plural = _("Memberships")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(MembershipQuerySet)()
    except:
        objects = MembershipQuerySet.as_manager()

    def __str__(self):
        if self.label:
            return "{0} -[{1}]> {2}".format(
                getattr(self.member, 'name'),
                self.label,
                self.organization
            )
        else:
            return "{0} -[member of]> {1}".format(
                getattr(self.member, 'name'),
                self.organization
            )


@python_2_unicode_compatible
class Ownership(
    SourceShortcutsMixin,
    Dateframeable, Timestampable, Permalinkable, models.Model
):
    """
    A relationship between an organization and an owner
    (be it a Person or another Organization), that indicates
    an ownership and quantifies it.

    This is an **extension** to the popolo schema
    """
    @property
    def slug_source(self):
        return u"{0} {1} ({2}%)".format(
            self.owner.name, self.organization.name, self.percentage*100
        )


    # person or organization that is a member of the organization
    organization = models.ForeignKey(
        'Organization',
        related_name='owned_organizations',
        verbose_name=_("Person"),
        help_text=_("The organization that is owned")
    )

    # reference to "http://popoloproject.com/schemas/person.json#"
    owner_person = models.ForeignKey(
        'Person',
        blank=True, null=True,
        related_name='ownerships',
        verbose_name=_("Person"),
        help_text=_("An owner of the organization, when it is a Person")
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    owner_organization = models.ForeignKey(
        'Organization',
        blank=True, null=True,
        related_name='ownerships',
        verbose_name=_("Organization"),
        help_text=_("An owner of the organization, when it is an Organization")
    )

    percentage = models.FloatField(
        _("percentage ownership"),
        validators=[validate_percentage, ],
        help_text=_(
            "The *required* percentage ownership, expressed as a floating "
            "number, from 0 to 1"
        )
    )
    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the ownership")
    )

    @property
    def owner(self):
        if self.owner_organization:
            return self.owner_organization
        else:
            return self.owner_person


    url_name = 'ownership-detail'

    class Meta:
        verbose_name = _("Ownership")
        verbose_name_plural = _("Ownerships")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(OwnershipQuerySet)()
    except:
        objects = OwnershipQuerySet.as_manager()

    def __str__(self):
        if self.label:
            return "{0} -[owns {1}% of]> {2}".format(
                getattr(self.owner, 'name'),
                self.percentage,
                self.organization.name
            )


@python_2_unicode_compatible
class ContactDetail(
    SourceShortcutsMixin,
    Timestampable, Dateframeable, GenericRelatable,
    models.Model
):
    """
    A means of contacting an entity
    see schema at http://popoloproject.com/schemas/contact-detail.json#
    """

    CONTACT_TYPES = Choices(
        ('ADDRESS', 'address', _('Address')),
        ('EMAIL', 'email', _('Email')),
        ('URL', 'url', _('Url')),
        ('MAIL', 'mail', _('Snail mail')),
        ('TWITTER', 'twitter', _('Twitter')),
        ('FACEBOOK', 'facebook', _('Facebook')),
        ('PHONE', 'phone', _('Telephone')),
        ('MOBILE', 'mobile', _('Mobile')),
        ('TEXT', 'text', _('Text')),
        ('VOICE', 'voice', _('Voice')),
        ('FAX', 'fax', _('Fax')),
        ('CELL', 'cell', _('Cell')),
        ('VIDEO', 'video', _('Video')),
        ('PAGER', 'pager', _('Pager')),
        ('TEXTPHONE', 'textphone', _('Textphone')),
    )

    label = models.CharField(
        _("label"),
        max_length=256, blank=True,
        help_text=_("A human-readable label for the contact detail")
    )

    contact_type = models.CharField(
        _("type"),
        max_length=12,
        choices=CONTACT_TYPES,
        help_text=_("A type of medium, e.g. 'fax' or 'email'")
    )

    value = models.CharField(
        _("value"),
        max_length=256,
        help_text=_("A value, e.g. a phone number or email address")
    )

    note = models.CharField(
        _("note"),
        max_length=512, blank=True,
        help_text=_(
            "A note, e.g. for grouping contact details by physical location"
        )
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the contact detail")
    )

    class Meta:
        verbose_name = _("Contact detail")
        verbose_name_plural = _("Contact details")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(ContactDetailQuerySet)()
    except:
        objects = ContactDetailQuerySet.as_manager()

    def __str__(self):
        return u"{0} - {1}".format(self.value, self.contact_type)


@python_2_unicode_compatible
class Area(
    SourceShortcutsMixin, LinkShortcutsMixin,
    IdentifierShortcutsMixin, OtherNamesShortcutsMixin,
    Permalinkable, Dateframeable, Timestampable,
    models.Model
):
    """
    An Area insance is a geographic area whose geometry may change over time.

    An area may change the name, or end its status as autonomous place,
    for a variety of reasons this events are mapped through these
    fields:

    - reason_end - a brief description of the reason (merge, split, ...)
    - new_places, old_places - what comes next, or what was before,
      this is multiple to allow description of merges and splits
    - popolo.behaviours.Dateframeable's start_date and end_date fields

    From **TimeStampedModel** the class inherits **created** and
    **modified** fields, to keep track of creation and
    modification timestamps

    From **Prioritized**, it inherits the **priority** field,
    to allow custom sorting order

    """
    @property
    def slug_source(self):
        return u"{0}".format(
            self.pk
        )

    name = models.CharField(
        _("name"),
        max_length=256, blank=True,
        help_text=_("The official, issued name")
    )

    identifier = models.CharField(
        _("identifier"),
        max_length=128, blank=True,
        unique=True,
        help_text=_("The main issued identifier")
    )

    classification = models.CharField(
        _("classification"),
        max_length=128, blank=True,
        help_text=_("An area category, according to GEONames definitions: "
            "http://www.geonames.org/export/codes.html")
    )

    ISTAT_CLASSIFICATIONS = Choices(
        ('NAZ',  'nazione',      _('Country')),
        ('RIP',  'ripartizione', _('Geographic partition')),
        ('REG',  'regione',      _('Region')),
        ('PROV', 'provincia',    _('Province')),
        ('CM',   'metro',        _('Metropolitan area')),
        ('COM',  'comune',       _('Municipality')),
    )
    istat_classification = models.CharField(
        _("ISTAT classification"),
        max_length=4, blank=True, null=True,
        choices=ISTAT_CLASSIFICATIONS,
        help_text=_("An area category, according to ISTAT: "
            "Ripartizione Geografica, Regione, Provincia, "
            "Città Metropolitana, Comune")
    )


    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(
        'Identifier',
        help_text=_(
            "Other issued identifiers (zip code, other useful codes, ...)"
        )
    )

    @property
    def other_identifiers(self):
        return self.identifiers

    # array of items referencing
    # "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(
        'OtherName',
        help_text=_("Alternate or former names")
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    parent = models.ForeignKey(
        'Area',
        blank=True, null=True,
        related_name='children',
        verbose_name=_('Main parent'),
        help_text=_(
            "The area that contains this area, "
            "as for the main administrative subdivision."
        )
    )

    is_provincial_capital = models.NullBooleanField(
        blank=True, null=True,
        verbose_name=_('Is provincial capital'),
        help_text=_(
            'If the city is a provincial capital.'
            'Takes the Null value if not a municipality.'
        )
    )

    geom = models.TextField(
        _("geom"),
        null=True, blank=True,
        help_text=_(
            "A geometry, expressed as text, eg: GeoJson, TopoJson, KML"
        )
    )

    gps_lat = models.DecimalField(
        _("GPS Latitude"),
        null=True, blank=True,
        max_digits=9, decimal_places=6,
        help_text=_("The Latitude, expressed as a float, eg: 85.3420")
    )

    gps_lon = models.DecimalField(
        _("GPS Longitude"),
        null=True, blank=True,
        max_digits=9, decimal_places=6,
        help_text=_("The Longitude, expressed as a float, eg: 27.7172")
    )

    # inhabitants, can be useful for some queries
    inhabitants = models.PositiveIntegerField(
        _("inhabitants"),
        null=True, blank=True,
        help_text=_("The total number of inhabitants")
    )

    # array of items referencing "http://popoloproject.com/schemas/links.json#"
    links = GenericRelation(
        'LinkRel',
        blank=True, null=True,
        help_text=_("URLs to documents relted to the Area")
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        blank=True, null=True,
        help_text=_("URLs to source documents about the Area")
    )

    # related areas
    related_areas = models.ManyToManyField(
        'self',
        through='AreaRelationship',
        through_fields=('source_area', 'dest_area'),
        help_text=_("Relationships between areas"),
        related_name='inversely_related_areas',
        symmetrical=False
    )

    new_places = models.ManyToManyField(
        'self', blank=True,
        related_name='old_places', symmetrical=False,
        help_text=_("Link to area(s) after date_end")
    )

    url_name = 'area-detail'

    class Meta:
        verbose_name = _("Geographic Area")
        verbose_name_plural = _("Geographic Areas")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(AreaQuerySet)()
    except:
        objects = AreaQuerySet.as_manager()

    def add_i18n_name(self, name, language):
        """add an i18 name to the area
        if the name already exists, then it is not duplicated

        :param name: The i18n name
        :param language: a Language instance
        :return:
        """

        if not isinstance(language, Language):
            raise Exception(
                _("The language parameter needs to be a Language instance")
            )
        i18n_name, created = self.i18n_names.get_or_create(
            language=language,
            name=name
        )

        return i18n_name

    def merge_from(self, *areas, **kwargs):
        """merge a list of areas into this one, creating relationships
        of new/old places

        :param areas:
        :param kwargs:
        :return:
        """
        moment=kwargs.get(
            'moment', datetime.strftime(datetime.now(), '%Y-%m-%d')
        )

        for ai in areas:
            ai.close(moment=moment, reason=_("Merged into other areas"))
            ai.new_places.add(self)
        self.start_date = moment
        self.save()

    def split_into(self, *areas, **kwargs):
        """split this area into a list of other areas, creating
        relationships of new/old places

        :param areas:
        :param kwargs: keyword args that may contain moment
        :return:
        """
        moment=kwargs.get(
            'moment', datetime.strftime(datetime.now(), '%Y-%m-%d')
        )

        for ai in areas:
            ai.start_date=moment
            ai.save()
            self.new_places.add(ai)
        self.close(moment=moment, reason=_("Split into other areas"))

    def add_relationship(self, area, classification,
        start_date=None, end_date=None, **kwargs
    ):
        """add a personal relaationship to dest_area
        with parameters kwargs

        :param area: destination area
        :param classification: the classification (rel label)
        :param start_date:
        :param end_date:
        :param kwargs: other relationships parameters
        :return: a Relationship instance
        """
        relationship, created = AreaRelationship.objects.get_or_create(
            source_area=self,
            dest_area=area,
            classification=classification,
            start_date=start_date,
            end_date=end_date,
            defaults=kwargs
        )
        return relationship, created

    def remove_relationship(self, area, classification,
        start_date, end_date, **kwargs
    ):
        """remove a relationtip to an area

        will raise an exception if no relationships or
        more than one are found

        :param area: destination area
        :param classification: the classification (rel label)
        :param start_date:
        :param end_date:
        :param kwargs: other relationships parameters
        :return:
        """
        r = AreaRelationship.objects.filter(
            source_area=self,
            dest_area=area,
            classification=classification,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )

        if r.count() > 1:
            raise Exception(_("More than one relationships found"))
        elif r.count() == 0:
            raise Exception(_("No relationships found"))
        else:
            r.delete()

    def get_relationships(self, classification):
        return self.from_relationships.filter(
            classification=classification
        ).select_related('source_area', 'dest_area')

    def get_inverse_relationships(self, classification):
        return self.to_relationships.filter(
            classification=classification
        ).select_related('source_area', 'dest_area')

    def get_former_parents(self, moment_date):
        """returns all parent relationtips valid at moment_date

        If moment_date is none, then returns all relationtips independently
        from their start and end dates

        :param moment_date: moment of validity, as YYYY-MM-DD
        :return: AreaRelationship queryset,
            with source_area and dest_area pre-selected
        """
        rels = self.get_relationships(
            AreaRelationship.CLASSIFICATION_TYPES.former_istat
        ).order_by('-end_date')

        if moment_date is not None:
            rels = rels.filter(
                Q(start_date__lt=moment_date) | Q(start_date__isnull=True)
            ).filter(
                Q(end_date__gt=moment_date) | Q(end_date__isnull=True)
            )

        return rels

    def get_former_children(self, start_date, end_date):
        """returns all children relationtips valid at moment_date

        If moment_date is none, then returns all relationtips independently
        from their start and end dates

        :param moment_date: moment of validity, as YYYY-MM-DD
        :return: AreaRelationship queryset,
            with source_area and dest_area pre-selected
        """
        rels = self.get_inverse_relationships(
            AreaRelationship.CLASSIFICATION_TYPES.former_istat
        ).order_by('-end_date')

        if moment_date is not None:
            rels = rels.filter(
                Q(start_date__lt=moment_date) | Q(start_date__isnull=True)
            ).filter(
                Q(end_date__gt=moment_date) | Q(end_date__isnull=True)
            )

        return rels

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class AreaRelationship(
    SourceShortcutsMixin,
    Dateframeable, Timestampable, models.Model
):
    """
    A relationship between two areas.
    Must be defined by a classification (type, ex: other_parent, previosly_in, ...)

    This is an **extension** to the popolo schema
    """

    source_area = models.ForeignKey(
        'Area',
        related_name='from_relationships',
        verbose_name=_("Source area"),
        help_text=_("The Area the relation starts from")
    )

    dest_area = models.ForeignKey(
        'Area',
        related_name='to_relationships',
        verbose_name=_("Destination area"),
        help_text=_("The Area the relationship ends to")
    )

    CLASSIFICATION_TYPES = Choices(
        (
            'FIP',
            'former_istat_parent',
            _('Former ISTAT parent')
        ),
        (
            'AMP',
            'alternate_mountain_community_parent',
            _('Alternate mountain community parent')
        ),
        (
            'ACP',
            'alternate_consortium_parent',
            _('Alternate consortium of municipality parent')
        ),
    )
    classification = models.CharField(
        max_length=3,
        choices=CLASSIFICATION_TYPES,
        help_text=_(
            "The relationship classification, ex: Former ISTAT parent, ..."
        )
    )

    note = models.TextField(
        blank=True, null=True,
        help_text=_(
            "Additional info about the relationship"
        )
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the relationship")
    )

    class Meta:
        verbose_name = _("Area relationship")
        verbose_name_plural = _("Area relationships")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(
            AreaRelationshipQuerySet
        )()
    except:
        objects = AreaRelationshipQuerySet.as_manager()

    def __str__(self):
        if self.classification:
            return "{0} -[{1} ({3} -> {4})]-> {2}".format(
                self.source_area.name,
                self.get_classification_display(),
                self.dest_area.name,
                self.start_date,
                self.end_date
            )
        else:
            return "{0} -[({2} -> {3})]-> {1}".format(
                self.source_area.name,
                self.dest_area.name,
                self.start_date,
                self.end_date
            )


@python_2_unicode_compatible
class AreaI18Name(models.Model):
    """
    Internationalized name for an Area.
    Contains references to language and area.
    """
    area = models.ForeignKey(
        'Area',
        related_name='i18n_names'
    )

    language = models.ForeignKey(
        'Language',
        verbose_name=_('Language')
    )

    name = models.CharField(
        _("name"),
        max_length=255
    )


    def __str__(self):
        return "{0} - {1}".format(self.language, self.name)

    class Meta:
        verbose_name = _('I18N Name')
        verbose_name_plural = _('I18N Names')
        unique_together = ('area', 'language', 'name')


@python_2_unicode_compatible
class Language(models.Model):
    """
    Maps languages, with names and 2-char iso 639-1 codes.
    Taken from http://dbpedia.org, using a sparql query
    """
    name = models.CharField(
        _("name"),
        max_length=128,
            help_text=_("English name of the language")
    )

    iso639_1_code = models.CharField(
        _("iso639_1 code"),
        max_length=2, unique=True,
        help_text=_("ISO 639_1 code, ex: en, it, de, fr, es, ..."),
    )

    dbpedia_resource = models.CharField(
        _("dbpedia resource"),
        max_length=255,
        blank=True, null=True,
        help_text=_("DbPedia URI of the resource"),
        unique=True
    )

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")

    def __str__(self):
        return u"{0} ({1})".format(self.name, self.iso639_1_code)


@python_2_unicode_compatible
class ElectoralEvent(
    SourceShortcutsMixin, LinkShortcutsMixin,
    Permalinkable, Dateframeable, Timestampable,
    models.Model
):
    """
    An electoral event generically describes an electoral session.

    It is used mainly to group all electoral results.

    This is an extension of the Popolo schema
    """
    @property
    def slug_source(self):
        return u"{0} {1}".format(
            self.name, self.get_event_type_display()
        )

    name = models.CharField(
        _("name"),
        max_length=256, blank=True, null=True,
        help_text=_("A primary, generic name, e.g.: Local elections 2016")
    )

    EVENT_TYPES = Choices(
        ('SIN', 'singleround', _('Single round')),
        ('1ST', 'firstround',  _('First round')),
        ('BAL', 'runoff',      _('Run-off election')),
    )
    event_type = models.CharField(
        _("event type"),
        default='SIN',
        max_length=3,
        choices = EVENT_TYPES,
        help_text=_("The electoral event type, e.g.: First round, run-off")
    )

    identifier = models.CharField(
        _("identifier"),
        max_length=128,
        blank=True, null=True,
        help_text=_("An issued identifier")
    )

    CLASSIFICATIONS = Choices(
        ('GEN', 'general',    _('General election')),
        ('REG', 'regional',   _('Regional election')),
        ('PRO', 'provincial', _('Provincial election')),
        ('LOC', 'local',      _('Local election')),
        ('BY',  'special',    _('Special election')),
    )
    classification = models.CharField(
        _("election classification"),
        max_length=3,
        choices=CLASSIFICATIONS,
        help_text=_("An election classification, e.g. Presdential, Municipal")
    )

    electoral_system = models.CharField(
        _("electoral system"),
        null=True,
        max_length=255,
        help_text=_(
            "The electoral system under which this election session is held"
        )
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to sources about the electoral event")
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        'LinkRel',
        help_text=_("URLs to documents referring to the electoral event")
    )

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(
            ElectoralEventQuerySet
        )()
    except:
        objects = ElectoralEventQuerySet.as_manager()

    class Meta:
        verbose_name = _("Electoral event")
        verbose_name_plural = _("Electoral events")

    def add_result(self, **electoral_result):
        self.results.create(**electoral_result)

    def __str__(self):
        return u"{0} - {1}".format(
            self.name, self.get_event_type_display()
        )

@python_2_unicode_compatible
class ElectoralResult(
    SourceShortcutsMixin, LinkShortcutsMixin,
    Permalinkable, Timestampable, models.Model
):
    """
    An electoral result is a set of numbers and percentages, describing
    a general, list or personal outcome within an electoral session.

    It regards a single Organization (usually an institution).
    It may regard a certain constituency (Area).
    It may regard an electoral list (Organization).
    It may regard a candidate (Person).

    It is always the child of an ElectoralEvent (session).

    When it's related to a general result, then generic values are
    populated.
    When it's related to a list number and percentage of votes of the list
    are also populated.
    When it's related to a person (candidate), then the flag `is_elected` is
    populated.

    When a result is not related to a constituency (Area), then it means
    the numbers refer to the total for all constituencies involved.

    This is an extension of the Popolo schema
    """

    @property
    def slug_source(self):

        fields = [
            self.event, self.organization
        ]
        if self.constituency is None:
            fields.append(self.constituency)

        if self.list:
            fields.append(self.list)

        if self.candidate:
            fields.append(self.candidate)

        return " ".join(map(str, fields))

    event = models.ForeignKey(
        'ElectoralEvent',
        related_name='results',
        verbose_name=_('Electoral event'),
        help_text=_('The generating electoral event')
    )

    constituency = models.ForeignKey(
        'Area',
        blank=True, null=True,
        related_name='electoral_results',
        verbose_name=_('Electoral constituency'),
        help_text=_(
            'The electoral constituency these electoral data are referred to'
        )
    )

    organization = models.ForeignKey(
        'Organization',
        related_name='general_electoral_results',
        verbose_name=_('Institution'),
        help_text=_(
            'The institution these electoral data are referred to'
        )
    )

    list = models.ForeignKey(
        'Organization',
        blank=True, null=True,
        related_name='list_electoral_results',
        verbose_name=_('Electoral list'),
        help_text=_(
            "The electoral list these electoral data are referred to"
        )
    )

    candidate = models.ForeignKey(
        'Person',
        blank=True, null=True,
        related_name='electoral_results',
        verbose_name=_('Candidate'),
        help_text=_(
            "The candidate in the election these data are referred to"
        )
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to sources about the electoral result")
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        'LinkRel',
        help_text=_("URLs to documents referring to the electoral result")
    )

    n_eligible_voters = models.PositiveIntegerField(
        _('Total number of eligible voters'),
        blank=True, null=True,
        help_text=_(
            'The total number of eligible voter'
        )
    )

    n_ballots = models.PositiveIntegerField(
        _('Total number of ballots casted'),
        blank=True, null=True,
        help_text=_(
            'The total number of ballots casted'
        )
    )

    perc_turnout = models.FloatField(
        _('Voter turnout'),
        blank=True, null=True,
        validators=[validate_percentage, ],
        help_text=_(
            'The percentage of eligible voters that casted a ballot'
        )
    )

    perc_valid_votes = models.FloatField(
        _('Valid votes perc.'),
        blank=True, null=True,
        validators=[validate_percentage, ],
        help_text=_(
            'The percentage of valid votes among those cast'
        )
    )

    perc_null_votes = models.FloatField(
        _('Null votes perc.'),
        blank=True, null=True,
        validators=[validate_percentage, ],
        help_text=_(
            'The percentage of null votes among those cast'
        )
    )

    perc_blank_votes = models.FloatField(
        _('Blank votes perc.'),
        blank=True, null=True,
        validators=[validate_percentage, ],
        help_text=_(
            'The percentage of blank votes among those cast'
        )
    )

    n_preferences = models.PositiveIntegerField(
        _('Total number of preferences'),
        blank=True, null=True,
        help_text=_(
            'The total number of preferences expressed for the list/candidate'
        )
    )

    perc_preferences = models.FloatField(
        _('Preference perc.'),
        blank=True, null=True,
        validators=[validate_percentage, ],
        help_text=_(
            'The percentage of preferences expressed for the list/candidate'
        )
    )

    is_elected = models.NullBooleanField(
        _('Is elected'),
        blank=True, null=True,
        help_text=_(
            'If the candidate has been elected with the result'
        )
    )

    url_name = 'electoral-result-detail'

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(
            ElectoralResultQuerySet
        )()
    except:
        objects = ElectoralResultQuerySet.as_manager()

    class Meta:
        verbose_name = _("Electoral result")
        verbose_name_plural = _("Electoral results")

    def __str__(self):
        return self.slug_source




@python_2_unicode_compatible
class OtherName(Dateframeable, GenericRelatable, models.Model):
    """
    An alternate or former name
    see schema at http://popoloproject.com/schemas/name-component.json#
    """
    name = models.CharField(
        _("name"),
        max_length=512,
        help_text=_("An alternate or former name")
    )

    NAME_TYPES = Choices(
        ('FOR', 'former', _('Former name')),
        ('ALT', 'alternate', _('Alternate name')),
        ('NIC', 'nickname', _('Nickname')),
        ('ACR', 'acronym', _('Acronym')),
    )
    othername_type = models.CharField(
        _("scheme"),
        max_length=3, default='ALT',
        choices=NAME_TYPES,
        help_text=_("Type of other name, e.g. F: former, A: alternate")
    )

    note = models.CharField(
        _("note"),
        max_length=1024, blank=True, null=True,
        help_text=_("An extended note, e.g. 'Birth name used before marrige'")
    )

    source = models.URLField(
        _("source"),
        max_length=256, blank=True, null=True,
        help_text=_("The URL of the source where this information comes from")
    )

    class Meta:
        verbose_name = _("Other name")
        verbose_name_plural = _("Other names")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(OtherNameQuerySet)()
    except:
        objects = OtherNameQuerySet.as_manager()

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Identifier(Dateframeable, GenericRelatable, models.Model):
    """
    An issued identifier
    see schema at http://popoloproject.com/schemas/identifier.json#
    """
    identifier = models.CharField(
        _("identifier"),
        max_length=512,
        help_text=_("An issued identifier, e.g. a DUNS number")
    )

    scheme = models.CharField(
        _("scheme"),
        max_length=128, blank=True,
        help_text=_("An identifier scheme, e.g. DUNS")
    )

    source = models.URLField(
        _("source"),
        max_length=256, blank=True, null=True,
        help_text=_("The URL of the source where this information comes from")
    )

    class Meta:
        verbose_name = _("Identifier")
        verbose_name_plural = _("Identifiers")

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4,
        # see issue #22
        objects = PassThroughManager.for_queryset_class(IdentifierQuerySet)()
    except:
        objects = IdentifierQuerySet.as_manager()

    def __str__(self):
        return "{0}: {1}".format(self.scheme, self.identifier)


@python_2_unicode_compatible
class LinkRel(
    GenericRelatable,
    models.Model
):
    """
    The relation between a generic object and a Source
    """
    link = models.ForeignKey(
        'Link',
        related_name='related_objects',
        help_text=_("A relation to a Link instance assigned to this object")
    )

    def __str__(self):
        return self.content_object, self.link

@python_2_unicode_compatible
class Link(models.Model):
    """
    A URL
    see schema at http://popoloproject.com/schemas/link.json#
    """
    url = models.URLField(
        _("url"),
        max_length=350,
        help_text=_("A URL")
    )

    note = models.CharField(
        _("note"),
        max_length=512, blank=True,
        help_text=_("A note, e.g. 'Wikipedia page'")
    )

    class Meta:
        verbose_name = _("Link")
        verbose_name_plural = _("Links")

    def __str__(self):
        return self.url


@python_2_unicode_compatible
class SourceRel(
    GenericRelatable,
    models.Model
):
    """
    The relation between a generic object and a Source
    """
    source = models.ForeignKey(
        'Source',
        related_name='related_objects',
        help_text=_("A Source instance assigned to this object")
    )

    def __str__(self):
        return self.content_object, self.source


@python_2_unicode_compatible
class Source(models.Model):
    """
    A URL for referring to sources of information
    see schema at http://popoloproject.com/schemas/link.json#
    """
    url = models.URLField(
        _("url"),
        max_length=350,
        help_text=_("A URL")
    )

    note = models.CharField(
        _("note"),
        max_length=512, blank=True,
        help_text=_("A note, e.g. 'Parliament website'")
    )

    class Meta:
        verbose_name = _("Source")
        verbose_name_plural = _("Sources")

    def __str__(self):
        return self.url


@python_2_unicode_compatible
class Event(Timestampable, SourceShortcutsMixin, models.Model):
    """An occurrence that people may attend

    """

    name = models.CharField(
        _("name"),
        max_length=128,
        help_text=_("The event's name")
    )

    description = models.CharField(
        _("description"),
        max_length=512, blank=True, null=True,
        help_text=_("The event's description")
    )

    # start_date and end_date are kept instead of the fields
    # provided by DateFrameable mixin,
    # starting and finishing *timestamps* for the Event are tracked
    # wjile fields in Dateframeable track the validity *dates* of the data
    start_date = models.CharField(
        _("start date"),
        max_length=20, blank=True, null=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{4}('
                    '(-[0-9]{2}){0,2}|(-[0-9]{2}){2}'
                        'T[0-9]{2}(:[0-9]{2}){0,2}'
                        '(Z|[+-][0-9]{2}(:[0-9]{2})?'
                    ')'
                ')$',
                message='start date must follow the given pattern: '
                    '^[0-9]{4}('
                        '(-[0-9]{2}){0,2}|(-[0-9]{2}){2}'
                        'T[0-9]{2}(:[0-9]{2}){0,2}'
                        '(Z|[+-][0-9]{2}(:[0-9]{2})?'
                    ')'
                ')$',
                code='invalid_start_date'
            )
        ],
        help_text=_("The time at which the event starts")
    )
    end_date = models.CharField(
        _("end date"),
        max_length=20, blank=True, null=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{4}('
                    '(-[0-9]{2}){0,2}|(-[0-9]{2}){2}'
                        'T[0-9]{2}(:[0-9]{2}){0,2}'
                        '(Z|[+-][0-9]{2}(:[0-9]{2})?'
                    ')'
                ')$',
                message='end date must follow the given pattern: '
                    '^[0-9]{4}('
                        '(-[0-9]{2}){0,2}|(-[0-9]{2}){2}'
                        'T[0-9]{2}(:[0-9]{2}){0,2}'
                        '(Z|[+-][0-9]{2}(:[0-9]{2})?'
                    ')'
                ')$',
                code='invalid_end_date'
            )
        ],
        help_text=_("The time at which the event ends")
    )

    # textual full address of the event
    location = models.CharField(
        _("location"),
        max_length=255, blank=True, null=True,
        help_text=_("The event's location")
    )
    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        'Area',
        blank=True, null=True,
        related_name='events',
        help_text=_("The Area the Event is related to")
    )

    status = models.CharField(
        _("status"),
        max_length=128, blank=True, null=True,
        help_text=_("The event's status")
    )

    # add 'identifiers' property to get array of items referencing 'http://www.popoloproject.com/schemas/identifier.json#'
    identifiers = GenericRelation(
        'Identifier',
        blank=True, null=True,
        help_text=_("Issued identifiers for this event")
    )

    classification = models.CharField(
        _("classification"),
        max_length=128, blank=True, null=True,
        help_text=_("The event's category")
    )

    # reference to 'http://www.popoloproject.com/schemas/organization.json#'
    organization = models.ForeignKey(
        'Organization',
        blank=True, null=True,
        related_name='events',
        help_text=_("The organization organizing the event")
    )

    # array of items referencing 'http://www.popoloproject.com/schemas/person.json#'
    attendees = models.ManyToManyField(
        'Person',
        blank=True,
        related_name='attended_events',
        help_text=_("People attending the event")
    )

    # reference to 'http://www.popoloproject.com/schemas/event.json#'
    parent = models.ForeignKey(
        'Event',
        blank=True, null=True,
        related_name='children',
        verbose_name=_('Parent'),
        help_text=_("The Event that this event is part of")
    )

    # array of items referencing
    # 'http://www.popoloproject.com/schemas/source.json#'
    sources = GenericRelation(
        'SourceRel',
        help_text=_("URLs to source documents about the event")
    )

    def __str__(self):
        return "{0} - {1}".format(self.name, self.start_date)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        unique_together = ('name', 'start_date',)


#
# signals
#

# copy founding and dissolution dates into start and end dates,
# so that Organization can extend the abstract Dateframeable behavior
# (it's way easier than dynamic field names)
@receiver(pre_save, sender=Organization)
def copy_organization_date_fields(sender, **kwargs):
    obj = kwargs['instance']

    if obj.founding_date:
        obj.start_date = obj.founding_date
    if obj.dissolution_date:
        obj.end_date = obj.dissolution_date


# copy birth and death dates into start and end dates,
# so that Person can extend the abstract Dateframeable behavior
# (it's way easier than dynamic field names)
@receiver(pre_save, sender=Person)
def copy_person_date_fields(sender, **kwargs):
    obj = kwargs['instance']

    if obj.birth_date:
        obj.start_date = obj.birth_date
    if obj.death_date:
        obj.end_date = obj.death_date


# all Dateframeable instances need to have dates properly sorted
@receiver(pre_save)
def verify_start_end_dates_order(sender, **kwargs):
    if not issubclass(sender, Dateframeable):
        return
    obj = kwargs['instance']
    if obj.start_date and obj.end_date and obj.start_date > obj.end_date:
        raise Exception(_(
            "Initial date must precede end date"
        ))


@receiver(pre_save, sender=Membership)
def verify_membership_has_org_and_member(sender, **kwargs):
    obj = kwargs['instance']
    if obj.person is None and obj.member_organization is None:
        raise Exception(_(
            "A member, either a Person or an Organization, must be specified."
        ))
    if obj.organization is None:
        raise Exception(_(
            "An Organization, must be specified."
        ))


@receiver(pre_save, sender=Ownership)
def verify_ownership_has_org_and_owner(sender, **kwargs):
    obj = kwargs['instance']
    if obj.owner_person is None and obj.owner_organization is None:
        raise Exception(_(
            "An owner, either a Person or an Organization, must be specified."
        ))

# all main instances are validated before being saved
@receiver(pre_save, sender=Person)
@receiver(pre_save, sender=Organization)
@receiver(pre_save, sender=Post)
@receiver(pre_save, sender=Membership)
@receiver(pre_save, sender=Ownership)
@receiver(pre_save, sender=ElectoralEvent)
@receiver(pre_save, sender=ElectoralResult)
@receiver(pre_save, sender=Area)
def validate_fields(sender, **kwargs):
    obj = kwargs['instance']
    obj.full_clean()


