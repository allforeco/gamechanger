#!/usr/bin/env python3
import os
import requests

def prime_send_file():
  filename = "fff-regid.csv" #In eventmap_data dir
  in_file = open(filename, "r")
  data = in_file.read()
  in_file.close()

  files = {'regfile': (filename, data)}
  print(f"TGCS Upload len {len(files['regfile'][1])}, sample {str(files['regfile'][1])[:200]}...")
  _send_to_gamechanger({}, files=files, local=True)

def _send_to_gamechanger(payload,files=None,local=True):
  urlsrc = "127.0.0.1:8000"
  if not local:
    print("ICSD, not sending to 'www.gamechanger.eco'")
    #urlsrc = "www.gamechanger.eco"

  url = "http://"+ urlsrc + "/action/upload_reg/post"
  token = os.environ['GAMECHANGER_UPLOAD_TOKEN']
  payload['token'] = token
  result = requests.post(url, data=payload, files=files)
  if(result.status_code == 200):
    print(f"UPGC Uploaded to {urlsrc}.\n{result.text}")
  else:
    print(f"NOGC Problem uploading to {urlsrc}:\n{result}")
    raise Exception(result.status_code)

'''
def main():
  #print(f"main()")
  debug = False
  selectors = []
  frequencies = []
  refreshers = []
  try:
    opts, args = getopt.getopt(sys.argv[1:],"hs:f:r:",
      ["help", "debug", "selector=", "frequency=", "refresh="])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ('-h', '--help'):
      usage()
      sys.exit()
    elif opt in ("-s", "--selector"):
      selectors += [arg]
    elif opt in ("-f", "--frequency"):
      frequencies += [arg]
    elif opt in ("-r", "--refresh"):
      refreshers += [arg]
    elif opt in ("--debug"):
      debug = True
    else:
      print(f'Unknown option "{opt}", exiting.')
      sys.exit(2)
'''

prime_send_file()