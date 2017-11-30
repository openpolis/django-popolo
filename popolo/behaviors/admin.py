try:
    from django.contrib.contenttypes.admin import GenericTabularInline, \
        GenericStackedInline
except ImportError:
    from django.contrib.contenttypes.generic import GenericTabularInline, \
        GenericStackedInline
from popolo import models


class LinkRelAdmin(GenericTabularInline):
    model = models.LinkRel
    extra = 0


class SourceRelAdmin(GenericTabularInline):
    model = models.SourceRel
    extra = 0


class IdentifierAdmin(GenericTabularInline):
    model = models.Identifier
    extra = 0


class ContactDetailAdmin(GenericStackedInline):
    model = models.ContactDetail
    extra = 0


class OtherNameAdmin(GenericTabularInline):
    model = models.OtherName
    extra = 0


BASE_INLINES = [
    LinkRelAdmin, SourceRelAdmin,
    IdentifierAdmin, ContactDetailAdmin, OtherNameAdmin,
]
