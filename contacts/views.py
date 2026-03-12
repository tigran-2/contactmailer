import logging
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q

from .models import Contact
from .forms import CSVImportForm
from common.csv_tools import parse_csv, generate_csv
from common.decorators import log_time, safe

logger = logging.getLogger('contactmailer')

@log_time
def contact_list(request):
    query = request.GET.get('q', '')
    if query:
        contacts_qs = Contact.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query)
        ).order_by('-id')
    else:
        contacts_qs = Contact.objects.all().order_by('-id')

    paginator = Paginator(contacts_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'contacts/contact_list.html', {'page_obj': page_obj, 'query': query})

@safe
@log_time
def import_csv(request):
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            file_data = csv_file.read().decode('utf-8')
            
            mapping = {
                form.cleaned_data['map_name']: 'name',
                form.cleaned_data['map_email']: 'email',
            }
            if form.cleaned_data.get('map_company'):
                mapping[form.cleaned_data['map_company']] = 'company'
            if form.cleaned_data.get('map_tags'):
                mapping[form.cleaned_data['map_tags']] = 'tags'

            parsed_data = parse_csv(file_data, mapping)
            
            created_count = 0
            error_count = 0
            for row in parsed_data:
                try:
                    Contact.objects.update_or_create(
                        email=row['email'],
                        defaults=row
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(f"Error saving contact {row.get('email')}: {e}")
                    error_count += 1

            messages.success(request, f"Imported {created_count} contacts. Errors: {error_count}.")
            return redirect('contacts:contact_list')
    else:
        form = CSVImportForm()

    return render(request, 'contacts/import_csv.html', {'form': form})

@log_time
def export_csv(request):
    contacts = Contact.objects.all()
    
    # We will export a generic structure
    columns = ['id', 'name', 'email', 'company', 'tags']
    data = []
    
    for c in contacts:
        data.append({
            'id': str(c.id),
            'name': c.name,
            'email': c.email,
            'company': c.company,
            'tags': c.tags
        })
        
    csv_string = generate_csv(data, columns)
    
    response = HttpResponse(csv_string, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts_export.csv"'
    return response

