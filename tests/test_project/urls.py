from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.views.generic import ListView

from plainmenu.models import Menu


urlpatterns = [
    url(r'^$', ListView.as_view(template_name='index.html', model=Menu)),
    url(r'^admin/', admin.site.urls),
]
