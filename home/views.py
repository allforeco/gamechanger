from django.shortcuts import render
from django.template import loader

# Create your views here.
from django.http import HttpResponse

def index(request):
  context = { 'latest_record_list': None }
  template = loader.get_template('action/index.html')
  return HttpResponse(template.render(context, request))

#def favicon(request):
#  image_data = open("static/favicon.ico", "rb").read()
#  return HttpResponse(image_data, content_type="image/png")