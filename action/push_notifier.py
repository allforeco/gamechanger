#   Gamechanger Action Push Notifier
#   Copyright (C) 2020 Jan Lindblad
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

import requests, os

'''
???send mobile push notification
'''
class Push_Notifier:
  @staticmethod
  def push(title, message):
    try:
      url = "https://api.pushover.net/1/messages.json"
      cred = Push_Notifier.get_or_die("PUSHOVER_TOKEN")
      payload = {}
      payload["token"] = cred
      payload["user"] = Push_Notifier.get_or_die("PUSHOVER_USERNAME")
      payload["title"] = title
      payload["message"] = message
      result = requests.post(url, data=payload)
      if(result.status_code == 200):
        print(f"PUSH Notice pushed: '{title}'\n     '{message}'")
        return
    except Exception as e:
      print(f"PUSH Exception: '{e}'")
      pass
    print(f"PUSH Failed to deliver notice: '{title}'\n     '{message}'")

  @staticmethod
  def get_or_die(name):
    return os.environ[name]
