from typing import Any


class PartialDateException(Exception):
    """Exception used in the context of the PartialDate class"""

    pass


class OverlappingDateIntervalException(Exception):
    """Raised when date intervals overlap

    Attributes:
        overlapping -- the first entity whose date interval overlaps
        message -- the extended description of the error

    """

    def __init__(self, overlapping: Any, message: str):
        self.overlapping = overlapping
        self.message = message

    def __str__(self) -> str:
        return repr(self.message)
