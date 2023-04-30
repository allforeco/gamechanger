#   Gamechanger Twiff2 Views
#   Copyright (C) 2023 Tom Vermolen, Jan Lindblad
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

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotAllowed
import logging, os, json
from . import search

@csrf_exempt
def run_view(request):
  if request.method != "GET":
    return HttpResponseNotAllowed(permitted_methods=['GET'])

  if request.GET.get('token', '') != os.environ["TWIFF2_TOKEN"]:
    return HttpResponseNotAllowed(permitted_methods=['GET'])

  logging.info("Twiff2 collection starting")
  try:
    logging.debug("Twiff2 collection called")

    twiff_args_file = os.environ["TWIFF2_ARGS_FILE"]
    with open(twiff_args_file, 'r') as fp:
      args = json.load(fp)
    search_results = search.main(args)

    logging.debug("Twiff2 collection complete")
    return HttpResponse(f"Twiff2 collection done\n{search_results}")
  except:
    logging.exception("Twiff2 collection raised an exception")
    return HttpResponse("Twiff2 collection failed.")
