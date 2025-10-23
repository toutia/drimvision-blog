from django import template

register = template.Library()

@register.filter
def dictget(d, key):
    """Safely get a key from a dictionary in templates."""
    if isinstance(d, dict):
        return d.get(key, [])
    return []