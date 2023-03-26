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
from .models import Actor, Quote, Conversation

# TODO: Add LoginRequiredMixin

@csrf_exempt
def botchat_view(request):
  if request.method != "POST":
    return HttpResponseNotAllowed(permitted_methods=['POST'])

  params = request.POST
  username = params.get('username')
  print(f"botchat_view: {request.get_host()} {username} {params}")

  new_user_flag = False
  user = Actor.objects.filter(user_handle=username)
  if user.exists():
    user = user[0]
  else:
    # Unknown/new user
    new_user_flag = True
    print(f"botchat_view: New user {username}. Welcome!")
    
    conversation = Conversation(settings = {})
    conversation.save()

    user = Actor(
      user_handle = username,
      conversation = conversation,
      #history = None,
    )
    user.save()

  klapp = Actor.objects.get(pk=7) # Klapp is actor #7

  new_quote = Quote(
    quote = params.get('message'),
    quote_from = user,
    quote_to = klapp)
  new_quote.save()

  message = f"Hej {params.get('display_name')}!" + ("\Trevligt att träffas!" if new_user_flag else "")

  new_quote = Quote(
    quote = message,
    quote_from = klapp,
    quote_to = user)
  new_quote.save()

  response = JsonResponse(
    {'ok':[{
      'operation':'send', 
      'to': username,
      'message': message,
    }]})
  return HttpResponse(response)




from django import forms
from django.utils.decorators import method_decorator

class ChatView(FormView):
  class ChatForm(forms.Form):
    username = forms.CharField()
    displayname = forms.CharField()

  template_name = 'klapp/chat.html'
  success_url = '/klapp/chat'
  form_class = ChatForm

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
      print(f"KCHV dispatch()")
      print(f"KCHV {args} {kwargs}")
      print(f"KCHV args.method")
      #if isinstance(args, HttpRequest):
      #  request = args
      #  if request.method == "POST":
      #    self.chat_respond(request)
      return super(ChatView, self).dispatch(*args, **kwargs)

  def form_valid(self, form):
    print(f"KCHV form_valid()")
    # Call super to let it do its work, but we compose the response
    super().form_valid(form)
    # We got valid data, let's respond
    return self.chat_respond(form)
    #return super().form_valid(form)

  def chat_respond(self, form):
    response = JsonResponse(
      {'ok':[{
        'operation':'send', 
        'to': form.cleaned_data.get('username'), 
        'message': f"Hej {form.cleaned_data.get('display_name')}!"
      }]})
    return response
