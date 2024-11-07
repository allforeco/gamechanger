from django.shortcuts import render, redirect
from django.template import loader, RequestContext
from django.http import HttpResponse
#from django.views.decorators.csrf import csrf_exempt
#from django.forms import ModelForm
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
#from django.core.exceptions import ValidationError
#from django.contrib.auth.decorators import login_required, permission_required
from django import forms
#from django.db.models import Sum
#from django.contrib.auth.models import User
from .models import Revent, Role, ContactInfo, ReventNote
import logging

logger = logging.getLogger(__name__)
#logging.basicConfig(filename='myapp.log', level=logging.INFO)
logging.basicConfig(level=logging.INFO)
logger.info('#### Started')

# Create your views here.

def index(request):
    revents = Revent.objects.order_by("-creation_date")
    template = loader.get_template("tribe/index.html")
    notes = {}
    roles = {}
    contacts = {}
    for rev in revents:
        notes[rev.id] = [(
            note.creation_date,
            note.text, 
            ) for note in ReventNote.objects.filter(in_revent=rev).order_by("-date")]
        roles[rev.id] = [(
            role.get_role_name(), 
            role.person.id,
            role.person.callsign,
            ) for role in Role.objects.filter(in_revent=rev).order_by("-seq")]
        contacts[rev.id] = [(
            contact.info, 
            contact.get_contact_type_name(),
            ) for contact in ContactInfo.objects.filter(in_revent=rev).order_by("-seq")]
    context = {
        "revents": revents,
        "notes": notes,
        "roles": roles,
        "contacts": contacts,
    }
    return HttpResponse(template.render(context, request))


class ReventDetailForm(forms.Form):
    name = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        pass

class ReventDetailView(FormView):
    template_name = "tribe/revent_form.html"
    model = Revent
    form_class = ReventDetailForm
    success_url = "/thanks/"

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        #form.send_email()
        return super().form_valid(form)

class ReventCreateView(CreateView):
    model = Revent
    fields = ["name"]

    def get_success_url(self):
        return reverse("tribe:revent")

class ReventUpdateView(UpdateView):
    model = Revent
    fields = ["name"]

    def get_success_url(self):
        return reverse("tribe:revent")

class ReventDeleteView(DeleteView):
    model = Revent

    def get_success_url(self):
        return reverse("tribe:revent")

class ReventNoteListView(ListView):
    model = ReventNote
    paginate_by = 10  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notes"] = ReventNote.objects.filter(in_revent=self.kwargs['pk'])
        context["revent_pk"] = self.kwargs['pk']
        return context

class ReventNoteCreateView(CreateView):
    model = ReventNote
    fields = ["text"]

    def form_valid(self, form):
        logger.info('#### form_valid')
        logger.info(f'#### self {self}')
        logger.info(f'#### self dict {self.__dict__}')
        logger.info(f'#### self pk {self.kwargs.get("pk")}')
        form.instance.in_revent = Revent.objects.filter(pk=self.kwargs.get("pk")).first()
        logger.info(f'#### kwargs {self.get_form_kwargs()}')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tribe:reventnote-list", kwargs={"pk":self.object.in_revent.pk})

class ReventNoteUpdateView(UpdateView):
    model = ReventNote
    fields = ["text"]

    def get_success_url(self):
        return reverse("tribe:reventnote-list", kwargs={"pk":self.object.in_revent.pk})

class ReventNoteDeleteView(DeleteView):
    model = ReventNote

    def get_success_url(self):
        return None#reverse("tribe:reventnote-list", kwargs={"pk":self.object.in_revent.pk})
