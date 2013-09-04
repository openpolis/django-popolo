from popolo.views import OrganizationDetailView, PersonDetailView, MembershipDetailView, PostDetailView

__author__ = 'guglielmo'
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # organization
    url(r'^person/(?P<slug>[-\w]+)/$', PersonDetailView.as_view(), name='person-detail'),
    url(r'^organization/(?P<slug>[-\w]+)/$', OrganizationDetailView.as_view(), name='organization-detail'),
    url(r'^membership/(?P<slug>[-\w]+)/$', MembershipDetailView.as_view(), name='membership-detail'),
    url(r'^post/(?P<slug>[-\w]+)/$', PostDetailView.as_view(), name='post-detail'),
)

