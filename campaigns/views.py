import logging
import json
import time
import socket
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import StreamingHttpResponse, JsonResponse

from .models import Campaign
from .forms import CampaignForm
from contacts.models import Contact
from common.emailer import start_bulk_emails_in_background
from common.progress_socket import HOST as SOCKET_HOST, PORT as SOCKET_PORT
from common.subprocess_tools import check_smtp_host
from common.decorators import log_time, safe

logger = logging.getLogger('contactmailer')

@log_time
def campaign_list(request):
    campaigns = Campaign.objects.all().order_by('-id')
    return render(request, 'campaigns/campaign_list.html', {'campaigns': campaigns})

@safe
@log_time
def campaign_create(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign created successfully.")
            return redirect('campaigns:campaign_list')
    else:
        form = CampaignForm()
    return render(request, 'campaigns/campaign_form.html', {'form': form})

@safe
@log_time
def campaign_trigger(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    
    if request.method == 'POST':
        # 1. Subprocess check for external SMTP host
        host = settings.EMAIL_HOST
        is_reachable = check_smtp_host(host)
        if not is_reachable:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
                return JsonResponse({"error": f"Cannot reach SMTP host ({host})."}, status=400)
            messages.error(request, f"Cannot reach SMTP host ({host}). Check logs for details.")
            return redirect('campaigns:campaign_list')
            
        # 2. Get contacts
        if campaign.target_tag:
            contacts = Contact.objects.filter(tags__icontains=campaign.target_tag)
        else:
            contacts = Contact.objects.all()
            
        if not contacts.exists():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
                return JsonResponse({"error": "No contacts found for this campaign."}, status=400)
            messages.warning(request, "No contacts found for this campaign.")
            return redirect('campaigns:campaign_list')
            
        # 3. Prepare recipients list
        recipients = [
            {'name': c.name, 'email': c.email, 'company': c.company, 'tags': c.tags}
            for c in contacts
        ]
        
        # 4. Trigger background task
        start_bulk_emails_in_background(campaign, recipients)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
            return JsonResponse({"status": "started"})
        
        messages.success(request, f"Campaign '{campaign.subject}' triggered for {len(recipients)} contacts.")
        return redirect('campaigns:campaign_list')
        
    return redirect('campaigns:campaign_list')

def campaign_progress_view(request, pk):
    campaign_id_str = str(pk)
    
    def event_stream():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(30.0) # Longer timeout for the stream
                s.connect((SOCKET_HOST, SOCKET_PORT))
                buffer = ""
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    buffer += data.decode('utf-8')
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue
                        
                        try:
                            msg_data = json.loads(line)
                            if str(msg_data.get('campaign_id')) == campaign_id_str:
                                # Calculate completion status
                                total = msg_data.get('total', 0)
                                sent = msg_data.get('sent', 0)
                                failed = msg_data.get('failed', 0)
                                if total > 0 and (sent + failed) >= total:
                                    msg_data['status'] = 'completed'
                                
                                yield f"data: {json.dumps(msg_data)}\n\n"
                                
                                if msg_data.get('status') == 'completed':
                                    return
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"SSE Socket Bridge Error: {e}")
            yield f"data: {json.dumps({'error': 'Lost connection to progress server'})}\n\n"
            
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
