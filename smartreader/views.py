import json
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from .tasks import send_mqtt_command
from django.urls import reverse_lazy
from formtools.wizard.views import SessionWizardView
from django.views.generic import FormView, ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import AlertAction, AlertCondition, AlertRule, MQTTConfiguration, MqttCommandTemplate, MQTTCommand, SmartReader
from .forms import AlertActionForm, AlertConditionForm, AlertConditionFilterForm, BasicInfoForm, ConditionFormSet, ActionFormSet, AlertRuleForm, AlertConditionForm, AlertActionForm, AlertRuleFilterForm, MQTTConfigurationForm, MqttCommandForm, MqttCommandTemplateForm, SmartReaderForm, SmartReaderFilterForm, CommandSendForm

TEMPLATES = {
    '0': 'smartreader/alert_rule_basic_info_form.html',
    '1': 'smartreader/alert_rule_conditions_form.html',
    '2': 'smartreader/alert_rule_actions_form.html',
}

def test_alert_action(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        action_type = data.get('action_type')
        action_value = data.get('action_value')
        message_template = data.get('message_template')
        
        # Create a temporary AlertAction object to simulate the execution
        action = AlertAction(action_type=action_type, action_value=action_value, message_template=message_template)
        
        # Simulate an event
        sample_event = {
            "reader_name": "SampleReader",
            "event_type": "SampleEvent",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        try:
            populated_message = action._populate_message(sample_event)
            # If no exception occurs, return success
            return JsonResponse({"success": True, "message": populated_message})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})

class AlertActionListView(ListView):
    model = AlertAction
    template_name = 'smartreader/alert_action_list.html'
    context_object_name = 'alert_actions'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        action_type = self.request.GET.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        return queryset

class AlertActionCreateView(CreateView):
    model = AlertAction
    form_class = AlertActionForm
    template_name = 'smartreader/alert_action_form.html'
    success_url = reverse_lazy('alert_action_list')

class AlertActionUpdateView(UpdateView):
    model = AlertAction
    form_class = AlertActionForm
    template_name = 'smartreader/alert_action_form.html'
    success_url = reverse_lazy('alert_action_list')

class AlertActionDeleteView(DeleteView):
    model = AlertAction
    template_name = 'smartreader/alert_action_confirm_delete.html'
    success_url = reverse_lazy('alert_action_list')

class AlertConditionListView(ListView):
    model = AlertCondition
    template_name = 'smartreader/alert_condition_list.html'
    context_object_name = 'alert_conditions'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        condition_type = self.request.GET.get('condition_type')
        field_name = self.request.GET.get('field_name')
        threshold = self.request.GET.get('threshold')

        if condition_type:
            queryset = queryset.filter(condition_type=condition_type)
        if field_name:
            queryset = queryset.filter(field_name__icontains=field_name)
        if threshold:
            queryset = queryset.filter(threshold__icontains=threshold)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AlertConditionFilterForm(self.request.GET or None)
        return context

class AlertConditionCreateView(CreateView):
    model = AlertCondition
    form_class = AlertConditionForm
    template_name = 'smartreader/alert_condition_form.html'
    success_url = reverse_lazy('alert_condition_list')

class AlertConditionUpdateView(UpdateView):
    model = AlertCondition
    form_class = AlertConditionForm
    template_name = 'smartreader/alert_condition_form.html'
    success_url = reverse_lazy('alert_condition_list')

class AlertConditionDeleteView(DeleteView):
    model = AlertCondition
    template_name = 'smartreader/alert_condition_confirm_delete.html'
    success_url = reverse_lazy('alert_condition_list')

class AlertRuleWizard(SessionWizardView):
    form_list = [BasicInfoForm, ConditionFormSet, ActionFormSet]
    template_name = 'smartreader/alert_rule_form.html'  # Fallback template

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        # Save the basic information form
        basic_info_form = form_list[0]
        alert_rule = basic_info_form.save()

        # Save the conditions
        condition_formset = form_list[1]
        for form in condition_formset:
            if form.cleaned_data:
                condition = form.save(commit=False)
                condition.alert_rule = alert_rule
                condition.save()

        # Save the actions
        action_formset = form_list[2]
        for form in action_formset:
            if form.cleaned_data:
                action = form.save(commit=False)
                action.alert_rule = alert_rule
                action.save()

        # Redirect to the alert rule list page or detail page after saving
        return redirect('alert_rule_list')
    
class AlertRuleListView(ListView):
    model = AlertRule
    template_name = 'smartreader/alert_rule_list.html'
    context_object_name = 'alert_rule_list'
    paginate_by = 10  # Show 10 alert rules per page

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtering by name
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Filtering by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Sorting
        ordering = self.request.GET.get('ordering')
        if ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AlertRuleFilterForm(self.request.GET or None)  # Assuming you have a filter form
        return context

class AlertRuleCreateView(CreateView):
    model = AlertRule
    form_class = AlertRuleForm
    template_name = 'smartreader/alert_rule_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle saving of conditions and actions in the next steps
        return response

class AlertRuleUpdateView(UpdateView):
    model = AlertRule
    form_class = AlertRuleForm
    template_name = 'smartreader/alert_rule_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle updating of conditions and actions
        return response

class AlertRuleDeleteView(DeleteView):
    model = AlertRule
    template_name = 'smartreader/alert_rule_confirm_delete.html'
    success_url = '/smartreader/alert-rules/'  # Adjust to your needs

class CommandSendView(FormView):
    template_name = 'smartreader/command_send.html'
    form_class = CommandSendForm
    success_url = reverse_lazy('smartreader_list')

    def form_valid(self, form):
        command_template = form.cleaned_data['command_template']
        selected_readers = form.cleaned_data['smartreaders']

        # Create the MQTTCommand and link it to the selected readers
        command = MqttCommand.objects.create(command_template=command_template)
        command.smartreaders.set(selected_readers)
        command.save()

        # Trigger the Celery task to send the command
        send_mqtt_command.delay(command.id)

        return super().form_valid(form)
    
class MQTTConfigurationListView(ListView):
    model = MQTTConfiguration
    template_name = 'smartreader/mqttconfiguration_list.html'
    context_object_name = 'configurations'
    paginate_by = 10  # Adjust the number of items per page as needed
    ordering = ['-id']  # Default sorting by ID descending

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add filtering logic here if needed
        return queryset

class MQTTConfigurationDetailView(DetailView):
    model = MQTTConfiguration
    template_name = 'smartreader/mqttconfiguration_detail.html'
    context_object_name = 'configuration'

class MQTTConfigurationCreateView(CreateView):
    model = MQTTConfiguration
    form_class = MQTTConfigurationForm
    template_name = 'smartreader/mqttconfiguration_form.html'
    success_url = reverse_lazy('mqttconfiguration_list')

class MQTTConfigurationUpdateView(UpdateView):
    model = MQTTConfiguration
    form_class = MQTTConfigurationForm
    template_name = 'smartreader/mqttconfiguration_form.html'
    success_url = reverse_lazy('mqttconfiguration_list')

class MQTTConfigurationDeleteView(DeleteView):
    model = MQTTConfiguration
    template_name = 'smartreader/mqttconfiguration_confirm_delete.html'
    success_url = reverse_lazy('mqttconfiguration_list')

class MqttCommandTemplateListView(ListView):
    model = MqttCommandTemplate
    template_name = 'smartreader/mqttcommandtemplate_list.html'

class MqttCommandTemplateCreateView(CreateView):
    model = MqttCommandTemplate
    form_class = MqttCommandTemplateForm
    template_name = 'smartreader/mqttcommandtemplate_form.html'
    success_url = reverse_lazy('mqttcommandtemplate_list')

class MqttCommandTemplateUpdateView(UpdateView):
    model = MqttCommandTemplate
    form_class = MqttCommandTemplateForm
    template_name = 'smartreader/mqttcommandtemplate_form.html'
    success_url = reverse_lazy('mqttcommandtemplate_list')

class MqttCommandTemplateDetailView(DetailView):
    model = MqttCommandTemplate
    template_name = 'smartreader/mqttcommandtemplate_detail.html'

class MqttCommandTemplateDeleteView(DeleteView):
    model = MqttCommandTemplate
    template_name = 'smartreader/mqttcommandtemplate_confirm_delete.html'
    success_url = reverse_lazy('mqttcommandtemplate_list')

class MQTTCommandListView(ListView):
    model = MQTTCommand
    template_name = 'smartreader/mqtt_command_list.html'
    context_object_name = 'commands'
    paginate_by = 10

    def get_queryset(self):
        queryset = MQTTCommand.objects.all().order_by('-created_at')
        return queryset

class MqttCommandCreateView(CreateView):
    model = MQTTCommand
    form_class = MqttCommandForm
    template_name = 'smartreader/mqttcommand_form.html'
    success_url = reverse_lazy('mqttcommand_list')

class MqttCommandUpdateView(UpdateView):
    model = MQTTCommand
    form_class = MqttCommandForm
    template_name = 'smartreader/mqttcommand_form.html'
    success_url = reverse_lazy('mqttcommand_list')

class MqttCommandDetailView(DetailView):
    model = MQTTCommand
    template_name = 'smartreader/mqttcommand_detail.html'

class MqttCommandDeleteView(DeleteView):
    model = MQTTCommand
    template_name = 'smartreader/mqttcommand_confirm_delete.html'
    success_url = reverse_lazy('mqttcommand_list')

class SmartReaderListView(ListView):
    model = SmartReader
    template_name = 'smartreader/smartreader_list.html'
    context_object_name = 'smartreaders'
    paginate_by = 10

    def get_queryset(self):
        queryset = SmartReader.objects.all()
        reader_name = self.request.GET.get('reader_name')
        if reader_name:
            queryset = queryset.filter(reader_name__icontains=reader_name)
        return queryset

class SmartReaderDetailView(DetailView):
    model = SmartReader
    template_name = 'smartreader/smartreader_detail.html'
    context_object_name = 'smartreader'

class SmartReaderCreateView(CreateView):
    model = SmartReader
    form_class = SmartReaderForm
    template_name = 'smartreader/smartreader_form.html'
    success_url = reverse_lazy('smartreader_list')

class SmartReaderUpdateView(UpdateView):
    model = SmartReader
    form_class = SmartReaderForm
    template_name = 'smartreader/smartreader_form.html'
    success_url = reverse_lazy('smartreader_list')

class SmartReaderDeleteView(DeleteView):
    model = SmartReader
    template_name = 'smartreader/smartreader_confirm_delete.html'
    success_url = reverse_lazy('smartreader_list')