from django.urls import path
from .views import RobotsTxtView

urlpatterns = [
    path("robots.txt", RobotsTxtView.as_view(content_type="text/plain"), name="robots"),
]