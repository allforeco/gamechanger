#   Gamechanger Action Views
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

from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
#from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
from django.shortcuts import redirect
import datetime


def tools_view_handler(request, result='Start'):
    template = loader.get_template('action/tools_view.html')
    merge_result = request.GET.get('message')
    context = {
        'test_text': str(result),
        'placeholders': ''
    }
    return HttpResponse(template.render(context, request))


def tools_view_post(request):
    if request.user.is_authenticated:
        do_merge_event = request.POST.get('do_merge_event')
        if do_merge_event:
            test_count = False # Test bit only counts number of gatherings to merge
            test_move = False # Test bit merge gatherings, do not delete location
            # Check the URLs
            from_location_url = request.POST.get('merge_from_url')
            to_location_url = request.POST.get('merge_to_url')
            result = ''
            try:
                url_parts = from_location_url.split('/')
                if url_parts[3] == 'action' and url_parts[4] == 'geo':
                    from_location_id = url_parts[5]
                    f_loc = Location.objects.filter(id=int(from_location_id))[0]
                else:
                    result = 'Invalid from URL'
                url_parts = to_location_url.split('/')
                if url_parts[3] == 'action' and url_parts[4] == 'geo':
                    to_location_id = url_parts[5]
                    t_loc = Location.objects.filter(id=int(to_location_id))[0]
                else:
                    result = 'Invalid to URL'
            except:
                result = 'Invalid URL exception'
            if result == '':
                # Check to from location has no sub locations, abort if found any
                if Location.objects.filter(in_location=f_loc).count() > 0:
                    result = 'The delete location still contains sub locations, merge aborted'
            # Let's see if anything needs to be merged
            if result == '':
                gatherings = Gathering.objects.filter(location=f_loc)
                if test_count:
                    result = str(gatherings.count())
                    return redirect('action:tools_result', result + str(t_loc))
                gat_count = 0
                for gat in gatherings:
                    gat.location = t_loc
                    gat.save()
                    gat_count += 1
                if test_move:
                    result = 'Locations moved: ' + str(gat_count)
                    return redirect('action:tools_result', result)
                old_name = f_loc.name
                new_name = t_loc.name
                f_loc.delete()
                result = 'Moved ' + str(gat_count) + ' gatherings from ' + old_name + ' (' + from_location_id + ') to '\
                         + new_name + ' (' + to_location_id + ') to '
            return redirect('action:tools_result', result)
    return redirect('action:home')
