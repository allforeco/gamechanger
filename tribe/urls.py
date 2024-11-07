from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from . import views

app_name = 'tribe'

urlpatterns = [
    path("", views.index, name="index" ),
    path("revent/", views.index, name="revent" ),
    path("revent/add/", views.ReventCreateView.as_view(), name="revent-add"),
    path("revent/<int:pk>/detail/", views.ReventDetailView.as_view(), name="revent-detail"),
    path("revent/<int:pk>/", views.ReventUpdateView.as_view(), name="revent-update"),
    path("revent/<int:pk>/delete/", views.ReventDeleteView.as_view(), name="revent-delete"),
    path("revent/<int:pk>/notes/", views.ReventNoteListView.as_view(), name="reventnote-list"),
    path("revent/<int:pk>/note/add/", views.ReventNoteCreateView.as_view(), name="reventnote-add"),
    path("revent/note/<int:pk>", views.ReventNoteUpdateView.as_view(), name="reventnote-update"),
    path("revent/note/<int:pk>/delete/", views.ReventNoteDeleteView.as_view(), name="reventnote-delete"),
    #path("revent/<str:pw>/", views.ReventCreateView.as_view(), name="revent-detail"),
    #path('person/<int:reventid>/', views.Person.as_view(), name='person'),
]
