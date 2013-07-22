from django.views.generic import DetailView
from popolo.models import Organization, Person


class PersonDetailView(DetailView):
    model = Person
    context_object_name = 'person'
    template_name='person_detail.html'

class OrganizationDetailView(DetailView):
    model = Organization
    context_object_name = 'organization'
    template_name='organization_detail.html'
