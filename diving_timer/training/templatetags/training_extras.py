from django import template

from training import utils


register = template.Library()


@register.filter
def format_duration(value: int) -> str:
    """Format duration in seconds for a template."""
    return utils.format_duration(value)
