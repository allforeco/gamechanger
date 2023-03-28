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
import json, logging, random

PK_SELF_ACTOR_ID = 7
SUPPORTED_LANGUAGES = ["sv"]

logging.basicConfig(
  level=logging.INFO, 
  format='%(asctime)s: %(message)s')
logging.info(f"Responder initialized")

class Responder:
  def __init__(self, request):
    self.request = request
    self.inc_message = self.request.get('message')
    self.curr_post = None
    self.conv = None
    self.commands = None
    self.child_commands = None
    self.message_params = {}
    self.responses = []
    logging.info(f"Responder: {self.get_user_handle()} {self.get_display_name()} {self.get_lang()} {self.get_usable_lang()}")

  def get_user_handle(self):
    return self.request.get('user_handle')

  def get_display_name(self):
    return self.request.get('display_name')

  def get_message(self):
    return self.inc_message

  def get_lang(self):
    return self.request.get('lang')

  def get_usable_lang(self):
    lang = self.get_lang().lower()
    if lang not in SUPPORTED_LANGUAGES:
      lang = "sv" # FIXME: Swedish
    return lang

  def get_user(self):
    users = Actor.objects.filter(user_handle=self.get_user_handle())
    if users.exists():
      return users.first()
    else:
      # Unknown/new user
      logging.info(f"Responder.get_user: New user {self.get_user_handle()}. Welcome!")
      
      conversation = Conversation(settings = {})
      conversation.save()

      user = Actor(
        user_handle = self.get_user_handle(),
        conversation = conversation,
      )
      user.save()
      self.respond_to_user(
        self.get_user(),
        self.get_named_post("welcome").body)
      
      # Whatever greeting user sends, don't take it as a command
      self.inc_message = ''
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
      logging.debug(f"Responder.fetch_curr_post: post id '{curr_post_id}'")
    except:
      logging.info(f"Responder.fetch_curr_post: could not find conversation {self.conv.settings}")
      curr_post_id = None

    if not curr_post_id: # New conversation
      curr_post_id = self.get_named_post("start").pk

    self.curr_post = Post.objects.get(pk=curr_post_id)
    logging.debug(f"Responder.fetch_curr_post: curr_post {self.curr_post} post_id = {curr_post_id}")

  def collect_commands(self):
    def child_command_name(child_post_name):
      return '-'.join(child_post_name.split('-')[1:]).lower()
    curr_post_children = self.curr_post.children.all()
    logging.debug(f"Responder.fetch_curr_post: self.post.children = {curr_post_children}")
    history_commands = self.get_setting(self.conv.settings, 'history')
    post_specfic_commands = self.get_setting(self.curr_post.settings, 'actions')
    self.child_commands = {child_command_name(c.name):c.pk for c in self.curr_post.children.all()}
    admin_commands = {".uppdatera":"update",".kommentera":"comment"} # FIXME: Swedish
    self.commands = {**history_commands,**post_specfic_commands,**self.child_commands,**admin_commands}
    logging.debug(f'Responder.collect_commands(): commands = {self.commands.keys()}')

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
    logging.debug(f"Responder.handle_post_settings: post preprocessors = {curr_post_preprocessors}")
    for dct in curr_post_preprocessors:
      instr = dct.get('instr')      
      if instr == 'set-command':
        self.command_line = dct.get('val','')
      else:
        logging.error(f"Unknown preprocessor command {instr}, ignoring")

  def execute_command(self):
    def parse_command(command_line, commands):
      for c in commands:
        if command_line.startswith(c):
          return (c, command_line[len(c):].strip())
      return (None, command_line)

    logging.debug(f"Responder.execute_command: command '{self.command_line}'")
    if not self.command_line:
      return self.new_post_to_user(self.curr_post.pk)
    (command, arg) = parse_command(self.command_line, self.commands)
    if not command:
      logging.warning(f'Responder.execute_command: unknown command')
      return self.respond_to_user(
        self.get_user(),
        self.get_named_post("system-error-unknown-command").body, 
        {'commands':", ".join(list(self.commands.keys()))})
    if isinstance(self.commands[command], int):
      logging.debug(f'Responder.execute_command: new post "{command}" -> post {self.commands[command]}')
      return self.new_post_to_user(self.commands[command])
    elif isinstance(self.commands[command], str):
      logging.debug(f'Responder.execute_command: calling special command "{self.commands[command]}"')
      return self.process_special_command(self.commands[command], arg)
    else:
      logging.error(f'Responder.execute_command: unknown command type "{self.commands[command]}"')
      return self.respond_to_user(
        self.get_user(),
        self.get_named_post("system-error-internal").body,
        {'code':'PEX'})

  def get_zip_prefix(self, zip):
    return zip[:2] # FIXME Swedish assumption

  def process_special_command(self, command, arg):
    # historia .uppdatera .visa inbox
    if command == "zip":
      logging.debug(f"zip {arg} {self.get_user()}")
      user = Actor.objects.get(pk=self.get_user().pk) # Why is this needed??
      user.zip_code = str(arg.upper())[:user._meta.get_field('zip_code').max_length]
      user.save(update_fields=['zip_code'])
      self.respond_to_user(
        self.get_user(),
        self.get_named_post("thanks-for-info-bit").body,
        {'arg':self.get_user().zip_code})

      for receiving_user in Actor.objects.filter(
        country_code=self.get_user().country_code,
        zip_code__startswith=self.get_zip_prefix(self.get_user().zip_code)):
        print(f"Zip in vicinity: {receiving_user.user_handle}")
        self.respond_to_user(
          receiving_user,
          self.get_named_post("invitation-to-connect").body,
          {'senders_zip_code': self.get_user().zip_code})

    elif command == "country":
      logging.debug(f"country {arg}")
      user = Actor.objects.get(pk=self.get_user().pk) # Why is this needed??
      user.country_code = str(arg.upper())[:user._meta.get_field('country_code').max_length]
      user.save(update_fields=['country_code'])
      self.respond_to_user(
        self.get_user(),
        self.get_named_post("thanks-for-info-bit").body,
        {'arg':self.get_user().country_code})
    else:
      logging.error(f"Unknown processor command {command}, ignoring")
      self.respond_to_user(
        self.get_user(),
        self.get_named_post("system-error-internal").body,
        {'code':'PESC'})

  def get_named_post(self, post_name):
    posts = Post.objects.filter(name=self.get_usable_lang() + "-" + post_name)
    if posts.exists():
      return posts.first()
    return None

  def new_post_to_user(self, next_post_id):
    post = Post.objects.get(pk=next_post_id)
    self.conv.settings = json.dumps({'post': post.pk, 'history':{**self.get_setting(self.conv.settings, 'history'),**self.child_commands}})
    self.conv.save(update_fields=['settings'])
    self.respond_to_user(self.get_user(), post.body)

  def respond_to_user(self, to_user, message, extra_bindings = {}):
    bound_message = self.bind_message(message, {**self.message_params,**extra_bindings})
    self.quote_message(
      quote = bound_message,
      quote_from = self.get_self(),
      quote_to = to_user)
    self.responses += [{
        'operation':'send', 
        'to': to_user.user_handle,
        'message': bound_message,
      }]
    logging.info(f"Responder queued message to {to_user.user_handle}:\n{bound_message}")

  def bind_message(self, message, bindings):
    logging.debug(f"Responder.bind_message: var subst {bindings}")
    message = random.choice(message.split('||'))
    message = message.replace('\\n',"""
""")
    while True:
      idx = message.find('${')
      if idx < 0:
        logging.debug(f"Responder.bind_message: {message}")
        return message
      idx_end = message[idx:].find('}')
      var_name = message[idx+2:idx+idx_end]
      subst = bindings.get(var_name)
      if not subst:
        if var_name == "display_name":
          subst = str(self.get_display_name())
        elif var_name == "user_handle":
          subst = str(self.get_user_handle())
        elif var_name == "zip_code":
          subst = str(self.get_user().zip_code)
        elif var_name == "country_code":
          subst = str(self.get_user().country_code)
        else:
          logging.error(f"Responder.bind_message: suspect subst {subst}, replacing with ??")
          subst = "??"
      if subst.find('${') >= 0:
        logging.error(f"Responder.bind_message: suspect subst {subst}, replacing with ???")
        subst = "???"
      message = message[:idx] + subst + message[idx+idx_end+1:]

  def get_responses(self):
    return {'ok':self.responses}