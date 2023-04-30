"""gamechanger URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('action/', include('action.urls')),
    path('klapp/', include('klapp.urls')),
    path('twiff2/', include('twiff2.urls')),
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
]

handler400 = 'action.views.bad_request'
handler403 = 'action.views.permission_denied'
handler404 = 'action.views.page_not_found'
handler500 = 'action.views.server_error'

#if settings.DEBUG:
#urlpatterns += static('/', document_root='static/')
