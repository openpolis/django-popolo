from django.views.generic import DetailView
from popolo.models import Organization, Person, Membership, Post, KeyEvent, Area


class PersonDetailView(DetailView):
    model = Person
    context_object_name = "person"
    template_name = "person_detail.html"


class OrganizationDetailView(DetailView):
    model = Organization
    context_object_name = "organization"
    template_name = "organization_detail.html"


class MembershipDetailView(DetailView):
    model = Membership
    context_object_name = "membership"
    template_name = "membership_detail.html"


class PostDetailView(DetailView):
    model = Post
    context_object_name = "post"
    template_name = "post_detail.html"


class KeyEventDetailView(DetailView):
    model = KeyEvent
    context_object_name = "event"
    template_name = "electoral_event_detail.html"


class AreaDetailView(DetailView):
    model = Area
    context_object_name = "area"
    template_name = "area_detail.html"
