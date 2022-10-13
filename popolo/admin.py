from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.gis import forms
from django.contrib.gis.db.models import MultiPolygonField
from django.db import models
from django.forms import TextInput

from popolo import models as popolo_models


class NullListFilter(SimpleListFilter):
    def lookups(self, request, model_admin):
        return ("1", "Null"), ("0", "!= Null")

    def queryset(self, request, queryset):
        if self.value() in ("0", "1"):
            kwargs = {"{0}__isnull".format(self.parameter_name): self.value() == "1"}
            return queryset.filter(**kwargs)
        return queryset


class EndDateNullListFilter(NullListFilter):
    title = "End date"
    parameter_name = "end_date"


class ClassificationAdmin(admin.ModelAdmin):
    model = popolo_models.Classification
    list_display = ("scheme", "code", "descr")
    list_filter = ("scheme",)
    search_fields = ("code", "descr")
    raw_id_fields = ("parent",)


def set_appointables(modeladmin, request, queryset):
    for item in queryset:
        item.is_appointable = True
        item.save()


set_appointables.short_description = "Set RoleTypes as appointables"


def unset_appointables(modeladmin, request, queryset):
    for item in queryset:
        item.is_appointable = False
        item.save()


unset_appointables.short_description = "Set RoleTypes as not appointables"


class KeyEventAdmin(admin.ModelAdmin):
    model = popolo_models.KeyEvent
    search_fields = ("name", )
    list_filter = ("event_type", )
    list_display = ("name", "identifier", "event_type", "start_date", "end_date", )


class RoleTypeAdmin(admin.ModelAdmin):
    model = popolo_models.RoleType
    list_display = ("label", "classification", "priority", "other_label", "is_appointer", "is_appointable")
    list_filter = (("classification", admin.RelatedOnlyFieldListFilter),)
    list_select_related = ("classification",)
    actions = (set_appointables, unset_appointables)
    search_fields = ("label", "other_label")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "classification":
            kwargs["queryset"] = popolo_models.Classification.objects.filter(scheme="FORMA_GIURIDICA_OP").order_by(
                "code"
            )
        return super(RoleTypeAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class PostAdmin(admin.ModelAdmin):
    model = popolo_models.Post
    list_display = ("label", "role_type", "appointed_by")
    list_filter = (("role_type", admin.RelatedOnlyFieldListFilter),)
    list_select_related = ("role_type", "organization", "appointed_by")
    search_fields = ("label", "other_label", "role", "role_type__label")
    raw_id_fields = ("role_type", "organization", "appointed_by")
    exclude = ("start_date", "end_date", "end_reason", "other_label", "area", "role")
    readonly_fields = ("label", "role_type", "organization")


class MembershipAdmin(admin.ModelAdmin):
    model = popolo_models.Membership
    list_display = ("person", "label", "start_date", "end_date", "appointed_by")
    list_display_links = ("label",)
    list_select_related = ("person", "appointed_by")
    list_filter = (EndDateNullListFilter,)
    search_fields = ("label", "role", "person__name", "organization__name")
    raw_id_fields = ("person", "organization", "appointed_by")
    readonly_fields = ("person", "organization", "role", "post", "start_date", "end_date", "end_reason")
    fields = readonly_fields + ("appointed_by", "is_appointment_locked", "appointment_note")


class OwnershipAdmin(admin.ModelAdmin):
    model = popolo_models.Ownership
    list_display = ("owner", "percentage", "owned_organization", "start_date", "end_date")
    list_filter = (EndDateNullListFilter,)
    list_display_links = ("percentage",)
    list_select_related = ("owned_organization", "owner_person", "owner_organization")
    search_fields = ("owned_organization__name", "owner_person__name", "owner_organization__name")
    raw_id_fields = ("owned_organization", "owner_organization", "owner_person")
    fields = (
        "owned_organization",
        "owner_person",
        "owner_organization",
        "percentage",
        "start_date",
        "end_date",
        "end_reason",
    )


class IdentifiersInline(GenericTabularInline):
    model = popolo_models.Identifier
    extra = 0
    max_num = 5


class OriginalEducationInline(admin.TabularInline):
    model = popolo_models.OriginalEducationLevel
    show_change_link = True
    extra = 0
    max_num = 10
    readonly_fields = ("name",)

    def has_add_permission(self, request, obj=None):
        return False


class EducationLevelAdmin(admin.ModelAdmin):
    model = popolo_models.EducationLevel
    list_display = ("name",)
    inlines = (IdentifiersInline, OriginalEducationInline)


class OriginalEducationLevelAdmin(admin.ModelAdmin):
    model = popolo_models.OriginalEducationLevel
    list_display = ("name", "normalized_education_level")
    list_filter = ("normalized_education_level",)
    search_fields = ("name", "normalized_education_level__name")
    formfield_overrides = {models.CharField: {"widget": TextInput(attrs={"size": "120"})}}


class OriginalProfessionInline(admin.TabularInline):
    model = popolo_models.OriginalProfession
    show_change_link = True
    extra = 0
    max_num = 10
    readonly_fields = ("name",)

    def has_add_permission(self, request, obj=None):
        return False


class ProfessionAdmin(admin.ModelAdmin):
    model = popolo_models.Profession
    list_display = ("name",)
    inlines = (IdentifiersInline, OriginalProfessionInline)


class OriginalProfessionAdmin(admin.ModelAdmin):
    model = popolo_models.OriginalProfession
    list_display = ("name", "normalized_profession")
    list_filter = ("normalized_profession",)
    search_fields = ("name", "normalized_profession__name")
    formfield_overrides = {models.CharField: {"widget": TextInput(attrs={"size": "120"})}}


class AreaAdmin(admin.ModelAdmin):
    model = popolo_models.Area
    list_display = ("name", "identifier", "classification", "inhabitants", "start_date", "end_date")
    fields = (
        "name", "identifier", "classification", "istat_classification",
        "start_date", "end_date", ("gps_lat", "gps_lon"), "geometry",
    )
    readonly_fields = ("gps_lat", "gps_lon", )
    list_filter = ("classification", "istat_classification")
    search_fields = ("name", "identifier", "identifiers__identifier")

    formfield_overrides = {
        MultiPolygonField: {"widget": forms.OSMWidget(attrs={"map_width": 600, "map_height": 400})}
    }


class PersonAdmin(admin.ModelAdmin):
    model = popolo_models.Person
    list_display = ("name", "birth_date", "birth_location")
    search_fields = ("name", "identifiers__identifier")
    exclude = ("original_profession", "original_education_level", "birth_location_area")


class OrganizationAdmin(admin.ModelAdmin):
    model = popolo_models.Organization
    list_display = ("name", "start_date")
    search_fields = ("name", "identifiers__identifier")
    ordering = ['name', ]
    exclude = ("area", "parent", "new_orgs")
    readonly_fields = fields = (
        "name",
        "start_date",
        "end_date",
        "end_reason",
        "identifier",
        "classification",
        "thematic_classification",
        "abstract",
        "description",
        "image",
    )


class OrganizationRelationshipAdmin(admin.ModelAdmin):
    model = popolo_models.OrganizationRelationship
    list_display = ("source_organization", "dest_organization", "weight")
    search_fields = ("source_organization__name", "dest_organization__name")
    raw_id_fields = ("source_organization", "dest_organization")
    list_filter = ("classification",)


def register():
    """Register all the admin classes. """
    for model_class, admin_class in {
        (popolo_models.Area, AreaAdmin),
        (popolo_models.KeyEvent, KeyEventAdmin),
        (popolo_models.Person, PersonAdmin),
        (popolo_models.Organization, OrganizationAdmin),
        (popolo_models.RoleType, RoleTypeAdmin),
        (popolo_models.Post, PostAdmin),
        (popolo_models.Membership, MembershipAdmin),
        (popolo_models.Ownership, OwnershipAdmin),
        (popolo_models.Classification, ClassificationAdmin),
        (popolo_models.EducationLevel, EducationLevelAdmin),
        (popolo_models.OriginalEducationLevel, OriginalEducationLevelAdmin),
        (popolo_models.Profession, ProfessionAdmin),
        (popolo_models.OriginalProfession, OriginalProfessionAdmin),
        (popolo_models.OrganizationRelationship, OrganizationRelationshipAdmin),
    }:
        admin.site.register(model_class, admin_class)

    admin.site.register(popolo_models.Language)
