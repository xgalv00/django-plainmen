from __future__ import absolute_import
from django import template

register = template.Library()

@register.inclusion_tag('plainmenu/menu.html', takes_context=True)
def show_menu(context, menu_name):
    from plainmenu.models import Menu

    if isinstance(menu_name, Menu):
        menu = menu_name
    else:
        try:
            menu = Menu.objects.get(identifier=menu_name)
        except Menu.DoesNotExist:
            return context

    context['items'] = menu.get_items()
    return context
