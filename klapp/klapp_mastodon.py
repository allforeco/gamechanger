#!/usr/bin/env python3.8

#   Gamechanger Klapp Mastodon Interface
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

import os, sys, getopt, logging, time, requests
from mastodon import Mastodon, StreamListener, MastodonError, MastodonNetworkError

############################################################
# Klapp
############################################################
class Klapp(StreamListener):
  MASTODON_SERVER_URL = os.environ['MASTODON_SERVER_URL']
  MASTODON_LOGIN_ID = os.environ['MASTODON_LOGIN_ID']
  MASTODON_LOGIN_PASS = os.environ['MASTODON_LOGIN_PASS']
  CLIENT_ID_FILE = '.env/Klapp.secret'

  KLAPP_SERVER = "http://127.0.0.1:8000"
  KLAPP_POST_PATH = "klapp/botchat"

  def __init__(self):
    logging.info(f"Klapp.__init__()")
    self.post_path = f"{Klapp.KLAPP_SERVER}/{Klapp.KLAPP_POST_PATH}"

  def on_update(self, status):
    logging.info(f"Klapp.on_update({status})")
    if status.visibility:
      logging.info(f"Content\n{status.content}!")

  def on_notification(self, notification):
    logging.info(f"Klapp.on_notification({notification})")
    if notification.type == "follow":
      logging.info(f"Followed by {notification.account.display_name}!")

    elif notification.type == "mention":
      logging.info(f"Mentioned by {notification.account.display_name}!")

      response = requests.post(self.post_path, data={
        'user_handle':notification.account.username,
        'display_name':notification.account.display_name,
        'message':notification.status.content or "No Content",
        'lang':notification.status.language or None,
      })
      self.process_klapp_response(response)

  def on_delete(self, status_id):
    logging.info(f"Klapp.on_delete({status_id})")

  def on_conversation(self, conversation):
    logging.info(f"Klapp.on_conversation({conversation})")

  def on_status_update(self, status):
    logging.info(f"Klapp.on_status_update({status})")

  def on_unknown_event(self, name, unknown_event=None):
    logging.info(f"Klapp.on_unknown_event({name}, {unknown_event})")

  def on_abort(self, err):
    logging.info(f"Klapp.on_abort({err})")

  def handle_heartbeat(self):
    #logging.info(f"Klapp.handle_heartbeat()")
    pass

  def process_klapp_response(self, response):
    if response.status_code == 200:
      try:
        json = response.json()
      except: 
        logging.error(f'PKR JSON decoding failed \n{response.text}')
        return
      logging.info(f"PKR received JSON {json}")
      #{"ok": [{"operation": "send", "to": "jarlix", "message": "Hej Jan L!"}]}
      if "ok" in json:
        for instr in json["ok"]:
          if instr["operation"] == "send":
            self.mastodon.status_post(
              f'@{instr["to"]}, {instr["message"]}', 
              in_reply_to_id=None, 
              visibility="direct")
          else:
            logging.error(f'PKR unknown operqation "{instr["operation"]}"')
      else:
        logging.error(f'PKR no "ok" in response')
    else:
      logging.error(f"PKR received HTTP status {response.status_code}")

  def register_server():
    return Mastodon.create_app(
      'Klapp',
      api_base_url = Klapp.MASTODON_SERVER_URL,
      to_file = Klapp.CLIENT_ID_FILE
    )

  def login(self):
    logging.info(f"Klapp.login()")
    self.mastodon = Mastodon(
      client_id = Klapp.CLIENT_ID_FILE,)
    self.access_token = self.mastodon.log_in(
      username=Klapp.MASTODON_LOGIN_ID,
      password=Klapp.MASTODON_LOGIN_PASS,
    )
    logging.info(f"Klapp access_token length={len(self.access_token)}")

  def serve(self):
    logging.info(f"Klapp.serve()")
    try:
      self.mastodon.stream_user(self)
    except MastodonNetworkError:
      time.sleep(15)
      raise

############################################################
# Main
############################################################
def usage():
  print("")

def main():
  logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s: %(message)s')
  logging.info(f"Klapp main() running")
  try:
    opts, args = getopt.getopt(sys.argv[1:],"hd",
      ["help", "debug", "selector=", "frequency=", "refresh="])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ('-h', '--help'):
      usage()
      sys.exit()
    elif opt in ("-d", "--debug"):
      logging.basicConfig(level=logging.DEBUG)

    elif opt in ("-s", "--selector"):
      pass
  
  klapp = Klapp()
  klapp.login()
  while True:
    try:
      klapp.serve()
    except Exception as ex:
      logging.error(f"Klapp.serve() exception", exc_info=ex)
    finally:
      logging.info(f"Klapp.serve() restarting")

if __name__ == '__main__':
  main()
############################################################