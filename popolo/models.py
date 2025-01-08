from datetime import datetime
from typing import Union, List, Iterable

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.db.models import Q, Index, F
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from popolo.behaviors.models import Permalinkable, Timestampable, Dateframeable, GenericRelatable
from popolo.managers import HistoricAreaManager
from popolo.mixins import (
    ContactDetailsShortcutsMixin,
    OtherNamesShortcutsMixin,
    IdentifierShortcutsMixin,
    LinkShortcutsMixin,
    SourceShortcutsMixin,
    ClassificationShortcutsMixin,
    OwnerShortcutsMixin,
)
from popolo.querysets import (
    PostQuerySet,
    OtherNameQuerySet,
    ContactDetailQuerySet,
    MembershipQuerySet,
    OwnershipQuerySet,
    OrganizationQuerySet,
    PersonQuerySet,
    PersonalRelationshipQuerySet,
    KeyEventQuerySet,
    AreaQuerySet,
    IdentifierQuerySet,
    AreaRelationshipQuerySet,
    ClassificationQuerySet,
    OrganizationRelationshipQuerySet,
)
from popolo.utils import PartialDatesInterval, PartialDate
from popolo.validators import validate_percentage


class Person(
    ContactDetailsShortcutsMixin,
    OtherNamesShortcutsMixin,
    IdentifierShortcutsMixin,
    ClassificationShortcutsMixin,
    LinkShortcutsMixin,
    SourceShortcutsMixin,
    OwnerShortcutsMixin,
    Dateframeable,
    Timestampable,
    Permalinkable,
    models.Model,
):
    """
    A real person, alive or dead.

    e.g. William Shakespeare

    JSON schema: http://popoloproject.com/schemas/person.json
    """

    MULTIPLE_CLASSIFICATIONS_SCHEMES = ['OPDM_PERSON_LABEL']

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")

    json_ld_context = "http://popoloproject.com/contexts/person.jsonld"

    json_ld_type = "http://www.w3.org/ns/person#Person"

    url_name = "person-detail"

    objects = PersonQuerySet.as_manager()

    name = models.CharField(
        verbose_name=_("name"),
        max_length=512,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("A person's preferred full name"),
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(to="OtherName", help_text=_("Alternate or former names"))

    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(to="Identifier", help_text=_("Issued identifiers"))

    classifications = GenericRelation(
        to="ClassificationRel", help_text=_("ATECO, Legal Form, OPDM labels and all other available classifications")
    )

    family_name = models.CharField(
        verbose_name=_("family name"),
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("One or more family names"),
    )

    given_name = models.CharField(
        verbose_name=_("given name"),
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("One or more primary given names"),
    )

    additional_name = models.CharField(
        verbose_name=_("additional name"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("One or more secondary given names"),
    )

    honorific_prefix = models.CharField(
        verbose_name=_("honorific prefix"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("One or more honorifics preceding a person's name"),
    )

    honorific_suffix = models.CharField(
        verbose_name=_("honorific suffix"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("One or more honorifics following a person's name"),
    )

    patronymic_name = models.CharField(
        verbose_name=_("patronymic name"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("One or more patronymic names"),
    )

    sort_name = models.CharField(
        verbose_name=_("sort name"),
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("A name to use in an lexicographically " "ordered list"),
    )

    email = models.EmailField(
        verbose_name=_("email"), blank=True, null=True, help_text=_("A preferred email address")
    )

    gender = models.CharField(
        verbose_name=_("gender"), max_length=32, blank=True, null=True, db_index=True, help_text=_("A gender")
    )

    birth_date = models.CharField(
        verbose_name=_("birth date"),
        max_length=10,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("A date of birth"),
    )

    birth_location = models.CharField(
        verbose_name=_("birth location"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("Birth location as a string"),
    )

    birth_location_area = models.ForeignKey(
        to="Area",
        blank=True,
        null=True,
        related_name="persons_born_here",
        verbose_name=_("birth location Area"),
        help_text=_("The geographic area corresponding " "to the birth location"),
        on_delete=models.CASCADE,
    )

    death_date = models.CharField(
        verbose_name=_("death date"),
        max_length=10,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("A date of death"),
    )

    is_identity_verified = models.BooleanField(
        verbose_name=_("identity verified"), default=False, help_text=_("If tax_id was verified formally")
    )

    image = models.URLField(verbose_name=_("image"), blank=True, null=True, help_text=_("A URL of a head shot"))

    summary = models.CharField(
        verbose_name=_("summary"),
        max_length=1024,
        blank=True,
        null=True,
        help_text=_("A one-line account of a person's life"),
    )

    biography = models.TextField(
        verbose_name=_("biography"), blank=True, null=True, help_text=_("An extended account of a person's life")
    )

    national_identity = models.CharField(
        verbose_name=_("national identity"), max_length=128, blank=True, null=True, help_text=_("A national identity")
    )

    original_profession = models.ForeignKey(
        to="OriginalProfession",
        blank=True,
        null=True,
        related_name="persons_with_this_original_profession",
        verbose_name=_("Non normalized profession"),
        help_text=_("The profession of this person, non normalized"),
        on_delete=models.CASCADE,
    )

    profession = models.ForeignKey(
        to="Profession",
        blank=True,
        null=True,
        related_name="persons_with_this_profession",
        verbose_name=_("Normalized profession"),
        help_text=_("The profession of this person"),
        on_delete=models.CASCADE,
    )

    original_education_level = models.ForeignKey(
        to="OriginalEducationLevel",
        blank=True,
        null=True,
        related_name="persons_with_this_original_education_level",
        verbose_name=_("Non normalized education level"),
        help_text=_("The education level of this person, non normalized"),
        on_delete=models.CASCADE,
    )

    education_level = models.ForeignKey(
        to="EducationLevel",
        blank=True,
        null=True,
        related_name="persons_with_this_education_level",
        verbose_name=_("Normalized education level"),
        help_text=_("The education level of this person"),
        on_delete=models.CASCADE,
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(to="ContactDetail", help_text="Means of contacting the person")

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(to="LinkRel", help_text="URLs to documents related to the person")

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text="URLs to source documents about the person")

    related_persons = models.ManyToManyField(
        to="self", through="PersonalRelationship", through_fields=("source_person", "dest_person"), symmetrical=False
    )

    @property
    def slug_source(self):
        return f"{self.name} {self.birth_date}"

    def add_membership(self, organization, **kwargs):
        """Add person's membership to an Organization

        Multiple memberships to the same organization can be added
        only if direct (no post) and if dates are not overlapping.

        This only add main values, not links, sources, contacts, that need to be added after

        :param organization: Organization instance
        :param kwargs: membership parameters
        :return: Membership, if just created
        """

        # new  dates interval as PartialDatesInterval instance
        new_int = PartialDatesInterval(start=kwargs.get("start_date", None), end=kwargs.get("end_date", None))

        is_overlapping = False

        allow_overlap = kwargs.pop("allow_overlap", False)

        # loop over memberships to the same org
        same_org_memberships = self.memberships.filter(organization=organization, post__isnull=True)
        for i in same_org_memberships:

            # existing identifier interval as PartialDatesInterval instance
            i_int = PartialDatesInterval(start=i.start_date, end=i.end_date)

            # compute overlap days
            #  > 0 means crossing
            # == 0 means touching (considered non overlapping)
            #  < 0 meand not overlapping
            overlap = PartialDate.intervals_overlap(new_int, i_int)

            if overlap > 0:
                is_overlapping = True

        if not is_overlapping or allow_overlap:
            m = self.memberships.create(organization=organization, **kwargs)
            return m

    def add_memberships(self, memberships):
        """Add multiple *blank* memberships to person.

        :param memberships: list of Membership dicts
        :return: None
        """
        for m in memberships:
            self.add_membership(**m)

    def add_role(self, post, **kwargs):
        """add person's role (membership through post) in an Organization

        A *role* is identified by the Membership to a given Post in an
        Organization.

        If the organization is specified in the kwargs parameters, then
        the Post needs to be a *generic* one (not linked to a specific
        organization).

        If no organization is specified in kwargs, then the Post needs
        to be linked to a specific organization.

        Multiple roles to the same post and organization can only be added
        if dates are not overlapping

        :param post: the post fullfilled
        :return: the Membership to rhe role
        """

        # read special kwarg that indicates whether to check label or not
        check_label = kwargs.pop("check_label", False)

        if "organization" not in kwargs:
            if post.organization is None:
                raise Exception("Post needs to be specific, " "i.e. linked to an organization")
            org = post.organization
        else:
            if post.organization is not None:
                raise Exception("Post needs to be generic, " "i.e. not linked to an organization")
            org = kwargs.pop("organization")

        # new  dates interval as PartialDatesInterval instance
        new_int = PartialDatesInterval(start=kwargs.get("start_date", None), end=kwargs.get("end_date", None))

        is_overlapping = False

        allow_overlap = kwargs.pop("allow_overlap", False)

        # loop over memberships to the same org and post
        # consider labels, too, if not None, and if specified with the check_label arg
        # for role as Ministro, Assessore, Sottosegretario
        label = kwargs.get("label", None)
        if label and check_label:
            same_org_post_memberships = self.memberships.filter(organization=org, post=post, label=label)
        else:
            same_org_post_memberships = self.memberships.filter(organization=org, post=post)

        for i in same_org_post_memberships.order_by('end_date'):

            # existing identifier interval as PartialDatesInterval instance
            i_int = PartialDatesInterval(start=i.start_date, end=i.end_date)

            # compute overlap days
            #  > 30 means crossing (less than that it's
            #  between 30 and 0 means touching (end date =~ start date)
            #  < 0 means not touching
            # dates only overlap if crossing
            # the touching case
            overlap = PartialDate.intervals_overlap(new_int, i_int)
            stop_and_go_days = kwargs.get('stop_and_go_days', getattr(settings, 'STOP_AND_GO_DAYS', 30))

            if overlap > 0:
                if overlap > stop_and_go_days or kwargs['start_date'] <= i.start_date:
                    is_overlapping = True
                    continue

        if not is_overlapping or allow_overlap:
            m = self.memberships.create(post=post, organization=org, **kwargs)

            return m

    def add_roles(self, roles):
        """
        Add multiple roles to person.

        :param roles: list of Role dicts
        """
        for r in roles:
            self.add_role(**r)

    def add_role_on_behalf_of(self, post, behalf_organization, **kwargs):
        """add a role (post) in an Organization on behhalf of the given
        Organization

        :param post: the post fullfilled
        :param behalf_organization: the organization on behalf of which the Post is fulfilled
        :return: the Membership to rhe role
        """
        return self.add_role(post, on_behalf_of=behalf_organization, **kwargs)

    def add_relationship(self, dest_person, **kwargs):
        """Add a personal relationship to dest_person with parameters kwargs

        :param dest_person:
        :param kwargs:
        :return:
        """
        r = PersonalRelationship(source_person=self, dest_person=dest_person, **kwargs)
        r.save()
        return r

    def organizations_has_role_in(self):
        """
        Get all organizations the person has a role in

        :return:
        """
        return Organization.objects.filter(posts__in=Post.objects.filter(memberships__person=self))

    @property
    def tax_id(self):
        try:
            tax_id = self.identifiers.get(scheme="CF").identifier
        except Identifier.DoesNotExist:
            tax_id = None
        return tax_id

    def __str__(self) -> str:
        return f"{self.name}"


class PersonalRelationship(SourceShortcutsMixin, Dateframeable, Timestampable, models.Model):
    """
    A relationship between two persons.

    Must be defined by a classification (type, ex: friendship, family, ...).

    Off-spec model.
    """

    class Meta:
        verbose_name = _("Personal relationship")
        verbose_name_plural = _("Personal relationships")
        unique_together = ("source_person", "dest_person", "classification")

    objects = PersonalRelationshipQuerySet.as_manager()

    source_person = models.ForeignKey(
        to="Person",
        related_name="to_relationships",
        verbose_name=_("Source person"),
        help_text=_("The Person the relation starts from"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/person.json#"
    dest_person = models.ForeignKey(
        to="Person",
        related_name="from_relationships",
        verbose_name=_("Destination person"),
        help_text=_("The Person the relationship ends to"),
        on_delete=models.CASCADE,
    )

    WEIGHTS = Choices(
        (-1, "strongly_negative", _("Strongly negative")),
        (-2, "negative", _("Negative")),
        (0, "neutral", _("Neutral")),
        (1, "positive", _("Positive")),
        (2, "strongly_positive", _("Strongly positive")),
    )
    weight = models.IntegerField(
        _("weight"),
        default=0,
        choices=WEIGHTS,
        help_text=_("The relationship weight, " "from strongly negative, to strongly positive"),
    )

    classification = models.ForeignKey(
        to="Classification",
        related_name="personal_relationships",
        limit_choices_to={"scheme": "OP_TIPO_RELAZIONE_PERS"},
        help_text=_("The classification for this personal relationship"),
        on_delete=models.CASCADE,
    )

    descr = models.CharField(
        blank=True,
        null=True,
        max_length=512,
        verbose_name=_("Description"),
        help_text=_("Some details on the relationship (not much, though)"),
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the relationship"))

    def __str__(self) -> str:
        return "({0}) -[{1} ({2}, {3})]-> ({4})".format(
            self.source_person.name, self.classification, self.descr, self.get_weight_display(), self.dest_person.name
        )


class Organization(
    ContactDetailsShortcutsMixin,
    OtherNamesShortcutsMixin,
    IdentifierShortcutsMixin,
    ClassificationShortcutsMixin,
    LinkShortcutsMixin,
    SourceShortcutsMixin,
    OwnerShortcutsMixin,
    Dateframeable,
    Timestampable,
    Permalinkable,
    models.Model,
):
    """
    A collection of people with a common purpose or reason for existence that
    goes beyond the set of people belonging to it.

    e.g. a social, commercial or political structure.

    JSON schema: http://popoloproject.com/schemas/organization.json
    """

    MULTIPLE_CLASSIFICATIONS_SCHEMES = ['OPDM_TOPIC_TAG', 'OPDM_ORGANIZATION_LABEL', 'CONTESTO_OP']

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        unique_together = ("name", "identifier", "start_date")

    url_name = "organization-detail"

    objects = OrganizationQuerySet.as_manager()

    @property
    def slug_source(self):
        return "{0} {1} {2}".format(self.name, self.identifier, self.start_date)

    name = models.CharField(
        verbose_name=_("name"), max_length=512, help_text=_("A primary name, e.g. a legally recognized name")
    )

    identifier = models.CharField(
        verbose_name=_("identifier"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("The main issued identifier, or fiscal code, for organization"),
    )

    classification = models.CharField(
        verbose_name=_("classification"),
        max_length=256,
        blank=True,
        null=True,
        help_text=_("The nature of the organization, legal form in many cases"),
    )

    thematic_classification = models.CharField(
        verbose_name=_("thematic classification"),
        max_length=256,
        blank=True,
        null=True,
        help_text=_("What the organization does, in what fields, ..."),
    )

    classifications = GenericRelation(
        to="ClassificationRel", help_text=_("ATECO, Legal Form and all other available classifications")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(to="OtherName", help_text=_("Alternate or former names"))

    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(to="Identifier", help_text=_("Issued identifiers"))

    # reference to "http://popoloproject.com/schemas/organization.json#"
    parent = models.ForeignKey(
        to="Organization",
        blank=True,
        null=True,
        related_name="children",
        verbose_name=_("Parent"),
        help_text=_("The organization that contains this " "organization"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        to="Area",
        blank=True,
        null=True,
        related_name="organizations",
        help_text=_("The geographic area to which this organization is related"),
        on_delete=models.CASCADE,
    )

    abstract = models.CharField(
        verbose_name=_("abstract"),
        max_length=256,
        blank=True,
        null=True,
        help_text=_("A one-line description of an organization"),
    )

    description = models.TextField(
        verbose_name=_("biography"), blank=True, null=True, help_text=_("An extended description of an organization")
    )

    founding_date = models.CharField(
        verbose_name=_("founding date"),
        max_length=10,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{4}(-[0-9]{2}){0,2}$",
                message="founding date must follow the given pattern: ^[0-9]{" "4}(-[0-9]{2}){0,2}$",
                code="invalid_founding_date",
            )
        ],
        help_text=_("A date of founding"),
    )

    dissolution_date = models.CharField(
        verbose_name=_("dissolution date"),
        max_length=10,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{4}(-[0-9]{2}){0,2}$",
                message="dissolution date must follow the given pattern: ^[" "0-9]{4}(-[0-9]{2}){0,2}$",
                code="invalid_dissolution_date",
            )
        ],
        help_text=_("A date of dissolution"),
    )

    image = models.URLField(
        verbose_name=_("image"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("A URL of an image, to identify the organization visually"),
    )

    new_orgs = models.ManyToManyField(
        to="Organization",
        blank=True,
        related_name="old_orgs",
        symmetrical=False,
        help_text=_(
            "Link to organization(s) after dissolution_date, " "needed to track mergers, acquisition, splits."
        ),
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(to="ContactDetail", help_text=_("Means of contacting the organization"))

    # array of references to KeyEvent instances related to this Organization
    key_events = GenericRelation(to="KeyEventRel", help_text=_("KeyEvents related to this organization"))

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(to="LinkRel", help_text=_("URLs to documents about the organization"))

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the organization"))

    person_members = models.ManyToManyField(
        to="Person",
        through="Membership",
        through_fields=("organization", "person"),
        related_name="organizations_memberships",
    )

    organization_members = models.ManyToManyField(
        to="Organization",
        through="Membership",
        through_fields=("organization", "member_organization"),
        related_name="organizations_memberships",
    )

    person_owners = models.ManyToManyField(
        to="Person",
        through="Ownership",
        through_fields=("owned_organization", "owner_person"),
        related_name="organizations_ownerships",
    )

    organization_owners = models.ManyToManyField(
        to="Organization",
        through="Ownership",
        through_fields=("owned_organization", "owner_organization"),
        related_name="organization_ownerships",
    )

    @property
    def members(self):
        """Returns list of members (it's not a queryset)

        :return: list of Person or Organization instances
        """
        return list(self.person_members.all()) + list(self.organization_members.all())

    @property
    def owners(self) -> List[Union["Person", "Organization"]]:
        """
        Returns list of owners (it's not a queryset)

        :return: list of Person or Organization instances
        """
        return list(self.person_owners.all()) + list(self.organization_owners.all())

    def add_member(self, member: Union["Person", "Organization"], **kwargs):
        """
        Add a member to this organization

        :param member: a Person or an Organization
        :param kwargs: membership parameters
        :return: the added member (be it Person or Organization)
        """
        if isinstance(member, Person) or isinstance(member, Organization):
            m = member.add_membership(self, **kwargs)
        else:
            raise Exception(_("Member must be Person or Organization"))
        return m

    def add_members(self, members: Iterable[Union["Person", "Organization"]]):
        """
        Add multiple *blank* members to this organization

        :param members: list of Person/Organization to be added as members
        :return:
        """
        for m in members:
            self.add_member(m)

    def add_membership(self, organization: "Organization", allow_overlap: bool = False, **kwargs) -> "Membership":
        """
        Add this organization (self) as member of the given `organization`

        Multiple memberships to the same organization can be added
        only when dates are not overlapping, or if overlap is explicitly allowed
        through the `allow_overlap` parameter.

        :param organization: the organization this one will be a member of
        :param allow_overlap:
        :param kwargs: membership parameters
        :return: the added Membership
        """

        # new  dates interval as PartialDatesInterval instance
        new_int = PartialDatesInterval(start=kwargs.get("start_date", None), end=kwargs.get("end_date", None))

        is_overlapping = False

        # loop over memberships to the same org
        same_org_memberships = self.memberships_as_member.filter(organization=organization)
        for i in same_org_memberships:

            # existing identifier interval as PartialDatesInterval instance
            i_int = PartialDatesInterval(start=i.start_date, end=i.end_date)

            # compute overlap days
            #  > 0 means crossing
            # == 0 means touching (considered non overlapping)
            #  < 0 meand not overlapping
            overlap = PartialDate.intervals_overlap(new_int, i_int)

            if overlap > 0:
                is_overlapping = True

        if not is_overlapping or allow_overlap:
            o = self.memberships_as_member.create(organization=organization, **kwargs)
            return o

    def add_owner(self, owner: Union["Person", "Organization"], **kwargs):
        """
        Add a owner to this organization

        :param owner: a Person or an Organization
        :param kwargs: ownership parameters
        :return: the added owner (be it Person or Organization)
        """
        if isinstance(owner, Person) or isinstance(owner, Organization):
            o = owner.add_ownership(self, **kwargs)
        else:
            # TODO: raising an exception is probably not a good idea...
            raise Exception(_("Owner must be Person or Organization"))
        return o

    def add_post(self, **kwargs):
        """
        Add post, specified with kwargs to this organization

        :param kwargs: Post parameters
        :return: the added Post
        """
        p = Post(organization=self, **kwargs)
        p.save()
        return p

    def add_posts(self, posts: Iterable):
        for p in posts:
            self.add_post(**p)

    def merge_from(self, *args, **kwargs):
        """Merge a list of organizations into this one, creating relationships of new/old organizations.

        :param args: elements to merge into
        :param kwargs: may contain the moment key
        """
        moment = kwargs.get("moment", datetime.strftime(datetime.now(), "%Y-%m-%d"))

        for i in args:
            i.close(moment=moment, reason=_("Merged into other organizations"))
            i.new_orgs.add(self)
        self.start_date = moment
        self.save()

    def split_into(self, *args, **kwargs):
        """
        Split this organization into a list of other organizations, creating relationships of new/old organizations.

        :param args: elements to be split into
        :param kwargs: keyword args that may contain moment
        """
        moment = kwargs.get("moment", datetime.strftime(datetime.now(), "%Y-%m-%d"))

        for i in args:
            i.start_date = moment
            i.save()
            self.new_orgs.add(i)
        self.close(moment=moment, reason=_("Split into other organiations"))

    def add_key_event_rel(self, key_event: Union[int, "KeyEvent"]) -> "KeyEventRel":
        """
        Add key_event (rel) to the organization.

        :param key_event: existing KeyEvent instance or id
        :return: the KeyEventRel instance just added
        """
        # then add the KeyEventRel to classifications
        if not isinstance(key_event, int) and not isinstance(key_event, KeyEvent):
            raise Exception("key_event needs to be an integer ID or a KeyEvent instance")
        if isinstance(key_event, int):
            ke, created = self.key_events.get_or_create(key_event_id=key_event)
        else:
            ke, created = self.key_events.get_or_create(key_event=key_event)

        # and finally return the KeyEvent just added
        return ke

    def add_key_events(self, new_key_events):
        """
        Add multiple key_events.

        :param new_key_events: KeyEvent ids to be added
        :return:
        """
        # add objects
        for new_key_event in new_key_events:
            if "key_event" in new_key_event:
                self.add_key_event_rel(**new_key_event)
            else:
                # TODO: raising an exception is probably not a good idea...
                raise Exception("key_event need to be present in dict")

    def update_key_events(self, new_items):
        """update key_events,
        removing those not present in new_items
        overwriting those present and existing,
        adding those present and not existing

        :param new_items: the new list of key_events
        :return:
        """
        existing_ids = set(self.key_events.values_list("key_event", flat=True))
        new_ids = set(n.get("key_event", None) for n in new_items)

        # remove objects
        delete_ids = existing_ids - set(new_ids)
        self.key_events.filter(key_event__in=delete_ids).delete()

        # update objects
        self.add_key_events([{"key_event": ke_id} for ke_id in new_ids])

    def __str__(self) -> str:
        return f"{self.name}"


class OrganizationRelationship(SourceShortcutsMixin, Dateframeable, Timestampable, models.Model):
    """
    A generic, graph, relationship between two organizations.

    Must be defined by a classification (type, ex: control, collaboration, ...)

    Off-spec model.
    """

    class Meta:
        verbose_name = _("Organization relationship")
        verbose_name_plural = _("Organization relationships")
        unique_together = ("source_organization", "dest_organization", "classification")

    objects = OrganizationRelationshipQuerySet.as_manager()

    # reference to "http://popoloproject.com/schemas/organization.json#"
    source_organization = models.ForeignKey(
        to="Organization",
        related_name="to_relationships",
        verbose_name=_("Source organization"),
        help_text=_("The Organization the relation starts from"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    dest_organization = models.ForeignKey(
        to="Organization",
        related_name="from_relationships",
        verbose_name=_("Destination organization"),
        help_text=_("The Organization the relationship ends to"),
        on_delete=models.CASCADE,
    )

    WEIGHTS = Choices(
        (-1, "strongly_negative", _("Strongly negative")),
        (-2, "negative", _("Negative")),
        (0, "neutral", _("Neutral")),
        (1, "positive", _("Positive")),
        (2, "strongly_positive", _("Strongly positive")),
    )
    weight = models.IntegerField(
        _("weight"),
        default=0,
        choices=WEIGHTS,
        help_text=_("The relationship weight, from strongly negative, to strongly positive"),
    )

    classification = models.ForeignKey(
        to="Classification",
        related_name="organization_relationships",
        limit_choices_to={"scheme": "OP_TIPO_RELAZIONE_ORG"},
        help_text=_("The classification for this organization relationship"),
        on_delete=models.CASCADE,
    )

    descr = models.CharField(
        blank=True,
        null=True,
        max_length=512,
        verbose_name=_("Description"),
        help_text=_("Some details on the relationship (not much, though)"),
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the relationship"))

    def __str__(self) -> str:
        return "({0}) -[{1} ({2})]-> ({3})".format(
            self.source_organization.name, self.classification, self.get_weight_display(), self.dest_organization.name
        )


class ClassificationRel(GenericRelatable, Dateframeable, models.Model):
    """
    The relation between a generic object and a Classification
    """

    classification = models.ForeignKey(
        to="Classification",
        related_name="related_objects",
        help_text=_("A Classification instance assigned to this object"),
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.content_object} - {self.classification}"


class Classification(SourceShortcutsMixin, Dateframeable, models.Model):
    """
    A generic, hierarchical classification usable in different contexts
    """

    class Meta:
        verbose_name = _("Classification")
        verbose_name_plural = _("Classifications")
        unique_together = ("scheme", "code", "descr")

    objects = ClassificationQuerySet.as_manager()

    scheme = models.CharField(
        verbose_name=_("scheme"),
        max_length=128,
        blank=True,
        help_text=_("A classification scheme, e.g. ATECO, or FORMA_GIURIDICA"),
    )

    code = models.CharField(
        verbose_name=_("code"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("An alphanumerical code in use within the scheme"),
    )

    descr = models.CharField(
        verbose_name=_("description"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("The extended, textual description of the classification"),
    )

    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the classification"))

    # reference to "http://popoloproject.com/schemas/area.json#"
    parent = models.ForeignKey(
        to="Classification",
        blank=True,
        null=True,
        related_name="children",
        help_text=_("The parent classification."),
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        if self.code:
            return "{0}: {1} - {2}".format(self.scheme, self.code, self.descr)
        else:
            return "{0}: {1}".format(self.scheme, self.descr)


class RoleType(models.Model):
    """
    A role type (Sindaco, Assessore, CEO), with priority, used to
    build a sorted drop-down in interfaces.

    Each role type is related to a given organization's
    OP_FORMA_GIURIDICA classification.
    """

    class Meta:
        verbose_name = _("Role type")
        verbose_name_plural = _("Role types")
        unique_together = ("classification", "label")

    label = models.CharField(
        verbose_name=_("label"),
        max_length=512,
        help_text=_("A label describing the post, better keep it unique and put the classification descr into it"),
        unique=True,
    )

    classification = models.ForeignKey(
        to="Classification",
        related_name="role_types",
        limit_choices_to={"scheme": "FORMA_GIURIDICA_OP"},
        help_text=_("The OP_FORMA_GIURIDICA classification this role type is related to"),
        on_delete=models.CASCADE,
    )

    other_label = models.CharField(
        verbose_name=_("other label"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("An alternate label, such as an abbreviation"),
    )

    is_appointer = models.BooleanField(
        verbose_name=_("is appointer"),
        default=False,
        help_text=_("Whether this is a role able to appoint other roles"),
    )

    is_appointable = models.BooleanField(
        verbose_name=_("is appointable"),
        default=False,
        help_text=_("Whether this is role can be appointed (by appointers)"),
    )

    priority = models.IntegerField(
        verbose_name=_("priority"),
        blank=True,
        null=True,
        help_text=_("The priority of this role type, within the same classification group"),
    )

    def __str__(self) -> str:
        return f"{self.label}"


class Post(
    ContactDetailsShortcutsMixin,
    LinkShortcutsMixin,
    SourceShortcutsMixin,
    Dateframeable,
    Timestampable,
    Permalinkable,
    models.Model,
):
    """
    A position that exists independent of the person holding it
    JSON schema: https://www.popoloproject.com/schemas/post.json
    """

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    url_name = "post-detail"

    objects = PostQuerySet.as_manager()

    label = models.CharField(_("label"), max_length=512, blank=True, help_text=_("A label describing the post"))

    other_label = models.CharField(
        verbose_name=_("other label"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("An alternate label, such as an abbreviation"),
    )

    role = models.CharField(
        verbose_name=_("role"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("The function that the holder of the post fulfills"),
    )

    role_type = models.ForeignKey(
        to="RoleType",
        related_name="posts",
        blank=True,
        null=True,
        verbose_name=_("Role type"),
        help_text=_("The structured role type for this post"),
        on_delete=models.CASCADE,
    )

    priority = models.FloatField(
        verbose_name=_("priority"),
        blank=True,
        null=True,
        help_text=_("The absolute priority of this specific post, with respect to all others."),
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey(
        to="Organization",
        related_name="posts",
        blank=True,
        null=True,
        verbose_name=_("Organization"),
        help_text=_("The organization in which the post is held"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        to="Area",
        blank=True,
        null=True,
        related_name="posts",
        verbose_name=_("Area"),
        help_text=_("The geographic area to which the post is related"),
        on_delete=models.CASCADE,
    )

    appointed_by = models.ForeignKey(
        to="Post",
        blank=True,
        null=True,
        related_name="appointees",
        verbose_name=_("Appointed by"),
        help_text=_(
            "The Post that officially appoints members to this one "
            "(appointment rule), ex: Secr. of Defence is appointed by POTUS"
        ),
        on_delete=models.CASCADE,
    )

    appointment_note = models.TextField(
        verbose_name=_("appointment note"),
        blank=True,
        null=True,
        help_text=_("A textual note for this appointment rule, if needed"),
    )

    is_appointment_locked = models.BooleanField(
        default=False,
        help_text=_(
            "A flag that shows if this appointment rule is locked (set to true when manually creating the rule)"
        ),
    )

    holders = models.ManyToManyField(
        to="Person", through="Membership", through_fields=("post", "person"), related_name="roles_held"
    )

    organizations = models.ManyToManyField(
        to="Organization",
        through="Membership",
        through_fields=("post", "organization"),
        related_name="posts_available",
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(to="ContactDetail", help_text=_("Means of contacting the holder of the post"))

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(to="LinkRel", help_text=_("URLs to documents about the post"))

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the post"))

    @property
    def slug_source(self):
        return self.label

    def add_person(self, person, **kwargs):
        """add given person to this post (through membership)
        A person having a post is also an explicit member
        of the organization holding the post.

        :param person: person to add
        :param kwargs: membership parameters (label, dates, ...)
        :return:
        """
        m = Membership(post=self, person=person, organization=self.organization, **kwargs)
        m.save()

    def add_person_on_behalf_of(self, person, organization, **kwargs):
        """add given `person` to this post (through a membership)
        on behalf of given `organization`

        :param person:
        :param organization: the organization on behalf the post is taken
        :param kwargs: membership parameters (label, dates, ...)
        :return:
        """
        m = Membership(post=self, person=person, organization=self.organization, on_behalf_of=organization, **kwargs)
        m.save()

    def add_appointer(self, role):
        """add role that appoints members to this one

        :param role: The apponinter
        :return: the appointee
        """
        self.appointed_by = role
        self.save()
        return self

    def __str__(self) -> str:
        return self.label


class Membership(
    ContactDetailsShortcutsMixin,
    LinkShortcutsMixin,
    SourceShortcutsMixin,
    ClassificationShortcutsMixin,
    Dateframeable,
    Timestampable,
    Permalinkable,
    models.Model,
):
    """
    A relationship between a person and an organization.

    JSON schema: http://popoloproject.com/schemas/membership.json
    """

    MULTIPLE_CLASSIFICATIONS_SCHEMES = ['OPDM_TOPIC_TAG', ]

    class Meta:
        verbose_name = _("Membership")
        verbose_name_plural = _("Memberships")

    url_name = "membership-detail"

    objects = MembershipQuerySet.as_manager()

    label = models.CharField(
        verbose_name=_("label"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("A label describing the membership"),
    )

    role = models.CharField(
        verbose_name=_("role"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("The role that the member fulfills in the organization"),
    )

    # organization that is a member of the organization
    member_organization = models.ForeignKey(
        to="Organization",
        blank=True,
        null=True,
        related_name="memberships_as_member",
        verbose_name=_("Organization"),
        help_text=_("The organization who is a member of the organization"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/person.json#"
    person = models.ForeignKey(
        to="Person",
        blank=True,
        null=True,
        related_name="memberships",
        verbose_name=_("Person"),
        help_text=_("The person who is a member of the organization"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey(
        to="Organization",
        blank=True,
        null=True,
        related_name="memberships",
        verbose_name=_("Organization"),
        help_text=_("The organization in which the person or organization is a member"),
        on_delete=models.CASCADE,
    )

    appointed_by = models.ForeignKey(
        to="Membership",
        blank=True,
        null=True,
        related_name="appointees",
        verbose_name=_("Appointed by"),
        help_text=_("The Membership that officially has appointed this one."),
        on_delete=models.SET_NULL,
    )

    appointment_note = models.TextField(
        verbose_name=_("appointment note"),
        blank=True,
        null=True,
        help_text=_("A textual note for this appointment, if needed."),
    )

    is_appointment_locked = models.BooleanField(
        default=False,
        help_text=_(
            "A flag that shows if this appointment is locked (set to true when manually creating the appointment)"
        ),
    )

    on_behalf_of = models.ForeignKey(
        to="Organization",
        blank=True,
        null=True,
        related_name="memberships_on_behalf_of",
        verbose_name=_("On behalf of"),
        help_text=_("The organization on whose behalf the person " "is a member of the organization"),
        on_delete=models.SET_NULL,
    )

    # reference to "http://popoloproject.com/schemas/post.json#"
    post = models.ForeignKey(
        to="Post",
        blank=True,
        null=True,
        related_name="memberships",
        verbose_name=_("Post"),
        help_text=_("The post held by the person in the " "organization through this membership"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        to="Area",
        blank=True,
        null=True,
        related_name="memberships",
        verbose_name=_("Area"),
        help_text=_("The geographic area to which the membership is related"),
        on_delete=models.SET_NULL,
    )

    classifications = GenericRelation(
        to="ClassificationRel", help_text=_("OP_TOPIG_TAG classifications")
    )

    # these fields store information present in the Openpolitici
    # database, that will constitute part of the Election
    # info-set in the future
    # THEY ARE TO BE CONSIDERED TEMPORARY
    constituency_descr_tmp = models.CharField(
        blank=True, null=True, max_length=128, verbose_name=_("Constituency location description")
    )

    electoral_list_descr_tmp = models.CharField(
        blank=True, null=True, max_length=512, verbose_name=_("Electoral list description")
    )
    # END OF TEMP

    electoral_event = models.ForeignKey(
        to="KeyEvent",
        blank=True,
        null=True,
        limit_choices_to={"event_type__contains": "ELE"},
        related_name="memberships_assigned",
        verbose_name=_("Electoral event"),
        help_text=_("The electoral event that assigned this membership"),
        on_delete=models.SET_NULL,
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        to="ContactDetail", help_text=_("Means of contacting the member of the organization")
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(to="LinkRel", help_text=_("URLs to documents about the membership"))

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the membership"))

    @property
    def member(self):
        if self.member_organization:
            return self.member_organization
        else:
            return self.person

    @property
    def slug_source(self):
        return f"{self.member.name} {self.organization.name}"

    def __str__(self) -> str:
        if self.label:
            return f"{getattr(self.member, 'name')} -[{self.label}]> " \
                f"{self.organization} ({self.start_date} - {self.end_date})"
        else:
            return f"{getattr(self.member, 'name')} -[member of]> " \
                f"{self.organization} ({self.start_date} - {self.end_date})"

    def get_apicals(self, current=True):
        """Return list of apicals memberships related to m.

        :param selg: the Membership object
        :param current: whether the apicals must be filtered out to compute
                        the current, date-crossing apicals
        :return: the list of apical Memberships, as queryset
        """
        if self.organization.classification in ["Consiglio regionale", "Giunta regionale"]:
            apicals = self.organization.parent.children.get(
                classification='Giunta regionale'
            ).memberships.filter(
                role__istartswith='Presidente'
            )
        elif self.organization.classification in ["Consiglio provinciale", "Giunta provinciale"]:
            apicals = self.organization.parent.children.get(
                classification='Giunta provinciale'
            ).memberships.filter(
                role='Presidente di Provincia'
            )
        elif self.organization.classification in ["Consiglio metropolitano", "Giunta metropolitana"]:
            apicals = self.organization.parent.children.get(
                classification='Giunta metropolitana'
            ).memberships.filter(
                role__istartswith='Sindaco metropolitano'
            )
        elif self.organization.classification in ["Consiglio comunale", "Giunta comunale"]:
            apicals = self.organization.parent.children.get(
                classification='Giunta comunale'
            ).memberships.filter(
                role__istartswith='Sindaco'
            )
        else:
            return Membership.objects.none()

        apicals = apicals.order_by(
            F('electoral_event__start_date').desc(nulls_last=True),
            '-start_date'
        )

        if current:
            if self.end_date is not None:
                apicals = apicals.filter(
                    Q(start_date__lte=self.start_date) & (Q(end_date__gt=self.start_date) | Q(end_date__isnull=True)) |
                    Q(start_date__lt=self.end_date) & (Q(end_date__gte=self.end_date) | Q(end_date__isnull=True))
                )
            else:
                apicals = apicals.filter(start_date__lte=self.start_date, end_date__isnull=True)

        return apicals

    def get_electoral_event(self, logger=None):
        """Given a membership object,
        looks up the apical membership and returns its electoral_event.

        :param logger: The logger object to emit logging messages
        :return: a KeyEvent containing the corresponding electoral event
        """
        apicals = self.get_apicals()
        n_apicals = apicals.count()
        if n_apicals == 1:
            if logger:
                logger.debug(f"{self}")
                logger.debug(f"  {apicals.first()}")
                logger.debug(f"  {apicals.first().electoral_event}")
            return apicals.first().electoral_event
        elif n_apicals == 0:
            return None
        else:
            if logger:
                logger.debug(f"  found {n_apicals} apical memberships for {self}!")
                for a in apicals:
                    logger.debug(f"  - {a}")
            return None

    def this_and_next_electoral_events(self, logger=None):
        """Return the electoral event for this membership (from its apicals),
        and the next electoral event, computed from organization apicals memebrships.

        :param m: The Memebrship this computation is performed for
        :return: 2-tuple of KeyEvent
        """

        all_apicals = self.get_apicals(current=False)

        if self.end_date is not None:
            apicals = all_apicals.filter(
                Q(start_date__lte=self.start_date) & (Q(end_date__gt=self.start_date) | Q(end_date__isnull=True)) |
                Q(start_date__lt=self.end_date) & (Q(end_date__gte=self.end_date) | Q(end_date__isnull=True))
            )
        else:
            apicals = all_apicals.filter(start_date__lte=self.start_date, end_date__isnull=True)

        n_apicals = apicals.count()

        event = None
        distinct_events = KeyEvent.objects.filter(
            pk__in=list(set(apicals.values_list('electoral_event_id', flat=True)))
        )
        n_distinct_events = distinct_events.count()

        if n_distinct_events == 1:
            event = distinct_events.first()
        elif n_distinct_events > 1:
            # compute min days from election date
            # assign the electoral event whose date is nearest to the membership's start date
            min_days = 999999
            dates_fmt = '%Y-%m-%d'
            for e in distinct_events:
                d = datetime.strptime(self.start_date, dates_fmt) - datetime.strptime(e.start_date, dates_fmt)
                if 0 < d.days < min_days:
                    min_days = abs(d.days)
                    event = e

            if event is None and logger:
                logger.warning(
                    f"  found {n_distinct_events} different electoral events for the {n_apicals} apicals "
                    f"for {self} - {self.electoral_event}!"
                )
                for a in apicals:
                    logger.warning(f"  - {a} {a.electoral_event}")

            if event is not None and logger:
                logger.debug(
                    f"  found {n_distinct_events} different electoral events for the {n_apicals} apicals "
                    f"for {self} - {self.electoral_event}!"
                )
                for a in apicals:
                    logger.debug(f"  - {a} {a.electoral_event}")
                logger.debug(f"  - {event} was selected")

        next_event = None
        if self.electoral_event is not None:
            m = all_apicals.filter(
                electoral_event__start_date__gt=self.electoral_event.start_date
            ).last()
            if m:
                next_event = m.electoral_event

        return event, next_event


class Ownership(SourceShortcutsMixin, Dateframeable, Timestampable, Permalinkable, models.Model):
    """
    A relationship between an organization and an owner
    (be it a Person or another Organization), that indicates
    an ownership and quantifies it.

    Off-spec model.
    """

    url_name = "ownership-detail"

    class Meta:
        verbose_name = _("Ownership")
        verbose_name_plural = _("Ownerships")

    objects = OwnershipQuerySet.as_manager()

    # person or organization that is a member of the organization
    owned_organization = models.ForeignKey(
        to="Organization",
        related_name="ownerships_as_owned",
        verbose_name=_("Owned organization"),
        help_text=_("The owned organization"),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/person.json#"
    owner_person = models.ForeignKey(
        to="Person",
        blank=True,
        null=True,
        related_name="ownerships",
        verbose_name=_("Person"),
        help_text=_("A person owning part of this organization."),
        on_delete=models.CASCADE,
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    owner_organization = models.ForeignKey(
        to="Organization",
        blank=True,
        null=True,
        related_name="ownerships",
        verbose_name=_("Owning organization"),
        help_text=_("An organization owning part of this organization"),
        on_delete=models.CASCADE,
    )

    percentage = models.FloatField(
        verbose_name=_("percentage ownership"),
        validators=[validate_percentage],
        help_text=_("The *required* percentage ownership, expressed as a floating " "number, from 0 to 1"),
    )
    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the ownership"))

    @property
    def owner(self):
        if self.owner_organization:
            return self.owner_organization
        else:
            return self.owner_person

    @property
    def slug_source(self):
        return f"{self.owner.name} {self.owned_organization.name} ({self.percentage * 100}%)"

    def __str__(self) -> str:
        return "{0} -[owns {1}% of]> {2}".format(
            getattr(self.owner, "name"), self.percentage, self.owned_organization.name
        )


class ContactDetail(SourceShortcutsMixin, Timestampable, Dateframeable, GenericRelatable, models.Model):
    """
    A means of contacting an entity.

    JSON schema: http://popoloproject.com/schemas/contact-detail.json#
    """

    class Meta:
        verbose_name = _("Contact detail")
        verbose_name_plural = _("Contact details")

    objects = ContactDetailQuerySet.as_manager()

    CONTACT_TYPES = Choices(
        ("ADDRESS", "address", _("Address")),
        ("EMAIL", "email", _("Email")),
        ("URL", "url", _("Url")),
        ("MAIL", "mail", _("Snail mail")),
        ("TWITTER", "twitter", _("Twitter")),
        ("FACEBOOK", "facebook", _("Facebook")),
        ("PHONE", "phone", _("Telephone")),
        ("MOBILE", "mobile", _("Mobile")),
        ("TEXT", "text", _("Text")),
        ("VOICE", "voice", _("Voice")),
        ("FAX", "fax", _("Fax")),
        ("CELL", "cell", _("Cell")),
        ("VIDEO", "video", _("Video")),
        ("INSTAGRAM", "instagram", _("Instagram")),
        ("YOUTUBE", "youtube", _("Youtube")),
        ("PAGER", "pager", _("Pager")),
        ("TEXTPHONE", "textphone", _("Textphone")),
        ("LINKEDIN", "linkedin", _("LinkedIn")),
    )

    label = models.CharField(
        verbose_name=_("label"),
        max_length=256,
        blank=True,
        help_text=_("A human-readable label for the contact detail"),
    )

    contact_type = models.CharField(
        verbose_name=_("type"),
        max_length=12,
        choices=CONTACT_TYPES,
        help_text=_("A type of medium, e.g. 'fax' or 'email'"),
    )

    value = models.CharField(
        verbose_name=_("value"), max_length=256, help_text=_("A value, e.g. a phone number or email address")
    )

    note = models.CharField(
        verbose_name=_("note"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("A note, e.g. for grouping contact details by physical location"),
    )

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the contact detail"))

    def __str__(self) -> str:
        return f"{self.value} - {self.contact_type}"


class Area(
    SourceShortcutsMixin,
    LinkShortcutsMixin,
    IdentifierShortcutsMixin,
    OtherNamesShortcutsMixin,
    Permalinkable,
    Dateframeable,
    Timestampable,
    models.Model,
):
    """
    A geographic area whose geometry may change over time.

    e.g. a country, city, ward, etc.

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

    class Meta:
        verbose_name = _("Geographic Area")
        verbose_name_plural = _("Geographic Areas")
        unique_together = ("identifier", "istat_classification")

    url_name = "area-detail"

    objects = AreaQuerySet.as_manager()

    historic_objects = HistoricAreaManager()

    name = models.CharField(
        verbose_name=_("name"), max_length=256, blank=True, help_text=_("The official, issued name")
    )

    identifier = models.CharField(
        verbose_name=_("identifier"), max_length=128, blank=True, help_text=_("The main issued identifier")
    )

    classification = models.CharField(
        verbose_name=_("classification"),
        max_length=128,
        blank=True,
        help_text=_(
            "An area category, according to GEONames definitions: " "http://www.geonames.org/export/codes.html"
        ),
    )

    ISTAT_CLASSIFICATIONS = Choices(
        ("NAZ", "nazione", _("Country")),
        ("RIP", "ripartizione", _("Geographic partition")),
        ("REG", "regione", _("Region")),
        ("PROV", "provincia", _("Province")),
        ("AI", "area_interna", _("Internal area")),
        ("CM", "metro", _("Metropolitan area")),
        ("COM", "comune", _("Municipality")),
        ("MUN", "municipio", _("Submunicipality")),
        ("ZU", "zona_urbanistica", _("Zone")),
    )
    istat_classification = models.CharField(
        verbose_name=_("ISTAT classification"),
        max_length=4,
        blank=True,
        null=True,
        choices=ISTAT_CLASSIFICATIONS,
        help_text=_(
            "An area category, according to ISTAT: "
            "Ripartizione Geografica, Regione, Provincia, "
            "Città Metropolitana, Comune"
        ),
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(
        to="Identifier", help_text=_("Other issued identifiers (zip code, other useful codes, ...)")
    )

    @property
    def other_identifiers(self):
        return self.identifiers

    # array of items referencing
    # "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(to="OtherName", help_text=_("Alternate or former names"))

    # reference to "http://popoloproject.com/schemas/area.json#"
    parent = models.ForeignKey(
        to="Area",
        blank=True,
        null=True,
        related_name="children",
        verbose_name=_("Main parent"),
        help_text=_("The area that contains this area, " "as for the main administrative subdivision."),
        on_delete=models.CASCADE,
    )

    is_provincial_capital = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_("Is provincial capital"),
        help_text=_("If the city is a provincial capital." "Takes the Null value if not a municipality."),
    )

    geometry = models.MultiPolygonField(
        verbose_name=_("Geometry"),
        null=True,
        blank=True,
        help_text=_("The geometry of the area"),
        dim=2,
    )

    @property
    def geom(self):
        """
        The geometry of the area expressed as a GeoJSON string.
        Property implemented for backward compatibility.
        It might be deprecated in the future.
        :return:    A GeoJSON string representing the geometry of the area.
        :rtype:     str
        """
        return self.geometry.json if self.geometry else None

    @property
    def coordinates(self):
        """
        The centroid point of the area.
        :return:    A GEOS point representing the centroid point of the area.
        :rtype:     Point
        """
        return self.geometry.centroid if self.geometry else None

    def _lat(self):
        """
        The latitude coordinate.
        :return:    The latitude coordinate.
        :rtype:     float
        """
        return self.coordinates.y if self.coordinates else None
    _lat.short_description = _("Latitude")
    gps_lat = property(_lat)

    def _lon(self):
        """
        The longitude coordinate.
        :return:    The longitude coordinate.
        :rtype:     float
        """
        return self.coordinates.x if self.coordinates else None
    _lon.short_description = _("Longitude")
    gps_lon = property(_lon)

    # inhabitants, can be useful for some queries
    inhabitants = models.PositiveIntegerField(
        verbose_name=_("inhabitants"), null=True, blank=True, help_text=_("The total number of inhabitants")
    )

    # array of items referencing "http://popoloproject.com/schemas/links.json#"
    links = GenericRelation(to="LinkRel", blank=True, null=True, help_text=_("URLs to documents relted to the Area"))

    # array of items referencing "http://popoloproject.com/schemas/source.json#"
    sources = GenericRelation(
        to="SourceRel", blank=True, null=True, help_text=_("URLs to source documents about the Area")
    )

    # related areas
    related_areas = models.ManyToManyField(
        to="self",
        through="AreaRelationship",
        through_fields=("source_area", "dest_area"),
        help_text=_("Relationships between areas"),
        related_name="inversely_related_areas",
        symmetrical=False,
    )

    new_places = models.ManyToManyField(
        to="self",
        blank=True,
        related_name="old_places",
        symmetrical=False,
        help_text=_("Link to area(s) after date_end"),
    )

    @property
    def slug_source(self):
        return "{0}-{1}".format(self.istat_classification, self.identifier)

    def add_i18n_name(self, name, language, update=False):
        """add an i18 name to the area
        if a name for that language already exists, then it is not touched, unless specified

        :param update:
        :param name: The i18n name
        :param language: a Language instance
        :return:
        """

        if not isinstance(language, Language):
            raise Exception(_("The language parameter needs to be a Language instance"))
        i18n_name, created = self.i18n_names.get_or_create(language=language, defaults={"name": name})

        if not created and update:
            i18n_name.name = "name"
            i18n_name.save()

        return i18n_name

    def merge_from(self, *areas, **kwargs):
        """merge a list of areas into this one, creating relationships
        of new/old places

        :param areas:
        :param kwargs:
        :return:
        """
        moment = kwargs.get("moment", datetime.strftime(datetime.now(), "%Y-%m-%d"))

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
        moment = kwargs.get("moment", datetime.strftime(datetime.now(), "%Y-%m-%d"))

        for ai in areas:
            ai.start_date = moment
            ai.save()
            self.new_places.add(ai)
        self.close(moment=moment, reason=_("Split into other areas"))

    def add_relationship(self, area, classification, start_date=None, end_date=None, **kwargs):
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
            defaults=kwargs,
        )
        return relationship, created

    def remove_relationship(self, area, classification, start_date, end_date, **kwargs):
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
            **kwargs,
        )

        if r.count() > 1:
            raise Exception(_("More than one relationships found"))
        elif r.count() == 0:
            raise Exception(_("No relationships found"))
        else:
            r.delete()

    def get_relationships(self, classification):
        return self.from_relationships.filter(classification=classification).select_related(
            "source_area", "dest_area"
        )

    def get_inverse_relationships(self, classification):
        return self.to_relationships.filter(classification=classification).select_related("source_area", "dest_area")

    def get_former_parents(self, moment_date=None):
        """returns all parent relationtips valid at moment_date

        If moment_date is none, then returns all relationtips independently
        from their start and end dates

        :param moment_date: moment of validity, as YYYY-MM-DD
        :return: AreaRelationship queryset,
            with source_area and dest_area pre-selected
        """
        rels = self.get_relationships(AreaRelationship.CLASSIFICATION_TYPES.former_istat_parent).order_by("-end_date")

        if moment_date is not None:
            rels = rels.filter(Q(start_date__lt=moment_date) | Q(start_date__isnull=True)).filter(
                Q(end_date__gt=moment_date) | Q(end_date__isnull=True)
            )

        return rels

    def get_former_children(self, moment_date=None):
        """returns all children relationtips valid at moment_date

        If moment_date is none, then returns all relationtips independently
        from their start and end dates

        :param moment_date: moment of validity, as YYYY-MM-DD
        :return: AreaRelationship queryset,
            with source_area and dest_area pre-selected
        """
        rels = self.get_inverse_relationships(AreaRelationship.CLASSIFICATION_TYPES.former_istat_parent).order_by(
            "-end_date"
        )

        if moment_date is not None:
            rels = rels.filter(Q(start_date__lt=moment_date) | Q(start_date__isnull=True)).filter(
                Q(end_date__gt=moment_date) | Q(end_date__isnull=True)
            )

        return rels

    def __str__(self) -> str:
        return f"{self.name}"


class AreaRelationship(SourceShortcutsMixin, Dateframeable, Timestampable, models.Model):
    """
    A relationship between two areas.

    Must be defined by a classification (type, ex: other_parent, previously, ...)

    Off-spec model.
    """

    class Meta:
        verbose_name = _("Area relationship")
        verbose_name_plural = _("Area relationships")

    objects = AreaRelationshipQuerySet.as_manager()

    source_area = models.ForeignKey(
        to="Area",
        related_name="from_relationships",
        verbose_name=_("Source area"),
        help_text=_("The Area the relation starts from"),
        on_delete=models.CASCADE,
    )

    dest_area = models.ForeignKey(
        to="Area",
        related_name="to_relationships",
        verbose_name=_("Destination area"),
        help_text=_("The Area the relationship ends to"),
        on_delete=models.CASCADE,
    )

    CLASSIFICATION_TYPES = Choices(
        ("FIP", "former_istat_parent", _("Former ISTAT parent")),
        ("AMP", "alternate_mountain_community_parent", _("Alternate mountain community parent")),
        ("ACP", "alternate_consortium_parent", _("Alternate consortium of municipality parent")),
        ("AIP", "alternate_internal_area_parent", _("Alternate internal area parent")),
        ("DEP", "depends_on", _("Area depends on another area")),
    )
    classification = models.CharField(
        max_length=3,
        choices=CLASSIFICATION_TYPES,
        help_text=_("The relationship classification, ex: Former ISTAT parent, ..."),
    )

    note = models.TextField(blank=True, null=True, help_text=_("Additional info about the relationship"))

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(to="SourceRel", help_text=_("URLs to source documents about the relationship"))

    def __str__(self) -> str:
        if self.classification:
            return "{0} -[{1} ({3} -> {4})]-> {2}".format(
                self.source_area.name,
                self.get_classification_display(),
                self.dest_area.name,
                self.start_date,
                self.end_date,
            )
        else:
            return "{0} -[({2} -> {3})]-> {1}".format(
                self.source_area.name, self.dest_area.name, self.start_date, self.end_date
            )


class AreaI18Name(models.Model):
    """
    Internationalized name for an Area.
    Contains references to language and area.
    """

    class Meta:
        verbose_name = _("I18N Name")
        verbose_name_plural = _("I18N Names")
        unique_together = ("area", "language", "name")

    area = models.ForeignKey(to="Area", related_name="i18n_names", on_delete=models.CASCADE)

    language = models.ForeignKey(to="Language", verbose_name=_("Language"), on_delete=models.CASCADE)

    name = models.CharField(verbose_name=_("name"), max_length=255)

    def __str__(self) -> str:
        return f"{self.language} - {self.name}"


class Language(models.Model):
    """
    Maps languages, with names and 2-char iso 639-1 codes.
    Taken from http://dbpedia.org, using a sparql query
    """

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")

    name = models.CharField(verbose_name=_("name"), max_length=128, help_text=_("English name of the language"))

    iso639_1_code = models.CharField(
        verbose_name=_("iso639_1 code"),
        max_length=2,
        unique=True,
        help_text=_("ISO 639_1 code, ex: en, it, de, fr, es, ..."),
    )

    dbpedia_resource = models.CharField(
        verbose_name=_("dbpedia resource"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("DbPedia URI of the resource"),
        unique=True,
    )

    def __str__(self) -> str:
        return f"{self.name} ({ self.iso639_1_code})"


class KeyEventRel(GenericRelatable, models.Model):
    """
    The relation between a generic object and a KeyEvent
    """

    key_event = models.ForeignKey(
        to="KeyEvent",
        related_name="related_objects",
        help_text=_("A relation to a KeyEvent instance assigned to this object"),
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.content_object} - {self.key_event}"


class KeyEvent(Permalinkable, Dateframeable, Timestampable, models.Model):
    """
    An electoral event generically describes an electoral session.

    It is used mainly to group all electoral results.

    This is an extension of the Popolo schema
    """

    class Meta:
        verbose_name = _("Key event")
        verbose_name_plural = _("Key events")
        unique_together = ("start_date", "event_type")

    url_name = "keyevent-detail"

    objects = KeyEventQuerySet.as_manager()

    name = models.CharField(
        _("name"),
        max_length=256,
        blank=True,
        null=True,
        help_text=_("A primary, generic name, e.g.: Local elections 2016"),
    )

    # TODO: transform into an external table, so that new event_types can be added by non-coders
    EVENT_TYPES = Choices(
        ("ELE", "election", _("Election round")),
        ("ELE-POL", "pol_election", _("National election")),
        ("ELE-SUP", "sup_election", _("National suppletive election")),
        ("ELE-EU", "eu_election", _("European election")),
        ("ELE-REG", "reg_election", _("Regional election")),
        ("ELE-METRO", "metro_election", _("Metropolitan election")),
        ("ELE-PROV", "prov_election", _("Provincial election")),
        ("ELE-COM", "com_election", _("Comunal election")),
        ("ITL", "it_legislature", _("IT legislature")),
        ("EUL", "eu_legislature", _("EU legislature")),
        ("XAD", "externaladm", _("External administration")),
    )
    event_type = models.CharField(
        _("event type"),
        default="ELE",
        max_length=12,
        choices=EVENT_TYPES,
        help_text=_("The electoral type, e.g.: election, legislature, ..."),
    )

    identifier = models.CharField(
        _("identifier"), max_length=512, blank=True, null=True, help_text=_("An issued identifier")
    )

    @property
    def slug_source(self):
        return f"{self.name} {self.get_event_type_display()}"

    def __str__(self) -> str:
        return f"{self.name}"


class OtherName(Dateframeable, GenericRelatable, models.Model):
    """
    An alternate or former name
    see schema at http://popoloproject.com/schemas/name-component.json#
    """

    class Meta:
        verbose_name = _("Other name")
        verbose_name_plural = _("Other names")

    objects = OtherNameQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=512, help_text=_("An alternate or former name"))

    NAME_TYPES = Choices(
        ("FOR", "former", _("Former name")),
        ("ALT", "alternate", _("Alternate name")),
        ("AKA", "aka", _("Also Known As")),
        ("NIC", "nickname", _("Nickname")),
        ("ACR", "acronym", _("Acronym")),
    )
    othername_type = models.CharField(
        _("scheme"),
        max_length=3,
        default="ALT",
        choices=NAME_TYPES,
        help_text=_("Type of other name, e.g. FOR: former, ALT: alternate, ..."),
    )

    note = models.CharField(
        _("note"),
        max_length=1024,
        blank=True,
        null=True,
        help_text=_("An extended note, e.g. 'Birth name used before marrige'"),
    )

    source = models.URLField(
        _("source"),
        max_length=256,
        blank=True,
        null=True,
        help_text=_("The URL of the source where this information comes from"),
    )

    def __str__(self) -> str:
        return f"{self.name}"


class Identifier(Dateframeable, GenericRelatable, models.Model):
    """
    An issued identifier
    see schema at http://popoloproject.com/schemas/identifier.json#
    """

    class Meta:
        verbose_name = _("Identifier")
        verbose_name_plural = _("Identifiers")
        indexes = [Index(fields=["identifier"])]

    objects = IdentifierQuerySet.as_manager()

    identifier = models.CharField(
        _("identifier"), max_length=512, help_text=_("An issued identifier, e.g. a DUNS number")
    )

    scheme = models.CharField(_("scheme"), max_length=128, blank=True, help_text=_("An identifier scheme, e.g. DUNS"))

    source = models.URLField(
        _("source"),
        max_length=256,
        blank=True,
        null=True,
        help_text=_("The URL of the source where this information comes from"),
    )

    def __str__(self) -> str:
        return f"{self.scheme}: {self.identifier}"


class LinkRel(GenericRelatable, models.Model):
    """
    The relation between a generic object and a Source
    """

    link = models.ForeignKey(
        to="Link",
        related_name="related_objects",
        help_text=_("A relation to a Link instance assigned to this object"),
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.content_object} - {self.link}"


class Link(models.Model):
    """
    A URL
    see schema at http://popoloproject.com/schemas/link.json#
    """

    class Meta:
        verbose_name = _("Link")
        verbose_name_plural = _("Links")
        unique_together = ("url", "note")

    url = models.URLField(_("url"), max_length=350, help_text=_("A URL"))

    note = models.CharField(_("note"), max_length=512, blank=True, help_text=_("A note, e.g. 'Wikipedia page'"))

    def __str__(self) -> str:
        return f"{self.url}"


class SourceRel(GenericRelatable, models.Model):
    """
    The relation between a generic object and a Source
    """

    source = models.ForeignKey(
        to="Source",
        related_name="related_objects",
        help_text=_("A Source instance assigned to this object"),
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.content_object} - {self.source}"


class Source(models.Model):
    """
    A URL for referring to sources of information
    see schema at http://popoloproject.com/schemas/link.json#
    """

    class Meta:
        verbose_name = _("Source")
        verbose_name_plural = _("Sources")
        unique_together = ("url", "note")

    url = models.URLField(verbose_name=_("url"), max_length=350, help_text=_("A URL"))

    note = models.CharField(
        verbose_name=_("note"), max_length=512, blank=True, help_text=_("A note, e.g. 'Parliament website'")
    )

    def __str__(self) -> str:
        return f"{self.url}"


class Event(Timestampable, SourceShortcutsMixin, models.Model):
    """
    An occurrence that people may attend.

    JSON schema: https://www.popoloproject.com/schemas/event.json
    """

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        unique_together = ("name", "start_date")

    name = models.CharField(verbose_name=_("name"), max_length=128, help_text=_("The event's name"))

    description = models.CharField(
        verbose_name=_("description"), max_length=512, blank=True, null=True, help_text=_("The event's description")
    )

    # start_date and end_date are kept instead of the fields provided by Dateframeable mixin,
    # starting and finishing *timestamps* for the Event are tracked,
    # while fields in Dateframeable track the validity *dates* of the data.
    # TODO: change to DateTimeField (?)
    start_date = models.CharField(
        verbose_name=_("start date"),
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{4}("
                "(-[0-9]{2}){0,2}|(-[0-9]{2}){2}"
                "T[0-9]{2}(:[0-9]{2}){0,2}"
                "(Z|[+-][0-9]{2}(:[0-9]{2})?"
                ")"
                ")$",
                message="start date must follow the given pattern: "
                "^[0-9]{4}("
                "(-[0-9]{2}){0,2}|(-[0-9]{2}){2}"
                "T[0-9]{2}(:[0-9]{2}){0,2}"
                "(Z|[+-][0-9]{2}(:[0-9]{2})?"
                ")"
                ")$",
                code="invalid_start_date",
            )
        ],
        help_text=_("The time at which the event starts"),
    )
    end_date = models.CharField(
        verbose_name=_("end date"),
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{4}("
                "(-[0-9]{2}){0,2}|(-[0-9]{2}){2}"
                "T[0-9]{2}(:[0-9]{2}){0,2}"
                "(Z|[+-][0-9]{2}(:[0-9]{2})?"
                ")"
                ")$",
                message="end date must follow the given pattern: "
                "^[0-9]{4}("
                "(-[0-9]{2}){0,2}|(-[0-9]{2}){2}"
                "T[0-9]{2}(:[0-9]{2}){0,2}"
                "(Z|[+-][0-9]{2}(:[0-9]{2})?"
                ")"
                ")$",
                code="invalid_end_date",
            )
        ],
        help_text=_("The time at which the event ends"),
    )

    # textual full address of the event
    location = models.CharField(
        verbose_name=_("location"), max_length=255, blank=True, null=True, help_text=_("The event's location")
    )
    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        to="Area",
        blank=True,
        null=True,
        related_name="events",
        help_text=_("The Area the Event is related to"),
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        verbose_name=_("status"), max_length=128, blank=True, null=True, help_text=_("The event's status")
    )

    # add 'identifiers' property to get array of items referencing
    # 'http://www.popoloproject.com/schemas/identifier.json#'
    identifiers = GenericRelation(
        to="Identifier", blank=True, null=True, help_text=_("Issued identifiers for this event")
    )

    classification = models.CharField(
        verbose_name=_("classification"), max_length=128, blank=True, null=True, help_text=_("The event's category")
    )

    # reference to 'http://www.popoloproject.com/schemas/organization.json#'
    organization = models.ForeignKey(
        to="Organization",
        blank=True,
        null=True,
        related_name="events",
        help_text=_("The organization organizing the event"),
        on_delete=models.CASCADE,
    )

    # array of items referencing 'http://www.popoloproject.com/schemas/person.json#'
    attendees = models.ManyToManyField(
        to="Person", blank=True, related_name="attended_events", help_text=_("People attending the event")
    )

    # reference to 'http://www.popoloproject.com/schemas/event.json#'
    parent = models.ForeignKey(
        to="Event",
        blank=True,
        null=True,
        related_name="children",
        verbose_name=_("Parent"),
        help_text=_("The Event that this event is part of"),
        on_delete=models.CASCADE,
    )

    # array of items referencing
    # 'http://www.popoloproject.com/schemas/source.json#'
    sources = GenericRelation(
        to="SourceRel", help_text=_("URLs to source documents about the event"), on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"{self.name} - {self.start_date}"


class OriginalProfession(models.Model):
    """
    Profession of a Person, according to the original source.

    Off-spec model.
    """

    class Meta:
        verbose_name = _("Original profession")
        verbose_name_plural = _("Original professions")

    name = models.CharField(
        verbose_name=_("name"), max_length=1024, unique=True, help_text=_("The original profession name")
    )

    normalized_profession = models.ForeignKey(
        to="Profession",
        null=True,
        blank=True,
        related_name="original_professions",
        help_text=_("The normalized profession"),
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.name}"

    def save(self, *args, **kwargs):
        """
        Upgrade persons professions when the normalized profession is changed

        :param args:
        :param kwargs:
        :return:
        """
        super(OriginalProfession, self).save(*args, **kwargs)
        if self.normalized_profession:
            self.persons_with_this_original_profession.exclude(profession=self.normalized_profession).update(
                profession=self.normalized_profession
            )


class Profession(IdentifierShortcutsMixin, models.Model):
    """
    Profession of a Person, as a controlled vocabulary.

    Off-spec model.
    """

    class Meta:
        verbose_name = _("Normalized profession")
        verbose_name_plural = _("Normalized professions")

    name = models.CharField(
        verbose_name=_("name"), max_length=1024, unique=True, help_text=_("Normalized profession name")
    )

    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(to="Identifier", help_text=_("Other identifiers for this profession (ISTAT code)"))

    def __str__(self) -> str:
        return f"{self.name}"


class OriginalEducationLevel(models.Model):
    """
    Non-normalized education level, as received from sources
    With identifiers (ICSED).

    Off-spec model.
    """

    class Meta:
        verbose_name = _("Original education level")
        verbose_name_plural = _("Original education levels")

    name = models.CharField(verbose_name=_("name"), max_length=512, unique=True, help_text=_("Education level name"))

    normalized_education_level = models.ForeignKey(
        to="EducationLevel",
        null=True,
        blank=True,
        related_name="original_education_levels",
        help_text=_("The normalized education_level"),
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.normalized_education_level})"

    def save(self, *args, **kwargs):
        """Upgrade persons education_levels when the normalized education_level is changed

        :param args:
        :param kwargs:
        :return:
        """
        super(OriginalEducationLevel, self).save(*args, **kwargs)
        if self.normalized_education_level:
            self.persons_with_this_original_education_level.exclude(
                education_level=self.normalized_education_level
            ).update(education_level=self.normalized_education_level)


class EducationLevel(IdentifierShortcutsMixin, models.Model):
    """
    Normalized education level
    With identifiers (ICSED).
    """

    class Meta:
        verbose_name = _("Normalized education level")
        verbose_name_plural = _("Normalized education levels")

    name = models.CharField(verbose_name=_("name"), max_length=256, unique=True, help_text=_("Education level name"))

    # array of items referencing
    # "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(
        to="Identifier", help_text=_("Other identifiers for this education level (ICSED code)")
    )

    def __str__(self) -> str:
        return f"{self.name}"

# TODO: link an electoral list (Organization?) to a party (Organization).
# class ElectoralEndorsement(models.Model):
#     """
#     An official political endorsement from a party to an electoral list for a specific electoral event.
#     """
#
#     class Meta:
#         verbose_name = _("electoral endorsement")
#         verbose_name_plural = _("electoral endorsements")
#
#     electoral_list = models.ForeignKey(
#         verbose_name=_("endorsed electoral list"),
#         help_text=_("The endorsed electoral list"),
#         to=Organization,
#         related_name="endorsed_by",
#         on_delete=models.CASCADE,
#     )
#
#     party = models.ForeignKey(
#         verbose_name=_("endorsing political party"),
#         help_text=_("The endorsing party"),
#         to=Organization,
#         related_name="endorsed",
#         on_delete=models.CASCADE,
#     )
#
#     event = models.ForeignKey(
#         verbose_name=_("electoral event"), help_text="The electoral event", to=KeyEvent, on_delete=models.CASCADE,
#     )
#
#     def __str__(self):
#         return f"{self.party} endorsed {self.electoral_list} @ {self.event.name}"
