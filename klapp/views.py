#   Gamechanger Klapp Views
#   Copyright (C) 2023 Jan Lindblad
# 
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from django.shortcuts import render
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from .responder import Responder
import logging

# TODO: Add LoginRequiredMixin
@csrf_exempt
def botchat_view(request):
  if request.method != "POST":
    return HttpResponseNotAllowed(permitted_methods=['POST'])

  responder = Responder(request.POST)
  user = responder.get_user()
  klapp = responder.get_self()

  responder.quote_message(
    quote = responder.get_message(),
    quote_from = user,
    quote_to = klapp)

  try:
    responses = responder.get_response_actions()
    return HttpResponse(JsonResponse(responses))
  except:
    logging.exception("Responder raised an exception")
    problem_response = JsonResponse(
      {'ok':[{
        'operation':'send', 
        'to': user.user_handle,
        'message': "Hmm. @$@!&!??? Oops. (BCVW)",
      }]})
    return HttpResponse(problem_response)