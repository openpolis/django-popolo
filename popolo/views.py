from django.views.generic import DetailView
from popolo.models import Organization, Person, Membership, Post


class PersonDetailView(DetailView):
    model = Person
    context_object_name = 'person'
    template_name='person_detail.html'

class OrganizationDetailView(DetailView):
    model = Organization
    context_object_name = 'organization'
    template_name='organization_detail.html'


class MembershipDetailView(DetailView):
    model = Membership
    context_object_name = 'membership'
    template_name='membership_detail.html'


class PostDetailView(DetailView):
    model = Post
    context_object_name = 'post'
    template_name='post_detail.html'