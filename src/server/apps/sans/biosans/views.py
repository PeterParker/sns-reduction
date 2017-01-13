import json
import logging
import os
from pprint import pformat

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, RedirectView, TemplateView

from server.apps.catalog.models import Instrument
from server.apps.users.ldap_util import LdapSns
from server.util import script
from server.util.formsets import FormsetMixin

from .forms import BioSANSConfigurationForm, BioSANSReductionForm, BioSANSRegionForm, BioSANSReductionScriptForm, \
    BioSANSRegionInlineFormSetCreate, BioSANSRegionInlineFormSetUpdate
from .models import BioSANSConfiguration, BioSANSReduction, BioSANSRegion
from ..models import Region

logger = logging.getLogger('sans.biosans')


class ConfigurationMixin(object):
    def get_queryset(self):
        '''
        Make sure the user only accesses its configurations
        '''
        return BioSANSConfiguration.objects.filter(user = self.request.user)

class ConfigurationList(LoginRequiredMixin, ConfigurationMixin, ListView):
    '''
    List all configurations.
    '''
    def get_queryset(self):
        return super(ConfigurationList, self).get_queryset()

class ConfigurationDetail(LoginRequiredMixin, ConfigurationMixin, DetailView):
    '''
    Detail of a configuration
    '''
    def get_queryset(self):
        queryset = super(ConfigurationDetail, self).get_queryset()
        return queryset.filter(id = self.kwargs['pk'])

class ConfigurationCreate(LoginRequiredMixin, CreateView):
    '''
    Detail of a configuration
    '''
    template_name = 'sans/biosansconfiguration_form.html'
    # Using form rather than model as we are hiding some fields!!
    form_class = BioSANSConfigurationForm

    def form_valid(self, form):
        """
        Sets initial values which are hidden in the form
        """
        form.instance.user = self.request.user
        form.instance.instrument = get_object_or_404(Instrument,
            name=self.request.session['instrument'].name)
        return CreateView.form_valid(self, form)

class ConfigurationUpdate(LoginRequiredMixin, UpdateView):
    '''
    Detail of a configuration
    '''
    template_name = 'sans/biosansconfiguration_form.html'
    # Using form rather than model as we are hiding some fields!!
    form_class = BioSANSConfigurationForm
    model = BioSANSConfiguration

class ConfigurationDelete(LoginRequiredMixin, DeleteView):
    
    model = BioSANSConfiguration
    success_url = reverse_lazy('sans:biosans:configuration_list')

    def get_object(self, queryset=None):
        """
        Hook to ensure object is owned by request.user.
        """
        obj = super(ConfigurationDelete, self).get_object()
        if not obj.user  == self.request.user:
            raise Http404
        return obj

    def delete(self, request, *args, **kwargs):
        logger.debug("Deleting Configuration %s"%self.get_object())
        messages.success(request, 'Configuration %s deleted.'%(self.get_object()))
        return super(ConfigurationDelete, self).delete(request, *args, **kwargs)
    

class ConfigurationClone(LoginRequiredMixin, ConfigurationMixin, DetailView):
    '''
    Clones the Object Configuration. Keeps the same user
    '''
    def get_object(self):
        obj = BioSANSConfiguration.objects.clone(self.kwargs['pk'])
        self.kwargs['pk'] = obj.pk
        messages.success(self.request, "Configuration '%s' cloned. New id is '%s'. Click Edit below to change it."%(obj, obj.pk))
        return obj

class ConfigurationAssignListUid(LoginRequiredMixin, ConfigurationMixin, TemplateView):
    '''
    List all UIDS + names and provides a link to assign a Configuration
    to a user.
    Context has 2 objects: the conf to assign and a list of uids + names
    '''
    template_name = 'sans/biosansconfiguration_list_uid.html'

    def get_context_data(self, **kwargs):
        context = super(ConfigurationAssignListUid, self).get_context_data(**kwargs)
        ldap_server = LdapSns()
        users_and_uids = ldap_server.get_all_users_name_and_uid()
        context['object_list'] = users_and_uids
        obj = BioSANSConfiguration.objects.get(pk=kwargs['pk'])
        context['object'] = obj
        return context

class ConfigurationAssignListIpts(LoginRequiredMixin, ConfigurationMixin, TemplateView):
    '''
    List all IPTSs and provides a link to assign a Configuration
    to all users to that IPTS.
    Context has 2 objects: the conf to assign and a list of ipts
    '''
    template_name = 'sans/biosansconfiguration_list_ipts.html'

    def get_context_data(self, **kwargs):
        context = super(ConfigurationAssignListIpts, self).get_context_data(**kwargs)
        ldap_server = LdapSns()
        ipts = ldap_server.get_all_ipts()
        context['object_list'] = ipts
        obj = BioSANSConfiguration.objects.get(pk=kwargs['pk'])
        context['object'] = obj
        return context


class ConfigurationAssignUid(LoginRequiredMixin, ConfigurationMixin, DetailView):
    '''
    This gets a configuration pk and uid from url, clones the Configuration
    and assigns it to the user
    It will display the original Configuration
    '''
    template_name = 'sans/biosansconfiguration_detail.html'
    model = BioSANSConfiguration
    
    def get(self, request, *args, **kwargs):
        obj = BioSANSConfiguration.objects.clone_and_assign_new_uid(kwargs['pk'],kwargs['uid'])
        messages.success(request, "Configuration %s assigned to the user %s. New configuration id = %s."%(obj, obj.user, obj.pk))
        return super(ConfigurationAssignUid, self).get(request, *args, **kwargs)

class ConfigurationAssignIpts(LoginRequiredMixin, ConfigurationMixin, DetailView):
    '''
    
    '''
    template_name = 'sans/biosansconfiguration_detail.html'
    model = BioSANSConfiguration
    
    def get(self, request, *args, **kwargs):
        cloned_objs = BioSANSConfiguration.objects.clone_and_assign_new_uids_based_on_ipts(kwargs['pk'],kwargs['ipts'])
        for obj in cloned_objs:
            messages.success(request, "Configuration %s assigned to the user %s. New configuration id = %s."%(obj, obj.user, obj.pk))
        return super(ConfigurationAssignIpts, self).get(request, *args, **kwargs)

#######################################################################
#
# Reduction
#
#######################################################################

class ReductionMixin(object):
    '''
    Used in the template form to populate the redution spreadsheet
    '''

    def get_context_data(self, **kwargs):
        '''
        Populates the context with the titled case names and names as in the model
        '''
        context = super(ReductionMixin, self).get_context_data(**kwargs)
        context["entry_headers"] = ["Sample Scattering", "Sample Transmission",
                                    "Backgroung Scattering", "Backgroung Transmission"]
        return context


    def get_queryset(self):
        '''
        Get only reductions for this user: reduction.configuration.user
        '''
        return BioSANSReduction.objects.filter(user = self.request.user)
    
    def get_formset(self, form_class=None):
        '''
        When creating/editing a formset, this will make sure the user only sees it's own
        configurations
        '''
        formset = super(ReductionMixin,self).get_formset(form_class) #instantiate using parent
        for form in formset:
            form.fields['configuration'].queryset = BioSANSConfiguration.objects.filter(user = self.request.user)
        return formset
    
    def get_formset_kwargs(self):
        '''
        Sets the initial values for the regions formsets
        '''
        kwargs = super(ReductionMixin,self).get_formset_kwargs()
        kwargs.update({'initial' : [{'region': Region.REGION_CHOICES[0][0]},
                                    {'region': Region.REGION_CHOICES[-1][0]}]})
        return kwargs
    
class ReductionList(LoginRequiredMixin, ReductionMixin, ListView):
    '''
    List all Reduction.
    '''
    template_name = 'sans/biosansreduction_list.html'
    # We wither use the model or the function get_queryset
    #model = BioSANSReduction
    def get_queryset(self):
        '''
        Get only reductions for this user: reduction.configuration.user
        '''
        return super(ReductionList, self).get_queryset()
    

class ReductionDetail(LoginRequiredMixin, ReductionMixin, DetailView):
    '''
    Detail of a Reduction
    A Reduction is a title and a set of entries.
    The entries are an hidden field : id="entries_hidden"
    Which are an Handsontable
    '''

    def get_queryset(self):
        '''
        Get only reductions for this user: reduction.configuration.user
        '''
        queryset = super(ReductionDetail, self).get_queryset()
        return queryset.filter(id = self.kwargs['pk'])


class ReductionCreate(LoginRequiredMixin, ReductionMixin, FormsetMixin, CreateView):
    '''
    Create a new entry!
    '''
    template_name = 'sans/biosansreduction_form.html'
    #model = BioSANSReduction
    form_class = BioSANSReductionForm
    formset_class = BioSANSRegionInlineFormSetCreate

    def form_valid(self, form, formset):
        """
        Sets initial values which are hidden in the form
        """
        form.instance.user = self.request.user
        form.instance.instrument = get_object_or_404(Instrument,
            name=self.request.session['instrument'].name)
        return FormsetMixin.form_valid(self, form, formset)


class ReductionUpdate(LoginRequiredMixin, ReductionMixin, FormsetMixin, UpdateView):
    '''
    Edit a Reduction
    '''
    template_name = 'sans/biosansreduction_form.html'
    form_class = BioSANSReductionForm
    formset_class = BioSANSRegionInlineFormSetUpdate


class ReductionDelete(LoginRequiredMixin, DeleteView):
    model = BioSANSReduction
    success_url = reverse_lazy('sans:biosans:reduction_list')

    def get_object(self, queryset=None):
        """
        Hook to ensure object is owned by request.user.
        """
        obj = super(ReductionDelete, self).get_object()
        if not obj.user  == self.request.user:
            raise Http404
        return obj
    
    def delete(self, request, *args, **kwargs):
        logger.debug("Deleting reduction %s"%self.get_object())
        messages.success(request, 'Reduction %s deleted.'%(self.get_object()))
        return super(ReductionDelete, self).delete(request, *args, **kwargs)

class ReductionClone(LoginRequiredMixin, ReductionMixin, DetailView):
    '''
    Clones the Object Configuration. Keeps the same user
    '''
    def get_object(self):
        obj = BioSANSReduction.objects.clone(self.kwargs['pk'])
        self.kwargs['pk'] = obj.pk
        messages.success(self.request, "Reduction '%s' cloned. New id is '%s'. Click Edit below to change it."%(obj, obj.pk))
        return obj

class ReductionScriptUpdate(LoginRequiredMixin, ReductionMixin, UpdateView):
    '''
    Edit a Reduction Script
    This View will generate the script, show it to the user and 
    on save save it to db and enevutally submit a job
    '''
    template_name = 'sans/reduction_script_form.html'
    form_class = BioSANSReductionScriptForm
    success_url = reverse_lazy('sans:biosans:reduction_list')
    
    def get_object(self):
        '''
        Generate the script and added to object shown on the form
        '''
        obj = super(ReductionScriptUpdate, self).get_object()
        obj_json = BioSANSReduction.objects.to_json(self.kwargs['pk'])
        python_script = script.build_script(
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         "script.tpl")
            , obj_json)
        obj.script = python_script
        return obj
    
    def form_valid(self, form):
        """
        Sends the script to the custer
        TODO
        """
        script = form.instance.script
        logger.debug(script)
        messages.success(self.request, "Reduction submitted to the cluster")
        return super(ReductionScriptUpdate, self).form_valid(form)