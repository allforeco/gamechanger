from django.urls import include, path
from django.conf.urls import url
from . import views

app_name = 'action'

urlpatterns = [
  path('join_us', views.join_us, name='join_us'),
  path('', views.index, name='index'),
  path('report_results/<str:regid>', views.overview),
  path('report_results/<str:regid>/', views.overview, name='overview'),
  path('report_results/date/<str:regid>', views.report_results),
  path('report_results/date/<str:regid>/', views.report_results, name='report_results'),
  path('report_results/date/<str:regid>/<str:date>', views.report_date),
  path('report_results/date/<str:regid>/<str:date>/', views.report_date, name='report_date'),
  path('upload_reg', views.upload_reg),
  path('upload_reg/', views.upload_reg, name='upload_reg'),
  path('upload_reg/post', views.upload_post, name='upload_post'),
  path('download_upd', views.download_upd),
  path('download_upd/', views.download_upd, name='download_reg'),
  path('download_upd/post', views.download_post, name='download_post'),
  path('accounts/', include('django.contrib.auth.urls')),
  #path('location/create', views.location_create, name='location_create'),
  #path('location/<int:pk>/update', views.location_update, name='location_update'),
  path('gathering/create', views.GatheringCreate.as_view(), name='gathering_create'),
  path('gathering/search', views.GatheringSearch.as_view(), name='gathering_search'),
  #path('home', views.home_view, name='home'),
  path('home', views.HomeView.as_view(), name='home'),
  #url(r'^location-autocomplete/$', views.LocationAutocomplete.as_view(), name='location-autocomplete'),
  path('location-autocomplete/', views.LocationAutocomplete.as_view(), name='location-autocomplete'),
]
