from datetime import datetime as dt
from datetime import timedelta
import operator
import sys

from django.utils.translation import ugettext_lazy as _
from popolo.exceptions import PartialDateException


class PartialDatesInterval(object):
    """Class used to represent an interval among two ``PartialDate`` instances
    """

    def __init__(self, start, end):
        """Initialize the instance.

        The interval can be instantiated both with
        `PartialDate` instances and with strings, using the formats
        allowed in `PartialDate`.

        :param start: the starting inteval date
        :param end: the ending interval date
        :type start Union[PartialDate, str]:
        :type end Union[PartialDate, str]:
        """
        if sys.version_info >= (3, 0, 0):

            if isinstance(start, PartialDate):
                self.start = start
            elif isinstance(start, str) or isinstance(start, bytes) or start is None:
                self.start = PartialDate(start)
            else:
                raise PartialDateException(f"Class {type(start)} not allowed here")

            if isinstance(end, PartialDate):
                self.end = end
            elif isinstance(end, str) or isinstance(end, bytes) or end is None:
                self.end = PartialDate(end)
            else:
                raise PartialDateException(f"Class {type(end)} not allowed here")

        else:

            if isinstance(start, PartialDate):
                self.start = start
            elif isinstance(start, str) or start is None:
                self.start = PartialDate(start)
            else:
                raise PartialDateException(f"Class {type(start)} not allowed here")

            if isinstance(end, PartialDate):
                self.end = end
            elif isinstance(end, str) or end is None:
                self.end = PartialDate(end)
            else:
                raise PartialDateException(f"Class {type(end)} not allowed here")

    def __eq__(self, other):
        """Equality operator for PartialDateInterval

        :param other:
        :return:
        """

        if self.start == other.start and self.end == other.end:
            return True
        else:
            return False

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.start is None:
            start = _("forever")
        else:
            start = self.start
        if self.end is None:
            end = _("forever")
        else:
            end = self.end

        return f"{start} => {end}"


class PartialDate(object):
    """Class that holds partial date and is able to compare among them.

    An instance is created by passing the string representation::

        a = PartialDate('2010-01')

        a.date
        > '2010-01'

    During the initialization, the attribute ``date_as_dt`` is instantiated::

        a.date_as_dt
        > datetime.datetime(2010, 1, 1, 0, 0)

    The class allows to switch seamlessly, between the partial textual
    representations of the date (2017-01-04, 2016-04, 2015) and
    their datetime instances.

    Null values are considered during comparisons, raising
    ``PartialDateException`` whenever comparisons are meaningless.

    Partial dates are pointed to the first days in the month, or year.

    Comparison operators are overrided, so that the textual representations
    are always compared.

    The ``intervals_overlap`` class method allows to compare two
    ``PartialDatesInterval`` instances and return the n. of days of overlap.


    """

    d_fmt = "%Y-%m-%d"
    m_fmt = "%Y-%m"
    y_fmt = "%Y"

    HUGE_OVERLAP = 999999

    @classmethod
    def intervals_overlap(cls, a: PartialDatesInterval, b: PartialDatesInterval):
        """Return the number of overlapping days between two intervals.

        Intervals are expressed as instances of the  ``PartialDatesInterval``
        namedtuple.

        Null start and end dates hold special meaning and the overlapping
        computation takes it into account.

        Two interval are overlapping when the returned value is greater than 0.

        When the two starting dates are both null, then the two intervals
        return a ``HUGE_OVERLAP`` value (999999).

        :param a: PartialDatesInterval
        :param b: PartialDatesInterval
        :return: integer
        """

        if not a.start.date and not b.start.date:
            return cls.HUGE_OVERLAP
        elif a.start.date and b.start.date:
            latest_start = max(a.start, b.start)
        elif not a.start.date:
            latest_start = b.start
        elif not b.start.date:
            latest_start = a.start

        if not a.end.date and not b.end.date:
            return cls.HUGE_OVERLAP
        elif a.end.date and b.end.date:
            earliest_end = min(a.end, b.end)
        elif not a.end.date:
            earliest_end = b.end
        elif not b.end.date:
            earliest_end = a.end

        overlap = (earliest_end - latest_start).days

        return overlap

    def __init__(self, date_string):
        """Initialize the instance, trying the various allowed format.

        If the string is not in one of the allowed format, then a
        ``PartialDateException`` is raised.

        The converted datetime instance is stored in the
        ``date_as_dt`` attribute.

        :param date_string: the date in one of the allowed formats.
        """

        self.date = date_string

        if self.date:
            try:
                self.date_as_dt = dt.strptime(self.date, self.d_fmt)
            except ValueError:
                try:
                    self.date_as_dt = dt.strptime(self.date, self.m_fmt)
                except ValueError:
                    try:
                        self.date_as_dt = dt.strptime(self.date, self.y_fmt)
                    except ValueError:
                        raise PartialDateException("Could not convert {0} into datetime".format(self.date))
        else:
            self.date_as_dt = None

    def __sub__(self, other):
        """Overrides the  `-` operator, so that:

        - in case ``other`` is a ``PartialDate`` instance,
          then a ``datetime.timedelta``,
        - in case ``other`` is a ``datetime.timedelta`` instance, then
            a ``PartialDate`` instance is returned.

            a = PartialDate('2010-01')
            b = PartialDate('2008-01')
            a - b
            > datetime.timedelta(731)

        :param other: the subtrahend
        :return: the PartialDate resulting from the subtraction
        :type other: Union[PartialDate, timedelta]
        :rtype: timedelta
        """
        if isinstance(other, PartialDate):
            return self.date_as_dt - other.date_as_dt
        elif isinstance(other, timedelta):
            return self.date_as_dt - other
        else:
            raise PartialDateException("Instance not allowed for the subtrahend")

    def __add__(self, other):
        """override the *add* operation,
        so that a ``datetime.timedelta` addendum can be added

        :param other: the timedelta to be added
        :return: the result of the add operation
        :type other timedelta
        :rtype PartialDate
        """
        if isinstance(other, timedelta):
            res_as_dt = self.date_as_dt + other
            return PartialDate(dt.strftime(res_as_dt, self.d_fmt))
        else:
            raise PartialDateException("Instance not allowed for the addendum")

    def __eq__(self, other):
        """

        :param other:
        :return:
        """

        if other:
            return self.date == other.date
        else:
            return self.date is None

    def _compare(self, other, op):
        """
        Overrides comparison operators.

        Raises an exception if one or both dates are null,
        as null dates are used with different meanings
        for start and end dates and the comparison does not make sense

        :param other: the PartialDate instance to be compared with
        :return: boolean
        """
        if self.date and other.date:
            return op(self.date, other.date)
        else:
            raise PartialDateException("Could not compare null dates")

    def __gt__(self, other):
        return self._compare(other, operator.gt)

    def __ge__(self, other):
        return self._compare(other, operator.ge)

    def __lt__(self, other):
        return self._compare(other, operator.lt)

    def __le__(self, other):
        return self._compare(other, operator.le)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.date is None:
            return "None"
        else:
            return self.date
