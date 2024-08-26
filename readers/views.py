from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.safestring import mark_safe
from datetime import timedelta
from .models import Reader, Preset, TagEvent
from .forms import ReaderForm, PresetForm
from django.http import JsonResponse
from django.http import HttpResponse
from .tasks import process_webhook_data
import csv
import requests
import json
import base64
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@login_required
def reader_list(request):
    readers = Reader.objects.all()
    
    # Create a dictionary to store the active preset for each reader
    active_presets = {}
    
    for reader in readers:
        active_presets[reader.pk] = reader.active_preset.preset_id if reader.active_preset else None
    
    context = {
        'readers': readers,
        'active_presets': active_presets,
    }
    return render(request, 'readers/reader_list.html', context)

@login_required
def reader_create(request):
    if request.method == 'POST':
        form = ReaderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('reader_list')
    else:
        form = ReaderForm()
    return render(request, 'readers/reader_form.html', {'form': form})

@login_required
def reader_update(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    if request.method == 'POST':
        form = ReaderForm(request.POST, instance=reader)
        if form.is_valid():
            form.save()
            return redirect('reader_list')
    else:
        form = ReaderForm(instance=reader)
    return render(request, 'readers/reader_form.html', {'form': form})

@login_required
def reader_delete(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    reader.delete()
    return redirect('reader_list')

@login_required
def query_presets(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    url = f"https://{reader.ip_address}:{reader.port}/api/v1/profiles/inventory/presets"
    print(f"url for preset list {url}")
    auth = (reader.username, reader.password)
    
    try:
        response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'}, verify=False)
        response.raise_for_status()
        preset_ids = response.json()
        
        print(f"Preset IDs retrieved from reader {reader.name} ({reader.ip_address}): {preset_ids}")
        
        for preset_id in preset_ids:
            # Check if preset already exists in the database
            preset, created = Preset.objects.get_or_create(
                reader=reader, 
                preset_id=preset_id, 
                defaults={'configuration': {}}
            )
            
            if created:
                # If created, fetch the preset details from the reader
                detail_url = f"https://{reader.ip_address}:{reader.port}/api/v1/profiles/inventory/presets/{preset_id}"
                print(f"url for preset {detail_url}")
                try:
                    detail_response = requests.get(detail_url, auth=auth, headers={'Content-Type': 'application/json'}, verify=False)
                    detail_response.raise_for_status()
                    preset.configuration = detail_response.json()
                    print(f"Configuration for preset '{preset_id}': {preset.configuration}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to retrieve configuration for preset '{preset_id}': {e}")
                    preset.configuration = {}
                preset.save()  # Save the preset with the fetched or default configuration
            else:
                print(f"Preset '{preset_id}' already exists in the database.")

        # Get all presets associated with this reader
        presets = Preset.objects.filter(reader=reader)
        return JsonResponse({'presets': list(presets.values('id', 'preset_id'))})

    except requests.exceptions.RequestException as e:
        print(f"Error querying presets from reader {reader.name} ({reader.ip_address}): {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def get_preset_details(request, reader_id, preset_id):
    reader = get_object_or_404(Reader, pk=reader_id)
    preset = get_object_or_404(Preset, reader=reader, preset_id=preset_id)
    
    data = {
        'reader_name': reader.name,
        'reader_ip': reader.ip_address,
        'preset_configuration': json.dumps(preset.configuration, indent=2)  # Formatting JSON
    }
    
    return JsonResponse(data)

@login_required
def start_preset(request, pk):
    logger.debug(f"Received PK: {pk}")
    reader = get_object_or_404(Reader, pk=pk)
    selected_preset_id = request.POST.get('preset_id')

    # Log the selected preset ID and available presets for this reader
    logger.debug(f"Selected Preset ID: {selected_preset_id}")
    logger.debug(f"Available Presets: {[preset.preset_id for preset in reader.presets.all()]}")

    # Fetch the preset
    try:
        preset = get_object_or_404(Preset, reader=reader, preset_id=selected_preset_id)
    except Preset.DoesNotExist:
        logger.error(f"No Preset matches the given query: Reader ID = {pk}, Preset ID = {selected_preset_id}")
        return JsonResponse({'status': 'error', 'message': f'Preset not found: {selected_preset_id}'}, status=404)

    if preset.preset_id != 'default':
        # Update the reader with the selected preset configuration
        update_url = f"https://{reader.ip_address}:{reader.port}/api/v1/profiles/inventory/presets/{preset.preset_id}"
        auth = (reader.username, reader.password)
        logger.debug(f"Selected Preset: {preset.configuration}")
        try:
            response = requests.put(update_url, json=preset.configuration, auth=auth, headers={'Content-Type': 'application/json'}, verify=False)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            messages.success(request, 'Preset started successfully.')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating preset {preset.preset_id} on reader {reader.name}: {str(e)}")
            #return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            messages.error(request, f'Error updating preset: {str(e)}')
            return redirect('reader_list')
        
    # Set all presets for this reader to inactive
    reader.presets.update(is_active=False)

    # Set the selected preset as active
    preset.is_active = True
    preset.save()

    # Update the active preset in the database
    reader.active_preset = preset
    reader.save()

    # Call the preset start endpoint
    start_url = f"https://{reader.ip_address}:{reader.port}/api/v1/profiles/inventory/presets/{preset.preset_id}/start"
    try:
        start_response = requests.post(start_url, auth=auth, verify=False)
        start_response.raise_for_status()  # Raise an HTTPError for bad responses
        # return JsonResponse({'status': 'started'})
        messages.success(request, 'Preset started successfully.')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error starting preset {preset.preset_id} on reader {reader.name}: {str(e)}")
        # return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        messages.error(request, f'Error starting preset: {str(e)}')
    return redirect('reader_list')

@login_required
def stop_preset(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    # Call the preset stop endpoint
    url = f'https://{reader.ip_address}:{reader.port}/api/v1/profiles/stop'
    try:
        response = requests.post(url, auth=(reader.username, reader.password), verify=False)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        messages.success(request, 'Preset stopped successfully.')
        #return JsonResponse({'status': 'stopped'})
    except requests.exceptions.RequestException as e:
        # return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        messages.error(request, f'Error stopping preset: {str(e)}')
    return redirect('reader_list')

@csrf_exempt
def webhook_receiver(request):
    logger.info(f"Method: {request.method}")
    logger.info("Headers:")
    for header, value in request.headers.items():
        logger.info(f"{header}: {value}")

    try:
        logger.info("Body:")
        logger.info(request.body.decode('utf-8'))
    except Exception as e:
        logger.error(f"Error reading body: {e}")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=200)
        
        # Handle empty JSON array as a keepalive
        if isinstance(data, list) and not data:
            return JsonResponse({'status': 'keepalive'}, status=204)

        try:
            process_webhook_data.delay(data)
        except Exception as e:
            logger.error(f"Error queuing task: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
        return JsonResponse({'status': 'queued'})
    
    return JsonResponse({'status': 'bad request'}, status=400)

@login_required
def tag_event_list(request):
    readers = Reader.objects.all()
    tags = TagEvent.objects.all()
    
     # Define columns dictionary
    columns = {
        'reader': 'Reader',
        'epc': 'EPC',
        'timestamp': 'Timestamp'
    }

    # Filtering
    reader_id = request.GET.get('reader')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if reader_id:
        tags = tags.filter(reader__id=reader_id)
    if start_date:
        tags = tags.filter(timestamp__gte=start_date)
    if end_date:
        tags = tags.filter(timestamp__lte=end_date)
    
    # Sorting
    sort = request.GET.get('sort', 'timestamp')  # Default sort by timestamp
    direction = request.GET.get('direction', 'desc')
    direction_toggle = 'asc' if direction == 'desc' else 'desc'
    if sort:
        if direction == 'asc':
            tags = tags.order_by(sort)
        else:
            tags = tags.order_by(f'-{sort}')

    # Pagination
    paginator = Paginator(tags, 10)  # Show 10 tags per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    

    context = {
        'readers': readers,
        'columns': columns,  # Pass the columns to the template
        'tags': page_obj,  # Pass the page object instead of the full queryset
        'sort': sort,
        'direction': direction,
        'direction_toggle': direction_toggle,
        'page_obj': page_obj,  # Pass the page object to the template
    }
    return render(request, 'readers/tag_event_list.html', context)

@login_required
def tag_event_details(request, event_id):
    try:
        event = TagEvent.objects.get(pk=event_id)
        
        # Serialize the tag event data to return as JSON
        data = {
            'epc': event.epc,
            'timestamp': event.timestamp,
            'antenna_port': event.antenna_port,
            'peak_rssi_cdbm': event.peak_rssi_cdbm,
            'frequency': event.frequency,
            'transmit_power_cdbm': event.transmit_power_cdbm,
            'last_seen_time': event.last_seen_time,
            'tid': event.tid,
            'tid_hex': event.tid_hex,
        }
        
        return JsonResponse(data)
    except TagEvent.DoesNotExist:
        return JsonResponse({'error': 'Tag event not found'}, status=404)

@login_required
def export_tag_events(request):
    # Filtering logic (same as in the list view)
    tags = TagEvent.objects.all()
    reader_id = request.GET.get('reader')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if reader_id:
        tags = tags.filter(reader__id=reader_id)
    if start_date:
        tags = tags.filter(timestamp__gte=start_date)
    if end_date:
        tags = tags.filter(timestamp__lte=end_date)
    
    # Sorting logic (same as in the list view)
    sort = request.GET.get('sort', 'timestamp')
    direction = request.GET.get('direction', 'desc')
    if direction == 'asc':
        tags = tags.order_by(sort)
    else:
        tags = tags.order_by(f'-{sort}')
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tag_events.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Reader', 'EPC', 'Timestamp'])
    
    for tag in tags:
        writer.writerow([tag.reader.name, tag.epc, tag.timestamp])
    
    return response

@login_required
def dashboard(request):
    # Calculate time ranges
    now = timezone.now()
    three_hours_ago = now - timedelta(hours=3)
    one_hour_ago = now - timedelta(hours=1)

    # Get the count of readers that have not sent events in the last 3 hours
    readers_with_recent_events = TagEvent.objects.filter(timestamp__gte=three_hours_ago).values('reader').distinct()
    inactive_readers_count = Reader.objects.exclude(id__in=readers_with_recent_events).count()

    # Get the count of tag events received in the last hour
    tag_events_last_hour = TagEvent.objects.filter(timestamp__gte=one_hour_ago).count()

    context = {
        'inactive_readers_count': inactive_readers_count,
        'tag_events_last_hour': tag_events_last_hour,
    }
    
    return render(request, 'readers/dashboard.html', context)

class PresetListView(ListView):
    model = Preset
    template_name = 'readers/preset_list.html'
    context_object_name = 'presets'

    def get_queryset(self):
        reader_id = self.kwargs['reader_id']
        return Preset.objects.filter(reader_id=reader_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reader_id = self.kwargs['reader_id']
        context['reader'] = get_object_or_404(Reader, pk=reader_id)

         # Format the configuration JSON
        for preset in context['presets']:
            preset.configuration = mark_safe(json.dumps(preset.configuration, indent=2))

        return context
    
class PresetCreateView(CreateView):
    model = Preset
    form_class = PresetForm
    template_name = 'readers/preset_form.html'

    def form_valid(self, form):
        form.instance.reader = get_object_or_404(Reader, pk=self.kwargs['reader_id'])
        response = super().form_valid(form)
        # Send the preset to the reader
        preset = form.instance
        preset.send_to_reader()
        return response

class PresetUpdateView(UpdateView):
    model = Preset
    form_class = PresetForm
    template_name = 'readers/preset_form.html'

    def form_valid(self, form):
        preset = form.save(commit=False)
        preset.reader = get_object_or_404(Reader, pk=self.kwargs['pk'])
        preset.save()
        preset.send_to_reader()
        if self.request.is_ajax():
            return JsonResponse({'status': 'success'})
        return super().form_valid(form)

class PresetDeleteView(DeleteView):
    model = Preset
    template_name = 'readers/preset_confirm_delete.html'
    success_url = reverse_lazy('reader_list')

    def delete(self, request, *args, **kwargs):
        preset = self.get_object()
        # Send delete request to the reader
        preset.delete_from_reader()
        return super().delete(request, *args, **kwargs)