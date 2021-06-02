from django.urls import include, path
from django.conf.urls import url
from . import views

app_name = 'action'

urlpatterns = [
  path('join_us', views.join_us, name='join_us'),
  path('', views.index, name='index'),
  path('report_results/date/<str:regid>/<str:date>/', views.translate_maplink, name='report_date'),
  path('report_results/', views.overview_by_name, name='overview_by_name'),
  path('report_results/', views.overview_by_name, name='overview'),
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
  path('location-autocomplete/', views.LocationAutocomplete.as_view(), name='location-autocomplete'),
  path('organization-autocomplete/', views.OrganizationAutocomplete.as_view(), name='organization-autocomplete'),
  path('start', views.start_view_handler, name='start'),
]
