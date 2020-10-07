from django.urls import path

from . import views

app_name = 'action'

urlpatterns = [
  path('', views.index, name='index'),
  path('report_results/<str:reg_id>/', views.overview, name='overview'),
  path('report_results/date/<str:reg_id>/', views.report_results, name='report_results'),
  path('report_results/date/<str:reg_id>/<str:date>/', views.report_date, name='report_date'),
]
