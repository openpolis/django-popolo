from popolo.views import OrganizationDetailView, PersonDetailView

__author__ = 'guglielmo'
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # organization
    url(r'^person/(?P<slug>[-\w]+)/$', PersonDetailView.as_view(), name='person-detail'),
    url(r'^organization/(?P<slug>[-\w]+)/$', OrganizationDetailView.as_view(), name='organization-detail'),
)

