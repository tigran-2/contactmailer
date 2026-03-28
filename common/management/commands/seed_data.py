from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from contacts.models import Contact
from campaigns.models import Campaign
import logging

class Command(BaseCommand):
    help = 'Seeds the database with initial data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1. Create Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Successfully created superuser (admin/admin)'))
        else:
            self.stdout.write('Superuser "admin" already exists.')

        # 2. Create Sample Contacts
        contacts_data = [
            {'name': 'Test Alpha', 'email': 'alpha@test.local', 'company': 'Test Co', 'tags': 'VIP'},
            {'name': 'Test Beta', 'email': 'beta@test.local', 'company': 'Test Co', 'tags': 'Standard'},
            {'name': 'Test Gamma', 'email': 'gamma@test.local', 'company': 'Other Ltd', 'tags': 'VIP;Standard'},
        ]
        
        for cdata in contacts_data:
            Contact.objects.get_or_create(email=cdata['email'], defaults=cdata)
        
        self.stdout.write(self.style.SUCCESS(f'Ensured {len(contacts_data)} sample contacts exist.'))

        # 3. Create Sample Campaigns
        campaigns_data = [
            {'subject': 'Welcome Campaign', 'body_text': 'Hello world!', 'target_tag': 'VIP', 'status': 'Draft'},
            {'subject': 'Monthly Newsletter', 'body_text': 'Here is our news...', 'target_tag': '', 'status': 'Draft'},
        ]

        for camdata in campaigns_data:
            Campaign.objects.get_or_create(subject=camdata['subject'], defaults=camdata)

        self.stdout.write(self.style.SUCCESS(f'Ensured {len(campaigns_data)} sample campaigns exist.'))
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
