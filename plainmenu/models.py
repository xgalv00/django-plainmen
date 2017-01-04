from __future__ import unicode_literals

from functools import wraps

from treebeard.mp_tree import MP_Node, get_result_class, MP_ComplexAddMoveHandler

from django.db import models, transaction


def _monkeypatch_treebeard():
    old_newpath = MP_ComplexAddMoveHandler.get_sql_newpath_in_branches
    old_numchild = MP_ComplexAddMoveHandler.get_sql_update_numchild

    @wraps(old_newpath)
    def new_newpath(self, *args, **kwargs):
        sql, vals = old_newpath(self, *args, **kwargs)
        return sql + ' AND menu_id = %s', vals + [self.node.menu_id]

    @wraps(old_numchild)
    def new_numchild(self, *args, **kwargs):
        sql, vals = old_numchild(self, *args, **kwargs)
        return sql + ' AND menu_id = %s', vals + [self.node.menu_id]

    MP_ComplexAddMoveHandler.get_sql_newpath_in_branches = new_newpath
    MP_ComplexAddMoveHandler.get_sql_update_numchild = new_numchild


class Menu(models.Model):
    identifier = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=64)


    def __str__(self):
        return self.name


    def get_items(self):
        return self.menuitem_set.order_by(*MenuItem.node_order_by).filter(depth=1)


class MenuItem(MP_Node):
    node_order_by = ['sort_weight']

    sort_weight = models.PositiveIntegerField()
    title = models.CharField(max_length=64)
    link = models.CharField(max_length=256, blank=True)
    menu = models.ForeignKey(Menu)

    class Meta:
        unique_together = (
            ('path', 'menu'),
        )


    def __str__(self):
        return self.title


    def fix_tree(self, destructive=False):
        for i, item in enumerate(self.get_children()):
            item.sort_order = i
            item.save()

        super(MenuItem, self).fix_tree(destructive)


    @transaction.atomic
    def move(self, target, pos=None):
        original_parent = self.get_parent()

        if self.menu != target.menu:
            target = self

        if self == target:
            pass
        elif 'sibling' in pos:
            target_siblings = list(target.get_siblings())

            if self in target_siblings:
                target_siblings.remove(self)

            target_siblings.insert(target_siblings.index(target), self)

            for i, item in enumerate(target_siblings):
                item.sort_weight = i
                item.save()

        else:
            last_child = target.get_last_child()
            self.sort_weight = last_child.sort_weight + 1 if last_child else 0
            self.save()

        super(MenuItem, self).move(target, pos)

        if original_parent:
            original_parent.fix_tree()


    def get_sorted_pos_queryset(self, siblings, newobj):
        return super(MenuItem, self).get_sorted_pos_queryset(siblings, newobj).filter(
            menu=self.menu
        )


    def get_children(self):
        return super(MenuItem, self).get_children().filter(
            menu=self.menu
        )


    def get_siblings(self):
        return super(MenuItem, self).get_siblings().filter(
            menu=self.menu
        )


    def get_parent(self, update=False):
        """
        :returns: the parent node of the current node object.
            Caches the result in the object itself to help in loops.
        """
        depth = int(len(self.path) / self.steplen)
        if depth <= 1:
            return
        try:
            if update:
                del self._cached_parent_obj
            else:
                return self._cached_parent_obj
        except AttributeError:
            pass
        parentpath = self._get_basepath(self.path, depth - 1)
        self._cached_parent_obj = get_result_class(
            self.__class__
        ).objects.get(
            path=parentpath, menu=self.menu
        )
        return self._cached_parent_obj

MenuItem._meta.get_field('path')._unique = False

_monkeypatch_treebeard()
