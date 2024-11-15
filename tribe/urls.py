from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from . import views

app_name = 'tribe'

urlpatterns = [
    path("", views.index, name="index" ),
    path("revent/", views.index, name="revent" ),
    path("revent/add/", views.ReventCreateView.as_view(), name="revent-add"),
    path("revent/<int:pk>/", views.ReventUpdateView.as_view(), name="revent-update"),
    path("revent/<int:pk>/delete/", views.ReventDeleteView.as_view(), name="revent-delete"),
    path("revent/<int:pk>/notes/", views.ReventNoteListView.as_view(), name="reventnote-list"),
    path("revent/<int:pk>/note/add/", views.ReventNoteCreateView.as_view(), name="reventnote-add"),
    path("revent/note/<int:pk>", views.ReventNoteUpdateView.as_view(), name="reventnote-update"),
    path("revent/note/<int:pk>/delete/", views.ReventNoteDeleteView.as_view(), name="reventnote-delete"),
    path("revent/<int:pk>/roles/", views.RoleListView.as_view(), name="role-list"),
    path("revent/<int:pk>/role/add/", views.RoleCreateView.as_view(), name="role-add"),
    path("revent/role/<int:pk>", views.RoleUpdateView.as_view(), name="role-update"),
    path("revent/role/<int:pk>/delete/", views.RoleDeleteView.as_view(), name="role-delete"),
    path("revent/<int:pk>/contacts/", views.ContactInfoListView.as_view(), name="contactinfo-list"),
    path("revent/<int:pk>/contact/add/", views.ContactInfoCreateView.as_view(), name="contactinfo-add"),
    path("revent/contact/<int:pk>", views.ContactInfoUpdateView.as_view(), name="contactinfo-update"),
    path("revent/contact/<int:pk>/delete/", views.ContactInfoDeleteView.as_view(), name="contactinfo-delete"),
    #path('person/<int:reventid>/', views.Person.as_view(), name='person'),
]
