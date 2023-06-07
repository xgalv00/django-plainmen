from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

import swapper

from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import admin
from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters

Menu = swapper.load_model('plainmenu', 'Menu')
MenuItem = swapper.load_model('plainmenu', 'MenuItem')
Group = swapper.load_model('plainmenu', 'Group')

_menu_prefix = '{}_{}'.format(Menu._meta.app_label, Menu._meta.model_name)
_menuitem_prefix = '{}_{}'.format(MenuItem._meta.app_label, MenuItem._meta.model_name)
_group_prefix = '{}_{}'.format(Group._meta.app_label, Group._meta.model_name)


class MenuItemRedirectView(RedirectView):
    name = None

    def get_redirect_url(self, *args, **kwargs):
        if args:
            item = get_object_or_404(MenuItem, pk=args[0])
            reverse_args = (item.menu.pk, item.pk)
        else:
            reverse_args = ()

        return reverse('admin:{}'.format(self.name), args=reverse_args)


class MenuItemAdmin(TreeAdmin):
    exclude = ('path', 'depth', 'numchild', '_position')
    form = movenodeform_factory(MenuItem)
    list_display = ('__str__', 'link', 'link_target')
    delete_confirmation_template = 'admin/plainmenu/menuitem/delete_confirmation.html'
    change_form_template = 'admin/plainmenu/menuitem/change_form.html'

    def get_queryset(self, request):
        queryset = super(MenuItemAdmin, self).get_queryset(request)

        if hasattr(request, '_current_tree_id'):
            queryset = queryset.filter(menu__pk=request._current_tree_id)

        return queryset

    @staticmethod
    def link_target(obj):
        return MenuItem.TARGET_CHOICES[obj.target]

    def delete_view(self, request, menu_id, object_id, extra_context=None):
        request._current_tree_id = menu_id
        extra_context = extra_context or {}
        extra_context['menu'] = get_object_or_404(Menu, pk=menu_id)
        extra_context['menu_opts'] = Menu._meta

        return super(MenuItemAdmin, self).delete_view(request, object_id, extra_context)

    def changeform_view(self, request, menu_id=None, object_id=None, form_url=None, extra_context=None):
        if object_id and not menu_id:
            menu_id = object_id
            object_id = None

        request._current_tree_id = menu_id
        extra_context = extra_context or {}
        extra_context['menu'] = get_object_or_404(Menu, pk=menu_id)
        extra_context['menu_opts'] = Menu._meta

        return super(MenuItemAdmin, self).changeform_view(
            request,
            object_id,
            form_url or '',
            extra_context
        )

    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(MenuItemAdmin, self).get_form(request, obj, **kwargs)

        class MyForm(ModelForm):
            HIDDEN_FIELDS = {'sort_weight', 'menu', '_position'}

            def __init__(self, *args, **kwargs):
                instance = kwargs.get('instance')
                initial = kwargs.get('initial', {})
                initial.update({
                    'menu': getattr(request, '_current_tree_id', None),
                    '_position': 'sorted-child',
                    'sort_weight': instance.sort_weight if instance else 2**16
                })
                kwargs['initial'] = initial

                super(MyForm, self).__init__(*args, **kwargs)

                for field in self.HIDDEN_FIELDS:
                    self.fields[field].widget = forms.HiddenInput()

                self.fields['_ref_node_id'].label = 'Child of'


            @classmethod
            def mk_dropdown_tree(cls, model, for_node=None):
                """ Creates a tree-like list of choices """

                menu_id = getattr(request, '_current_tree_id', None)
                queryset = model.get_root_nodes()

                if menu_id:
                    queryset = queryset.filter(menu__id=menu_id)

                options = [(0, _('-- root --'))]
                for node in queryset:
                    cls.add_subtree(for_node, node, options)
                return options

        return MyForm

    def response_post_save_add(self, request, obj):
        opts = self.model._meta
        if self.has_change_permission(request, None):
            post_url = reverse('admin:%s_menu_change' % (opts.app_label,),
                               current_app=self.admin_site.name, args=[obj.menu.pk])
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, post_url)
        else:
            post_url = reverse('admin:index', current_app=self.admin_site.name)
        return HttpResponseRedirect(post_url)

    response_post_save_change = response_post_save_add


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    change_form_template = 'admin/plainmenu/menu_change.html'
    list_display = ('identifier', 'name', 'group')
    list_filter = ('group',)
    ordering = ('group', 'identifier')

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.menu_admin = MenuItemAdmin(MenuItem, admin.site)

    def get_urls(self):
        from django.views.i18n import JavaScriptCatalog

        return [
            url(r'^.+/move/$', self.admin_site.admin_view(self.menu_admin.move_node), ),
            url(r'^.+/jsi18n/$', JavaScriptCatalog.as_view(), {'packages': ('treebeard',)}),
            url(r'^(\d+)/items/', include(self.menu_admin.get_urls())),
            url(r'^items/change/(.+)/', MenuItemRedirectView.as_view(name='%s_change' % _menuitem_prefix), name='%s_change' % _menuitem_prefix),
            url(r'^items/delete/(.+)/', MenuItemRedirectView.as_view(name='%s_delete' % _menuitem_prefix), name='%s_delete' % _menuitem_prefix),
            url(r'^items/changelist/', MenuItemRedirectView.as_view(name='%s_changelist' % _menu_prefix), name='%s_changelist' % _menuitem_prefix)
        ] + super(MenuAdmin, self).get_urls()

    def change_view(self, request, object_id, form_url=u'', extra_context=None):
        request._current_tree_id = object_id
        extra_context = extra_context or {}
        extra_context['cl'] = self.get_chagelist_instance(request)
        extra_context['item_opts'] = MenuItem._meta

        return super(MenuAdmin, self).change_view(request, object_id, form_url, extra_context)

    def get_chagelist_instance(self, request):
        ChangeList = self.menu_admin.get_changelist(request)

        class MyChangeList(ChangeList):
            def url_for_result(self, result):
                return reverse(
                    'admin:{}_{}_change'.format(self.opts.app_label, self.opts.model_name),
                    args=(result.menu.pk, admin.utils.quote(result.pk)),
                    current_app=self.model_admin.admin_site.name
                )

            def get_filters(self, request):
                return ([], False, {}, False, False)

        list_display = self.menu_admin.get_list_display(request)
        sortable_by = self.menu_admin.get_sortable_by(request)

        cl = MyChangeList(
            request,
            self.menu_admin.model,
            list_display,
            self.menu_admin.get_list_display_links(request, list_display),
            self.menu_admin.get_list_filter(request),
            self.menu_admin.date_hierarchy,
            self.menu_admin.get_search_fields(request),
            self.menu_admin.get_list_select_related(request),
            self.menu_admin.list_per_page,
            self.menu_admin.list_max_show_all,
            self.menu_admin.list_editable,
            self.menu_admin,
            sortable_by,
        )

        cl.formset = None

        return cl


admin.site.register(Group)
