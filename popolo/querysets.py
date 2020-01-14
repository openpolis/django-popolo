from typing import Dict, Tuple

from django.db.models import Q

__author__ = "guglielmo"

from django.db import models, transaction
from datetime import datetime


class PopoloQueryset(models.query.QuerySet):
    def strategic_update_or_create(
        self, defaults: Dict = None, strategy: str = "overwrite", **kwargs
    ) -> Tuple[models.Model, bool]:

        """
        Look up an object with the given kwargs, updating one with defaults
        if it exists, otherwise create a new one.

        Return a tuple (object, created), where created is a boolean
        specifying whether an object was created.

        Patched version of `update_or_create` which allows different update strategy.

        :param defaults: a dictionary of (field, value) pairs used to update the object
        :param strategy:
            - `overwrite`: (default) Normal `update_or_create` behaviour.
            - `keep_old`: Only update fields which do not have an already set-value.
                In other words, just update fields which are non-null.
        :param kwargs: Fields used to fetch the object.
            May be empty if your model has defaults for all fields.
        :return: a tuple (object, created), where created is a boolean
            specifying whether an object was created.
        """

        self._for_write = True
        with transaction.atomic(using=self.db):
            try:
                obj = self.select_for_update().get(**kwargs)
            except self.model.DoesNotExist:
                params = self._extract_model_params(defaults, **kwargs)
                # Lock the row so that a concurrent update is blocked until
                # after update_or_create() has performed its save.
                obj, created = self._create_object_from_params(kwargs, params, lock=True)
                if created:
                    return obj, created
            for k, v in defaults.items():
                if strategy == "keep_old" and getattr(obj, k):
                    continue  # Do not update already set attribute

                setattr(obj, k, v() if callable(v) else v)
            obj.save(using=self.db)
        return obj, False


class DateframeableQuerySet(models.query.QuerySet):
    """
    A custom ``QuerySet`` allowing easy retrieval of current, past and future
    instances
    of a Dateframeable model.

    Here, a *Dateframeable model* denotes a model class having an associated
    date range.

    We assume that the date range is described by two ``Char`` fields
    named ``start_date`` and ``end_date``, respectively,
    whose validation pattern is: "^[0-9]{4}(-[0-9]{2}){0,2}$",
    in order to represent partial dates.
    """

    def past(self, moment=None):
        """
        Return a QuerySet containing the *past* instances of the model
        (i.e. those having an end date which is in the past).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), "%Y-%m-%d")
        return self.filter(end_date__lte=moment)

    def future(self, moment=None):
        """
        Return a QuerySet containing the *future* instances of the model
        (i.e. those having a start date which is in the future).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), "%Y-%m-%d")
        return self.filter(start_date__gte=moment)

    def current(self, moment=None):
        """
        Return a QuerySet containing the *current* instances of the model
        at the given moment in time, if the parameter is spcified
        now if it is not
        @moment - is a string, representing a date in the YYYY-MM-DD format
        (i.e. those for which the moment date-time lies within their
        associated time range).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), "%Y-%m-%d")

        return self.filter(
            (Q(start_date__lte=moment) | Q(start_date__isnull=True))
            & (Q(end_date__gte=moment) | Q(end_date__isnull=True))
        )


class PersonQuerySet(DateframeableQuerySet):
    pass


class OrganizationQuerySet(DateframeableQuerySet):
    def municipalities(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Comune",
        )

    def comuni(self):
        return self.municipalities()

    def metropolitan_areas(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Città metropolitana",
        )

    def metropoli(self):
        return self.metropolitan_areas()

    def provinces(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Provincia",
        )

    def province(self):
        return self.provinces()

    def provincie(self):
        return self.provinces()

    def regions(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Regione",
        )

    def regioni(self):
        return self.regions()

    def giunte_regionali(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Giunta regionale",
        )

    def giunte_provinciali(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Giunta provinciale",
        )

    def giunte_comunali(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Giunta comunale",
        )

    def conferenze_metropolitane(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Conferenza metropolitana",
        )

    def consigli_regionali(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Consiglio regionale",
        )

    def consigli_provinciali(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Consiglio provinciale",
        )

    def consigli_comunali(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Consiglio comunale",
        )

    def consigli_metropolitane(self):
        return self.filter(
            classifications__classification__scheme="FORMA_GIURIDICA_OP",
            classifications__classification__descr="Consiglio metropolitano",
        )


class PostQuerySet(DateframeableQuerySet):
    pass


class MembershipQuerySet(DateframeableQuerySet):
    pass


class OwnershipQuerySet(DateframeableQuerySet):
    pass


class ContactDetailQuerySet(DateframeableQuerySet):
    pass


class OtherNameQuerySet(DateframeableQuerySet):
    pass


class PersonalRelationshipQuerySet(DateframeableQuerySet):
    pass


class OrganizationRelationshipQuerySet(DateframeableQuerySet):
    pass


class KeyEventQuerySet(PopoloQueryset, DateframeableQuerySet):
    pass


class AreaQuerySet(DateframeableQuerySet):
    def municipalities(self):
        return self.filter(istat_classification=self.model.ISTAT_CLASSIFICATIONS.comune)

    def comuni(self):
        return self.municipalities()

    def metropolitan_areas(self):
        return self.filter(istat_classification=self.model.ISTAT_CLASSIFICATIONS.metro)

    def metropoli(self):
        return self.metropolitan_areas()

    def provinces(self):
        return self.filter(istat_classification=self.model.ISTAT_CLASSIFICATIONS.provincia)

    def province(self):
        return self.provinces()

    def regions(self):
        return self.filter(istat_classification=self.model.ISTAT_CLASSIFICATIONS.regione)

    def regioni(self):
        return self.regions()

    def macro_areas(self):
        return self.filter(istat_classification=self.model.ISTAT_CLASSIFICATIONS.ripartizione)

    def ripartizioni(self):
        return self.macro_areas()


class AreaRelationshipQuerySet(DateframeableQuerySet):
    pass


class IdentifierQuerySet(DateframeableQuerySet):
    pass


class ClassificationQuerySet(DateframeableQuerySet):
    pass
