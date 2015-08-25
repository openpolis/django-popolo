from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from popolo import models
from .behaviors import admin as generics



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
    inlines = generics.BASE_INLINES

class OrganizationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'gender', 'founding_date', 'dissolution_date')
        }),
        ('Biography', {
            'classes': ('collapse',),
            'fields': ('summary', 'image', 'description')
        }),
        ('Honorifics', {
            'classes': ('collapse',),
            'fields': ('honorific_prefix', 'honorific_suffix')
        }),
        ('Special Names', {
            'classes': ('collapse',),
            'fields': ('area', 'given_name', 'additional_name','patronymic_name','sort_name')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('classification','start_date', 'end_date')
        }),
    )
    inlines = generics.BASE_INLINES


admin.site.register(models.Person,PersonAdmin)
admin.site.register(models.Organization,OrganizationAdmin)
