from django.views.generic import DetailView
from popolo.models import Organization, Person, Membership, Post, \
    ElectoralEvent, ElectoralResult, Area


class PersonDetailView(DetailView):
    model = Person
    context_object_name = 'person'
    template_name = 'person_detail.html'


class OrganizationDetailView(DetailView):
    model = Organization
    context_object_name = 'organization'
    template_name = 'organization_detail.html'


class MembershipDetailView(DetailView):
    model = Membership
    context_object_name = 'membership'
    template_name = 'membership_detail.html'


class PostDetailView(DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'post_detail.html'


class ElectoralEventDetailView(DetailView):
    model = ElectoralEvent
    context_object_name = 'event'
    template_name = 'electoral_event_detail.html'


class ElectoralResultDetailView(DetailView):
    model = ElectoralResult
    context_object_name = 'result'
    template_name = 'electoral_result_detail.html'


class AreaDetailView(DetailView):
    model = Area
    context_object_name = 'area'
    template_name = 'area_detail.html'
