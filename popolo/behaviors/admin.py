try:
    from django.contrib.contenttypes.admin import GenericTabularInline,GenericStackedInline
except ImportError:
    from django.contrib.contenttypes.generic import GenericTabularInline,GenericStackedInline
from popolo import models, behaviors

class LinkAdmin(GenericTabularInline):
    model = models.Link
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
class SourceAdmin(GenericTabularInline):
    model = models.Source
    extra = 0

BASE_INLINES = [
        LinkAdmin,IdentifierAdmin,ContactDetailAdmin,OtherNameAdmin,SourceAdmin
    ]
