from django.apps import apps
from django.db import IntegrityError
from django.db.models import Model
from django.db.models.signals import pre_save, post_save
from django.utils.translation import ugettext_lazy as _

from popolo.behaviors.models import Dateframeable
from popolo.models import Organization, Person, Membership, Ownership, OriginalEducationLevel, Post, Area, KeyEvent


def copy_organization_date_fields(sender, instance: Organization, **kwargs):
    """
    Copy founding and dissolution dates into start and end dates,
    so that Organization can extend the abstract Dateframeable behavior.

    :param sender: The model class
    :param instance: The actual instance being saved.
    :param kwargs: Other args. See: https://docs.djangoproject.com/en/dev/ref/signals/#pre-save
    """
    if instance.founding_date:
        instance.start_date = instance.founding_date
    if instance.dissolution_date:
        instance.end_date = instance.dissolution_date


def copy_person_date_fields(sender, instance: Person, **kwargs):
    """
    Copy birth and death dates into start and end dates,
    so that Person can extend the abstract Dateframeable behavior.

    :param sender: The model class
    :param instance: The actual instance being saved.
    :param kwargs: Other args. See: https://docs.djangoproject.com/en/dev/ref/signals/#pre-save
    """

    if instance.birth_date:
        instance.start_date = instance.birth_date
    if instance.death_date:
        instance.end_date = instance.death_date


def verify_start_end_dates_order(sender, instance: Dateframeable, **kwargs):
    """
    All Dateframeable instances need to have proper dates.

    :param sender: The model class
    :param instance: The actual instance being saved.
    :param kwargs: Other args. See: https://docs.djangoproject.com/en/dev/ref/signals/#pre-save
    :raises: IntegrityError
    """

    if instance.start_date and instance.end_date and instance.start_date > instance.end_date:
        raise IntegrityError(_("Initial date must precede end date"))


def verify_start_end_dates_non_blank(sender, instance: Dateframeable, **kwargs):
    """
    Memberships dates must be non-blank.

    :param sender: The model class
    :param instance: The actual instance being saved.
    :param kwargs: Other args. See: https://docs.djangoproject.com/en/dev/ref/signals/#pre-save
    :raises: IntegrityError
    """

    if instance.end_date == "" or instance.start_date == "":
        raise IntegrityError(
            _(
                f"Dates should not be blank for "
                f"{type(instance)} (id:{instance.id}): <{instance.start_date}> - <{instance.end_date}>"
            )
        )


def verify_membership_has_org_and_member(sender, instance: Membership, **kwargs):
    """
    A proper memberships has at least an organisation and a person member

    :param sender: The model class
    :param instance: The actual instance being saved.
    :param kwargs: Other args. See: https://docs.djangoproject.com/en/dev/ref/signals/#pre-save
    :raises: IntegrityError
    """
    if instance.person is None and instance.member_organization is None:
        raise IntegrityError(_("A member, either a Person or an Organization, must be specified."))
    if instance.organization is None:
        raise IntegrityError(_("An Organization, must be specified."))


def verify_ownership_has_org_and_owner(sender, instance: Ownership, **kwargs):
    """
    A proper ownership has at least an owner and an owned organisations.

    :param sender: The model class
    :param instance: The actual instance being saved.
    :param kwargs: Other args. See: https://docs.djangoproject.com/en/dev/ref/signals/#pre-save
    :raises: IntegrityError
    """
    if instance.owner_person is None and instance.owner_organization is None:
        raise IntegrityError(_("An owner, either a Person or an Organization, must be specified."))
    if instance.owned_organization is None:
        raise IntegrityError(_("An owned Organization must be specified."))


def update_education_levels(sender, instance, **kwargs):
    """
    Updates persons education_level when the mapping between
    the original education_level and the normalized one is touched.

    :param sender: The model class
    :param instance: The actual instance being saved.
    :param kwargs: Other args. See: https://docs.djangoproject.com/en/dev/ref/signals/#post-save
    """
    if instance.normalized_education_level:
        instance.persons_with_this_original_education_level.exclude(
            education_level=instance.normalized_education_level
        ).update(education_level=instance.normalized_education_level)


def validate_fields(sender, instance: Model, **kwargs):
    """
    Main instances are always validated before being saved.

    :param sender:
    :param instance:
    :param kwargs:
    """
    instance.full_clean()


def connect():
    """
    Connect all the signals.
    """

    for model_class in [Person, Organization, Post, Membership, Ownership, KeyEvent, Area]:
        pre_save.connect(receiver=validate_fields, sender=model_class)

    pre_save.connect(receiver=copy_organization_date_fields, sender=Organization)

    pre_save.connect(receiver=copy_person_date_fields, sender=Person)

    # Connect a pre-save signal to all models subclassing Dateframeable
    for _dummy, model_class in apps.all_models.get("popolo").items():
        if issubclass(model_class, Dateframeable):
            pre_save.connect(receiver=verify_start_end_dates_order, sender=model_class)
            pre_save.connect(receiver=verify_start_end_dates_non_blank, sender=model_class)

    pre_save.connect(receiver=verify_membership_has_org_and_member, sender=Membership)

    pre_save.connect(receiver=verify_ownership_has_org_and_owner, sender=Ownership)

    post_save.connect(receiver=update_education_levels, sender=OriginalEducationLevel)
