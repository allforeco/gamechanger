from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from . import views

app_name = 'action'

urlpatterns = [
  path('join_us', views.join_us, name='join_us'),
  path('', views.index, name='index'),
  path('record_results/date/<str:regid>/<str:date>/', views.translate_maplink, name='record_date'),
  path('report_results/date/<str:regid>/<str:date>/', RedirectView.as_view(url=f"/{app_name}/record_results/date/%(regid)s/%(date)s/")),
  path('record_results/', views.overview_by_name, name='overview_by_name'),
  path('record_results/', views.overview_by_name, name='overview'),
  path('report_results/', RedirectView.as_view(url=f"/{app_name}/record_results/")),
  path('geo/<int:locid>/', views.geo_view_handler, name='geo_view'),
  path('geo/<int:locid>/<str:date>', views.geo_date_view_handler, name='geo_date_view'),
  path('geo/invalid/', views.geo_invalid, name='geo_invalid'),
  path('geo/update/', views.geo_update_view, name='geo_update'),
  path('geo/update/post/', views.geo_update_post, name='geo_post'),
  path('geo/search/', views.geo_search, name='geo_search'),
  path('upload_reg', views.upload_reg),
  path('upload_reg/', views.upload_reg, name='upload_reg'),
  path('upload_reg/post', views.upload_post, name='upload_post'),
  path('download_upd', views.download_upd),
  path('download_upd/', views.download_upd, name='download_reg'),
  path('download_upd/post', views.download_post, name='download_post'),
  path('accounts/', include('django.contrib.auth.urls')),
  path('home', views.HomeView.as_view(), name='home'),
  path('geo_new/<int:locid>/', views.geo_view_handler_new, name='geo_view_new'),
  path('tools', views.tools_view_handler, name='tools_view'),
  path('tools/post', views.tools_view_post, name='tools_post'),
  path('tools/<str:result>', views.tools_view_handler, name='tools_result'),
  path('location-autocomplete/', views.LocationAutocomplete.as_view(), name='location-autocomplete'),
  path('organization-autocomplete/', views.OrganizationAutocomplete.as_view(), name='organization-autocomplete'),
  path('start/', views.start_view_handler, name='start'),
  path('start/latest_records', views.latest_records_view, name='latest_records'),
  path('start/latest_reports', RedirectView.as_view(url=f"/{app_name}/start/latest_records")),
  path('locations_list', views.locations_view, name='locations_list'),
  path('start', views.start_view_handler, name='start'),
  path('contacts', views.contacts_view, name='contacts_list'),
  path('start/contacts', views.contacts_view, name='contacts_list'), #TEMP TRANSISTION
  path('contacts/import/<int:option>', views.contacts_import, name='contacts_import'),
  path('organizations/<int:orgid>/', views.organization_view, name='organization_view'),
  path('eventmap_data/', views.eventmap_data_view, name='eventmap_data_view'),
  path('eventmap_data/update_csv', views.eventmap_data, name='eventmap_data'),
  path('report_gathering', views.GatheringReport, name='gathering_report'),
  path('create_gathering', views.GatheringCreate, name='gathering_create'),
]
