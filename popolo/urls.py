from popolo.views import OrganizationDetailView, PersonDetailView, \
    MembershipDetailView, PostDetailView, ElectoralEventDetailView, \
    ElectoralResultDetailView, AreaDetailView
from django.conf.urls import url

__author__ = 'guglielmo'

urlpatterns = [
    url(r'^person/(?P<slug>[-\w]+)/$', PersonDetailView.as_view(),
        name='person-detail'),
    url(r'^organization/(?P<slug>[-\w]+)/$', OrganizationDetailView.as_view(),
        name='organization-detail'),
    url(r'^membership/(?P<slug>[-\w]+)/$', MembershipDetailView.as_view(),
        name='membership-detail'),
    url(r'^post/(?P<slug>[-\w]+)/$', PostDetailView.as_view(),
        name='post-detail'),
    url(r'^electoral-event/(?P<slug>[-\w]+)/$', ElectoralEventDetailView.as_view(),
        name='electoral-event-detail'),
    url(r'^electoral-result/(?P<slug>[-\w]+)/$', ElectoralResultDetailView.as_view(),
        name='electoral-result-detail'),
    url(r'^area/(?P<slug>[-\w]+)/$', AreaDetailView.as_view(),
        name='area-detail'),
]
