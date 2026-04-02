#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ml_ids_project.settings')
django.setup()
from api.models import LogEntry, ResponseRule

print('Log entries:')
for l in LogEntry.objects.all().order_by('-timestamp')[:50]:
    print(l.timestamp, l.action, l.target, l.result, l.details)

print('\nResponse rules trigger counts:')
for r in ResponseRule.objects.all():
    print(r.id, r.name, r.triggered_count)
