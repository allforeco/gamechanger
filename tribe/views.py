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

def get_notes_list(rev):
    return [(
        note.pk,
        note.creation_date,
        note.text, 
    ) for note in ReventNote.objects.filter(in_revent=rev).order_by("-date")]

def get_roles_list(rev):
    return [(
        role.pk,
        role.get_role_name(), 
        role.person.id,
        role.person.callsign,
    ) for role in Role.objects.filter(in_revent=rev).order_by("-seq")]

def get_contact_info_list(rev):
    return [(
        contact.pk,
        contact.get_info_type_display(),
        contact.info, 
        contact.info.lower().startswith('http'),
    ) for contact in ContactInfo.objects.filter(in_revent=rev).order_by("-seq")]

def index(request):
    revents = Revent.objects.order_by("-creation_date")
    template = loader.get_template("tribe/index.html")
    notes = {}
    roles = {}
    contacts = {}
    for rev in revents:
        notes[rev.id] = get_notes_list(rev)
        roles[rev.id] = get_roles_list(rev)
        contacts[rev.id] = get_contact_info_list(rev.id)
    context = {
        "revents": revents,
        "notes": notes,
        "roles": roles,
        "contacts": contacts,
    }
    return HttpResponse(template.render(context, request))

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
        context["reventnote_list"] = ReventNote.objects.filter(in_revent=self.kwargs['pk'])
        logger.info(f'#### ReventNoteListView {len(context["reventnote_list"])} items')
        context["revent"] = Revent.objects.get(pk=self.kwargs['pk'])
        logger.info(f'#### ReventNoteListView revent {context["revent"]}')
        return context

class ReventNoteCreateView(CreateView):
    model = ReventNote
    fields = ["text"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["revent"] = Revent.objects.get(pk=self.kwargs['pk'])
        logger.info(f'#### ReventNoteCreateView revent {context["revent"]}')
        return context

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["revent"] = Revent.objects.get(pk=self.object.in_revent.pk)
        logger.info(f'#### ReventNoteUpdateView revent {context["revent"]}')
        return context

    def get_success_url(self):
        return reverse("tribe:reventnote-list", kwargs={"pk":self.object.in_revent.pk})

class ReventNoteDeleteView(DeleteView):
    model = ReventNote

    def get_success_url(self):
        return reverse("tribe:reventnote-list", kwargs={"pk":self.object.in_revent.pk})

class RoleListView(ListView):
    model = Role
    paginate_by = 10  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_list"] = get_roles_list(self.kwargs['pk'])
        context["revent"] = Revent.objects.get(pk=self.kwargs['pk'])
        return context

class RoleCreateView(CreateView):
    model = Role
    fields = ["role_type", "seq", "person"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["revent"] = Revent.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        logger.info('#### RoleCreate form_valid')
        logger.info(f'#### self {self}')
        logger.info(f'#### self dict {self.__dict__}')
        logger.info(f'#### self pk {self.kwargs.get("pk")}')
        form.instance.in_revent = Revent.objects.filter(pk=self.kwargs.get("pk")).first()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tribe:role-list", kwargs={"pk":self.object.in_revent.pk})

class RoleUpdateView(UpdateView):
    model = Role
    fields = ["role_type", "seq", "person"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["revent"] = Revent.objects.get(pk=self.object.in_revent.pk)
        return context

    def get_success_url(self):
        return reverse("tribe:role-list", kwargs={"pk":self.object.in_revent.pk})

class RoleDeleteView(DeleteView):
    model = Role

    def get_success_url(self):
        return reverse("tribe:role-list", kwargs={"pk":self.object.in_revent.pk})

class ContactInfoListView(ListView):
    model = ContactInfo
    paginate_by = 10  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contactinfo_list"] = get_contact_info_list(self.kwargs['pk'])
        context["revent"] = Revent.objects.get(pk=self.kwargs['pk'])
        return context

class ContactInfoCreateView(CreateView):
    model = ContactInfo
    fields = ["info_type", "seq", "info"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["revent"] = Revent.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        form.instance.in_revent = Revent.objects.filter(pk=self.kwargs.get("pk")).first()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("tribe:contactinfo-list", kwargs={"pk":self.object.in_revent.pk})

class ContactInfoUpdateView(UpdateView):
    model = ContactInfo
    fields = ["info_type", "seq", "info"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["revent"] = Revent.objects.get(pk=self.object.in_revent.pk)
        return context

    def get_success_url(self):
        return reverse("tribe:contactinfo-list", kwargs={"pk":self.object.in_revent.pk})

class ContactInfoDeleteView(DeleteView):
    model = ContactInfo

    def get_success_url(self):
        return reverse("tribe:contactinfo-list", kwargs={"pk":self.object.in_revent.pk})
