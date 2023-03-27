#   Gamechanger Klapp Responder
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

from .models import Actor, Quote, Post, Conversation
from html.parser import HTMLParser
from io import StringIO
import json

PK_SELF_ACTOR_ID = 7
PK_NEW_USER_POST_ID = 4

class Responder:
  def __init__(self, request):
    self.request = request
    self.curr_post = None
    self.conv = None
    self.commands = None
    self.child_commands = None
    self.command_line = None
    self.message_params = {}
    self.responses = []
    print(f"Responder: {self.get_username()} {self.get_display_name()} {self.get_lang()}")

  def get_username(self):
    return self.request.get('username')

  def get_display_name(self):
    return self.request.get('display_name')

  def get_message(self):
    return self.request.get('message')

  def get_lang(self):
    return self.request.get('lang')

  def get_user(self):
    users = Actor.objects.filter(user_handle=self.get_username())
    if users.exists():
      return users.first()
      #return Actor.objects.get(pk=users.first().pk)
    else:
      # Unknown/new user
      print(f"Responder.get_user: New user {self.get_username()}. Welcome!")
      
      conversation = Conversation(settings = {})
      conversation.save()

      user = Actor(
        user_handle = self.get_username(),
        conversation = conversation,
      )
      user.save()
    return user

  def get_self(self):
    return Actor.objects.get(pk=PK_SELF_ACTOR_ID)

  def quote_message(self, quote, quote_from, quote_to):
    new_quote = Quote(
      quote = quote,
      quote_from = quote_from,
      quote_to = quote_to)
    new_quote.save()

  def get_response_actions(self):
    self.fetch_curr_post()
    self.collect_commands()
    self.parse_inc_message()
    self.handle_post_settings()
    self.execute_command()
    return self.get_responses()

  def fetch_curr_post(self):
    self.conv = self.get_user().conversation
    try:
      curr_post_id = self.get_setting(self.conv.settings, 'post')
      print(f"Responder.fetch_curr_post: post id '{curr_post_id}'")
    except:
      print(f"Responder.fetch_curr_post: could not find conversation {self.conv.settings}")
      curr_post_id = None

    if not curr_post_id: # New conversation
      curr_post_id = PK_NEW_USER_POST_ID
      command = None

    #print(f"Responder.fetch_curr_post: post_id = {curr_post_id}")
    self.curr_post = Post.objects.get(pk=curr_post_id)

  def collect_commands(self):
    curr_post_children = self.curr_post.children.all()
    print(f"Responder.fetch_curr_post: self.post.children = {curr_post_children}")
    history_commands = self.get_setting(self.conv.settings, 'history')
    post_specfic_commands = self.get_setting(self.curr_post.settings, 'actions')
    self.child_commands = {c.name.lower():c.pk for c in self.curr_post.children.all()}
    admin_commands = {".uppdatera":"update",".kommentera":"comment"} # FIXME: Swedish
    self.commands = {**history_commands,**post_specfic_commands,**self.child_commands,**admin_commands}
    print(f'Responder.collect_commands(): commands = {self.commands.keys()}')

  def get_setting(self, settings, key):
    try:
      #print(f"get_json_setting: {settings} {key}")
      #print(f"get_json_setting: {json.loads(settings)}")
      return json.loads(settings).get(key,{})
    except:
      return {}

  def parse_inc_message(self):
    # Stolen from https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    def strip_tags(html):
      s = MLStripper()
      s.feed(html)
      return s.get_data()

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

    #print(f"get_command({msg})")
    msg = strip_tags(self.get_message().lower())
    msg = msg.strip()
    msg = " ".join(msg.split()[1:])
    #print(f"-> '{msg}'")
    self.command_line = msg

  def handle_post_settings(self):
    curr_post_preprocessors = self.get_setting(self.curr_post.settings,'preprocessors') or []
    print(f"Responder.handle_post_settings: post preprocessors = {curr_post_preprocessors}")
    for (precmd, arg) in curr_post_preprocessors:
      if precmd == 'set-command':
        self.command_line = arg
      else:
        print(f"Unknown preprocessor command {precmd}, ignoring")

  def execute_command(self):
    def parse_command(command_line, commands):
      for c in commands:
        if command_line.startswith(c):
          return (c, command_line[len(c):])
      return (None, command_line)

    print(f"Responder.execute_command: command '{self.command_line}'")
    if not self.command_line:
      return self.respond_to_user(self.curr_post_id)
    (command, arg) = parse_command(self.command_line, self.commands)
    if not command:
      print(f'Responder.execute_command: unknown command')
      self.respond_to_user(
        self.get_user(), # FIXME: Swedish
        "Jag förstod inte riktigt. Här är de svar jag förstår just nu: " + ", ".join(list(self.commands.keys())))
    if isinstance(self.commands[command], int):
      self.new_post_to_user(self.commands[command])
      print(f'Responder.execute_command: new post "{command}" -> post {self.commands[command]}')
    elif isinstance(self.commands[command], str):
      print(f'Responder.execute_command: calling special command "{self.commands[command]}"')
      self.process_special_command(self.commands[command], arg)
    else:
      print(f'Responder.execute_command: unknown command type "{self.commands[command]}"')
      self.respond_to_user(
        self.get_user(), # FIXME: Swedish
        "Nu blev jag yr i mössan och förvirrad. Vad hände???")

  def process_special_command(self, command, arg):
    # historia .uppdatera .visa inbox
    if command == "zip":
      print(f"zip {arg} {self.get_user()}")
      user = Actor.objects.get(pk=self.get_user().pk) # Why is this needed??
      user.zip_code = str(arg)
      user.save(update_fields=['zip_code'])
      self.respond_to_user(
        self.get_user(), # FIXME: Swedish
        f"Tack för det! {self.get_user().zip_code}, noterat.")
    elif command == "country":
      print(f"country {arg}")
      self.get_user().country_code = arg
      self.get_user().save(update_fields=['country_code'])
      self.respond_to_user(
        self.get_user(), # FIXME: Swedish
        f"Tack för det! {arg}, memorerat.")
    else:
      print(f"Unknown processor command {command}, ignoring")
      self.respond_to_user(
        self.get_user(), # FIXME: Swedish
        "Hoppsan, det där blev konstigt. Vad hände???")

  def new_post_to_user(self, next_post_id):
    post = Post.objects.get(pk=next_post_id)
    self.conv.settings = json.dumps({'post': post.pk, 'history':{**self.get_setting(self.conv.settings, 'history'),**self.child_commands}})
    self.conv.save()
    message = post.name + "\n\n" + post.body
    self.respond_to_user(self.get_user(), message)

  def respond_to_user(self, to_user, message):
    bound_message = self.bind_message(message)
    self.quote_message(
      quote = bound_message,
      quote_from = self.get_self(),
      quote_to = to_user)
    self.responses += [{
        'operation':'send', 
        'to': to_user.user_handle,
        'message': bound_message,
      }]

  def bind_message(self, message):
    print(f"Responder.bind_message: var subst {self.message_params}")
    while True:
      idx = message.find('${')
      if idx < 0:
        print(f"Responder.bind_message: {message}")
        return message
      idx_end = message[idx:].find('}')
      var_name = message[idx+2:idx+idx_end]
      subst = self.message_params.get(var_name)
      if not subst:
        if var_name == "zip":
          subst = str(self.get_user().zip_code)
        elif var_name == "country":
          subst = str(self.get_user().country_code)
        else:
          print(f"Responder.bind_message: suspect subst {subst}, replacing with ??")
          subst = "??"
      if subst.find('${') >= 0:
        print(f"Responder.bind_message: suspect subst {subst}, replacing with ???")
        subst = "???"
      message = message[:idx] + subst + message[idx+idx_end+1:]

  def get_responses(self):
    return {'ok':self.responses}