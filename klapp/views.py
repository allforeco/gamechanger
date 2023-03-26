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
from .models import Actor, Quote, Post, Conversation
from html.parser import HTMLParser
from io import StringIO
import json

# TODO: Add LoginRequiredMixin

KLAPP_ACTOR_ID = 7
POST_ROOT_ID = 4

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
    print(f"botchat_view: New user {username}. Welcome!")
    
    conversation = Conversation(settings = {})
    conversation.save()

    user = Actor(
      user_handle = username,
      conversation = conversation,
      #history = None,
    )
    user.save()

  klapp = Actor.objects.get(pk=KLAPP_ACTOR_ID)

  users_message = params.get('message')

  new_quote = Quote(
    quote = users_message,
    quote_from = user,
    quote_to = klapp)
  new_quote.save()

  message = reply_to_user(user, users_message)

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


def reply_to_user(user, msg):
  command = get_command(msg)
  if command:
    print(f"reply_to_user: Got command '{command}'")

  conv = user.conversation
  try:
    conv_settings = json.loads(conv.settings)
    old_post_id = conv_settings['post']
  except:
    print(f"reply_to_user: could not find conversation {conv.settings}")
    old_post_id = None

  if not old_post_id: # New/blank user
    old_post_id = POST_ROOT_ID
    command = ''

  print(f"reply_to_user: post_id = {old_post_id}")
  old_post = Post.objects.get(pk=old_post_id)
  print(f"reply_to_user: post.settings = {old_post.settings}")
  old_post_settings = json.loads(old_post.settings)
  responses = old_post_settings['responses']
  if command:
    if command not in responses:
      print(f'reply_to_user: got unknown command "{command}"')
      return "Jag förstod inte riktigt. Här är de svar jag förstår just nu: " + ", ".join(list(responses.keys()))
    else:
      print(f'reply_to_user: got command "{command}"')
      new_post_id = responses[command]
  else:
    new_post_id = old_post_id
  post = Post.objects.get(pk=new_post_id)
  message = post.name + "\n\n" + post.body
  conv.settings = "{" + f'"post": {post.pk}' + "}"
  conv.save()

  return message

def get_command(msg):
  print(f"get_command({msg})")
  msg = msg.lower()
  msg = strip_tags(msg)
  msg = msg.strip()
  msg = " ".join(msg.split()[1:])
  print(f"-> '{msg}'")
  return msg

# Stolen from https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class MLStripper(HTMLParser):
  def __init__(self):
    super().__init__()
    self.reset()
    self.strict = False
    self.convert_charrefs= True
    self.text = StringIO()
  def handle_data(self, d):
    self.text.write(d)
  def get_data(self):
    return self.text.getvalue()

def strip_tags(html):
  s = MLStripper()
  s.feed(html)
  return s.get_data()
