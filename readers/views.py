from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Reader, TagEvent
from .forms import ReaderForm
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

def reader_list(request):
    readers = Reader.objects.all()
    return render(request, 'readers/reader_list.html', {'readers': readers})

def reader_create(request):
    if request.method == 'POST':
        form = ReaderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('reader_list')
    else:
        form = ReaderForm()
    return render(request, 'readers/reader_form.html', {'form': form})

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

def reader_delete(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    reader.delete()
    return redirect('reader_list')

def start_preset(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    preset_id = reader.preset_id if reader.preset_id else 'default'  # Use 'default' if no preset_id is specified
    # Call the preset start endpoint
    url = f'https://{reader.ip_address}:{reader.port}/api/v1/profiles/inventory/presets/{preset_id}/start'
    try:
        response = requests.post(url, auth=(reader.username, reader.password), verify=False)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return JsonResponse({'status': 'started'})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def stop_preset(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    # Call the preset stop endpoint
    url = f'https://{reader.ip_address}:{reader.port}/api/v1/profiles/stop'
    try:
        response = requests.post(url, auth=(reader.username, reader.password), verify=False)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return JsonResponse({'status': 'stopped'})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

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