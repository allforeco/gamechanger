from django.urls import include, path, re_path
from . import views

app_name = 'twiff2'

urlpatterns = [
  path('run', views.run_view, name='run'),
]
