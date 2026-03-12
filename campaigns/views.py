import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from .models import Campaign
from .forms import CampaignForm
from contacts.models import Contact
from common.emailer import send_bulk_emails
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
            messages.error(request, f"Cannot reach SMTP host ({host}). Check logs for details.")
            return redirect('campaigns:campaign_list')
            
        # 2. Get contacts
        if campaign.target_tag:
            contacts = Contact.objects.filter(tags__icontains=campaign.target_tag)
        else:
            contacts = Contact.objects.all()
            
        if not contacts.exists():
            messages.warning(request, "No contacts found for this campaign.")
            return redirect('campaigns:campaign_list')
            
        # 3. Prepare recipients list
        recipients = [
            {'name': c.name, 'email': c.email, 'company': c.company, 'tags': c.tags}
            for c in contacts
        ]
        
        # 4. Update status and trigger
        campaign.status = "Sending"
        campaign.save()
        
        # Call the bulk emailer which uses ThreadPoolExecutor internally
        send_bulk_emails(str(campaign.id), campaign.subject, campaign.body_text, recipients)
        
        campaign.status = "Completed"
        campaign.save()
        
        messages.success(request, f"Campaign '{campaign.subject}' triggered for {len(recipients)} contacts.")
        return redirect('campaigns:campaign_list')
        
    return redirect('campaigns:campaign_list')
