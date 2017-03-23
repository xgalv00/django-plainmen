from __future__ import unicode_literals

from django.db import models

from plainmenu.models import AbstractMenu, AbstractMenuItem


class Menu(AbstractMenu):
    test_field = models.CharField(max_length=10, blank=True)


class MenuItem(AbstractMenuItem):
    test_field = models.CharField(max_length=10, blank=True)
