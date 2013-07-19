from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from autoslug import AutoSlugField

__author__ = 'guglielmo'


class GenericRelatable(models.Model):
    """
    An abstract class that provides the possibility of generic relations
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True


class Timestampable(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created_at = AutoCreatedField(_('creation time'))
    updated_at = AutoLastModifiedField(_('last modification time'))

    class Meta:
        abstract = True


class Dateframeable(models.Model):
    """
    An abstract base class model that provides a start and an end dates to the class.
    Uncomplete dates can be used. The validation pattern is: "^[0-9]{4}(-[0-9]{2}){0,2}$"
    """
    end_date = models.CharField(_("end date"), max_length=10, blank=True, help_text=_("The date when the validity of the item ends"))
    start_date = models.CharField(_("start date"), max_length=10, blank=True, help_text=_("The date when the validity of the item starts"))

    class Meta:
        abstract = True


class Permalinkable(models.Model):
    """
    An abstract base class model that provides a unique slug,
    and the methods necessary to handle the permalink
    """
    from django.utils.text import slugify

    slug = AutoSlugField(
        populate_from=lambda instance: instance.slug_source,
        unique=True,
        slugify=slugify
    )

    class Meta:
        abstract = True

    def get_url_kwargs(self, **kwargs):
        kwargs.update(getattr(self, 'url_kwargs', {}))
        return kwargs

    @models.permalink
    def get_absolute_url(self):
        url_kwargs = self.get_url_kwargs(slug=self.slug)
        return (self.url_name, (), url_kwargs)

