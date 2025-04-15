from django.shortcuts import render
from django.views.generic import TemplateView

class RobotsTxtView(TemplateView):
    template_name = "robots.txt"