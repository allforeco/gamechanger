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
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.http import JsonResponse
from django import forms

# TODO: Add LoginRequiredMixin
class ChatView(FormView):
  class ChatForm(forms.Form):
    username = forms.CharField()
    displayname = forms.CharField()

  template_name = 'klapp/chat.html'
  success_url = '/klapp/chat'
  form_class = ChatForm

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
      return super(ChatView, self).dispatch(*args, **kwargs)

  def form_valid(self, form):
    print(f"KCHV ")
    # Call super to let it do its work, but we compose the response
    super().form_valid(form)
    # We got valid data, let's respond
    response = JsonResponse(
      {'ok':[{
        'operation':'send', 
        'to': form.cleaned_data.get('username'), 
        'message': f"Hej {form.cleaned_data.get('displayname')}!"
      }]})
    return response
    #return super().form_valid(form)
