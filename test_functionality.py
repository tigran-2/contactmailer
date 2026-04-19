import os
import django
import urllib.request
import json
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contactmailer.settings')
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from contacts.models import Contact
from campaigns.models import Campaign
from campaigns.views import campaign_trigger

def run_tests():
    c = Client(SERVER_NAME='localhost')
    print("Testing contact_list...")
    response = c.get('/contacts/')
    assert response.status_code == 200
    print("contact_list OK.")

    print("Testing import_csv...")
    csv_content = b"Name,Email,Company,Tags\nTest User,test@import.local,TestCorp,tag1,tag2\n"
    csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
    
    response = c.post('/contacts/import/', {
        'csv_file': csv_file,
        'map_name': 'Name',
        'map_email': 'Email',
        'map_company': 'Company',
        'map_tags': 'Tags'
    })
    assert response.status_code == 302
    assert Contact.objects.filter(email='test@import.local').exists()
    print("import_csv OK.")

    print("Testing export_csv...")
    response = c.get('/contacts/export/')
    assert response.status_code == 200
    assert b'test@import.local' in response.content
    print("export_csv OK.")

    print("Testing campaign_list...")
    response = c.get('/campaigns/')
    assert response.status_code == 200
    print("campaign_list OK.")

    print("Testing campaign_create...")
    response = c.post('/campaigns/create/', {
        'subject': 'Integration Test Campaign',
        'body_text': 'This is an integration test.',
        'target_tag': 'tag1'
    })
    assert response.status_code == 302
    camp = Campaign.objects.filter(subject='Integration Test Campaign').first()
    assert camp is not None
    print("campaign_create OK.")

    print("Testing campaign_trigger...")
    from django.test import RequestFactory
    from django.contrib.messages.storage.fallback import FallbackStorage
    request = RequestFactory().post(f'/campaigns/{camp.id}/trigger/', SERVER_NAME='localhost')
    setattr(request, 'session', 'session')
    setattr(request, '_messages', FallbackStorage(request))
    response = campaign_trigger(request, camp.id)
    assert response.status_code == 302
    print("campaign_trigger OK.")

    print("Testing Mailpit delivery...")
    # Fetch from mailpit to see if message arrived
    req = urllib.request.Request('http://mailpit:8025/api/v1/messages')
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        messages = [m['Subject'] for m in data.get('messages', [])]
        assert 'Integration Test Campaign' in messages
    print("Mailpit delivery OK.")

if __name__ == '__main__':
    run_tests()
