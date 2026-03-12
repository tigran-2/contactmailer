from django import forms
from .models import Contact

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='Upload CSV File')
    
    # Mapping fields
    map_name = forms.CharField(label='CSV Column for Name', initial='Name')
    map_email = forms.CharField(label='CSV Column for Email', initial='Email')
    map_company = forms.CharField(label='CSV Column for Company', initial='Company', required=False)
    map_tags = forms.CharField(label='CSV Column for Tags', initial='Tags', required=False)
