from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def query_transform(context, *args):
    request = context['request']
    updated = request.GET.copy()
    for arg in args:
        value = context.get(arg)
        if value is not None:
            updated[arg] = value
    return updated.urlencode()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
