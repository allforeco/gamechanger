from django.urls import include, path, re_path
from . import views

app_name = 'klapp'

urlpatterns = [
  #path('botchat', views.ChatView.as_view(), name='botchat'),
  path('botchat', views.botchat_view, name='botchat'),
]
