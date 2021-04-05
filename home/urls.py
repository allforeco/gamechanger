from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
  path('', lambda x: redirect('action/home'), name='index'),
]
