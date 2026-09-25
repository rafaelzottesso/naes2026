from urllib.parse import urlencode

from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def pagination_query(context, **kwargs):
    """Preserve the current query string while replacing pagination values."""
    request = context['request']
    query_params = request.GET.copy()

    for key, value in kwargs.items():
        query_params[key] = value

    query_string = urlencode(query_params, doseq=True)
    return f'?{query_string}' if query_string else ''


@register.simple_tag(takes_context=True)
def pagination_page_range(context):
    paginator = context['paginator']
    current_page = context['page_obj'].number
    return paginator.get_elided_page_range(
        current_page,
        on_each_side=1,
        on_ends=1,
    )
