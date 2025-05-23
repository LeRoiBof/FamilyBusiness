from datetime import date
from django import template

register = template.Library()

@register.filter
def days_since(value):
    if not value:
        return ""
    try:
        return (date.today() - value).days
    except Exception:
        return ""
