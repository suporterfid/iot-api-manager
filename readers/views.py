from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Reader, TagEvent
from .forms import ReaderForm
from django.http import JsonResponse
import requests
import json
import base64

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
    # Print the HTTP method (GET, POST, etc.)
    print(f"Method: {request.method}")

    # Print the full request headers
    print("Headers:")
    for header, value in request.headers.items():
        print(f"{header}: {value}")
    
    # Print the full request body
    try:
        print("Body:")
        print(request.body.decode('utf-8'))
    except Exception as e:
        print(f"Error reading body: {e}")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=200)
        
        # Handle empty JSON array as a keepalive
        if isinstance(data, list) and not data:
            return JsonResponse({'status': 'keepalive'}, status=204)
        
        for event in data:
            if event.get('eventType') == 'tagInventory':
                tag_inventory = event.get('tagInventoryEvent')
                if tag_inventory:
                    # Determine the reader based on hostname if provided
                    reader = None
                    hostname = event.get('hostname')
                    if hostname:
                        try:
                            reader = Reader.objects.get(name=hostname)
                        except Reader.DoesNotExist:
                            return JsonResponse({'status': 'error', 'message': f'Reader with hostname {hostname} not found'}, status=404)

                    # Handle EPC, checking for either Base64 or Hex format
                    epc_hex = None
                    epc_base64 = tag_inventory.get('epc')
                    if epc_base64:
                        epc_hex = base64.b64decode(epc_base64).hex().upper()
                    else:
                        epc_hex = tag_inventory.get('epcHex')

                    if epc_hex:
                        timestamp = event.get('timestamp')

                        # Parse optional fields
                        antenna_port = tag_inventory.get('antennaPort')
                        antenna_name = tag_inventory.get('antennaName')
                        peak_rssi_cdbm = tag_inventory.get('peakRssiCdbm')
                        frequency = tag_inventory.get('frequency')
                        transmit_power_cdbm = tag_inventory.get('transmitPowerCdbm')
                        last_seen_time_str = tag_inventory.get('lastSeenTime')
                        tid_base64 = tag_inventory.get('tid')
                        tid_hex = tag_inventory.get('tidHex')

                        # Convert last seen time to datetime object if present
                        last_seen_time = None
                        if last_seen_time_str:
                            try:
                                last_seen_time = datetime.fromisoformat(last_seen_time_str.replace('Z', '+00:00'))
                            except ValueError:
                                return JsonResponse({'status': 'error', 'message': 'Invalid lastSeenTime format'}, status=400)

                        # Decode tid from base64 if provided
                        if tid_base64 and not tid_hex:
                            tid_hex = base64.b64decode(tid_base64).hex().upper()

                        # If reader was not found by hostname, use a default or fallback method
                        if reader is None:
                            reader, created = Reader.objects.get_or_create(serial_number='default-serial-number', defaults={'name': 'Default Reader'})

                        # Store the data in the database
                        TagEvent.objects.create(
                            reader=reader,
                            epc=epc_hex,  # Store the hexadecimal EPC
                            timestamp=timestamp,
                            antenna_port=antenna_port if antenna_port is not None and antenna_port > 0 else None,
                            antenna_name=antenna_name,
                            peak_rssi_cdbm=peak_rssi_cdbm if peak_rssi_cdbm is not None and peak_rssi_cdbm < 0 else None,
                            frequency=frequency if frequency is not None and frequency > 0 else None,
                            transmit_power_cdbm=transmit_power_cdbm if transmit_power_cdbm is not None and transmit_power_cdbm > 0 else None,
                            last_seen_time=last_seen_time,
                            tid=tid_base64,
                            tid_hex=tid_hex
                        )
        return JsonResponse({'status': 'ok'})
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
