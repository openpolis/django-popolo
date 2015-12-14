from django.db.models import Q

__author__ = 'guglielmo'

from django.db import models
from datetime import datetime

class DateframeableQuerySet(models.query.QuerySet):
    """
    A custom ``QuerySet`` allowing easy retrieval of current, past and future instances
    of a Dateframeable model.

    Here, a *Dateframeable model* denotes a model class having an associated date range.

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
            moment = datetime.strftime(datetime.now(), '%Y-%m-%d')
        return self.filter(end_date__lte=moment)

    def future(self, moment=None):
        """
        Return a QuerySet containing the *future* instances of the model
        (i.e. those having a start date which is in the future).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), '%Y-%m-%d')
        return self.filter(start_date__gte=moment)

    def current(self, moment=None):
        """
        Return a QuerySet containing the *current* instances of the model
        at the given moment in time, if the parameter is spcified
        now if it is not
        @moment - is a string, representing a date in the YYYY-MM-DD format
        (i.e. those for which the moment date-time lies within their associated time range).
        """
        if moment is None:
            moment = datetime.strftime(datetime.now(), '%Y-%m-%d')

        return self.filter(Q(start_date__lte=moment) &
                           (Q(end_date__gte=moment) | Q(end_date__isnull=True)))




class PersonQuerySet(DateframeableQuerySet):
    pass

class OrganizationQuerySet(DateframeableQuerySet):
    pass

class PostQuerySet(DateframeableQuerySet):
    pass

class MembershipQuerySet(DateframeableQuerySet):
    pass

class ContactDetailQuerySet(DateframeableQuerySet):
    pass

class OtherNameQuerySet(DateframeableQuerySet):
    pass
