from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

def validate_percentage(value):
    if value < 0 or value > 1.:
        raise ValidationError(
            _('%(value)s is not a percentage'),
            params={'value': value}
        )