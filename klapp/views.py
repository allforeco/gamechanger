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
POST_NEW_USER_ID = 4

@csrf_exempt
def botchat_view(request):
  if request.method != "POST":
    return HttpResponseNotAllowed(permitted_methods=['POST'])

  params = request.POST
  username = params.get('username')
  display_name = params.get('display_name')
  users_message = params.get('message')
  lang = params.get('lang')
  print(f"botchat_view: {request.get_host()} {username} {display_name} {lang}")

  new_user_flag = False
  user = Actor.objects.filter(user_handle=username)
  if user.exists():
    user = user.first()
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
    curr_post_id = get_json_setting(conv.settings, 'post')
    print(f"reply_to_user: current post '{curr_post_id}'")
  except:
    print(f"reply_to_user: could not find conversation {conv.settings}")
    curr_post_id = None

  if not curr_post_id: # New/blank user
    curr_post_id = POST_NEW_USER_ID
    command = None

  print(f"reply_to_user: post_id = {curr_post_id}")
  curr_post = Post.objects.get(pk=curr_post_id)

  curr_post_children = curr_post.children.all()
  print(f"reply_to_user: post.children = {curr_post_children}")
  #curr_post_settings = json.loads(curr_post.settings)
  #print(f"reply_to_user: post.settings = {curr_post_settings}")

  history_commands = get_json_setting(conv.settings, 'history')
  post_specfic_commands = {}
  child_commands = {c.name.lower():c.pk for c in curr_post.children.all()}
  admin_commands = {".uppdatera":lambda:post_update(),".kommentera":lambda:post_add_comment()}
  commands = {**history_commands,**post_specfic_commands,**child_commands,**admin_commands}
  print(f'reply_to_user(): commands = {commands.keys()}')

  if command:
    if command not in commands.keys():
      print(f'reply_to_user: got unknown command "{command}"')
      return "Jag förstod inte riktigt. Här är de svar jag förstår just nu: " + ", ".join(list(commands.keys()))
    else:
      if isinstance(commands[command], int):
        new_post_id = commands[command]
        print(f'reply_to_user: got command "{command}" -> post {new_post_id}')
      else:
        print(f'reply_to_user: calling special command "{commands[command]}"')
        new_post_id = commands[command]()
        print(f'reply_to_user: -> post {new_post_id}')
  else:
    new_post_id = curr_post_id
  post = Post.objects.get(pk=new_post_id)
  message = post.name + "\n\n" + post.body
  conv.settings = json.dumps({'post': post.pk, 'history':{**get_json_setting(conv.settings, 'history'),**child_commands}})
  conv.save()

  return message

# historia .uppdatera .visa

def get_json_setting(settings,key):
  try:
    #print(f"get_json_setting: {settings} {key}")
    #print(f"get_json_setting: {json.loads(settings)}")
    return json.loads(settings).get(key,{})
  except:
    return {}

def post_update():
  print("post_update() called")
  return 6

def post_add_comment():
  print("post_add_comment() called")
  return 6

def get_command(msg):
  #print(f"get_command({msg})")
  msg = msg.lower()
  msg = strip_tags(msg)
  msg = msg.strip()
  msg = " ".join(msg.split()[1:])
  #print(f"-> '{msg}'")
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
