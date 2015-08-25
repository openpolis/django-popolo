from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from popolo import models
from .behaviors import admin as generics


class MembershipInline(admin.StackedInline):
    extra = 0
    model = models.Membership

class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'gender', 'birth_date', 'death_date')
        }),
        ('Biography', {
            'classes': ('collapse',),
            'fields': ('summary', 'image', 'biography')
        }),
        ('Honorifics', {
            'classes': ('collapse',),
            'fields': ('honorific_prefix', 'honorific_suffix')
        }),
        ('Demography', {
            'classes': ('collapse',),
            'fields': ('national_identity',)
        }),
        ('Special Names', {
            'classes': ('collapse',),
            'fields': ('family_name', 'given_name', 'additional_name','patronymic_name','sort_name')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('start_date', 'end_date')
        }),
    )
    inlines = generics.BASE_INLINES + [MembershipInline]

class OrganizationMembersInline(MembershipInline):
    fk_name = 'organization'
class OrganizationOnBehalfInline(MembershipInline):
    fk_name = 'on_behalf_of'


class PostAdmin(admin.ModelAdmin):
    model = models.Post
    fieldsets = (
        (None, {
            'fields': ('label','role', 'start_date', 'end_date')
        }),
        ('Details', {
            'classes': ('collapse',),
            'fields': ('other_label', 'area', 'organization','membership')
        }),
    )
    inlines = [
            generics.LinkAdmin,generics.ContactDetailAdmin,generics.SourceAdmin
        ]

class OrganizationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'founding_date', 'dissolution_date')
        }),
        ('Details', {
            'classes': ('collapse',),
            'fields': ('summary', 'image', 'description')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('classification','start_date', 'end_date')
        }),
    )
    inlines = generics.BASE_INLINES + [OrganizationMembersInline,OrganizationOnBehalfInline]


admin.site.register(models.Post,PostAdmin)
admin.site.register(models.Person,PersonAdmin)
admin.site.register(models.Organization,OrganizationAdmin)
