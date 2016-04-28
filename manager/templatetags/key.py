from django import template
register = template.Library()

@register.filter
def key(Dict, i):
    return Dict[i]
