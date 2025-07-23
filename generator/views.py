# views.py
import os
import csv
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def upload_files(request):
    if request.method == 'POST':
        csv_file = request.FILES['data_file']
        template_file = request.FILES['template_file']

        fs = FileSystemStorage(location='media/')
        csv_path = fs.save(csv_file.name, csv_file)
        template_path = fs.save(template_file.name, template_file)

        # Full CSV path
        csv_full_path = os.path.join(settings.MEDIA_ROOT, csv_path)

        with open(csv_full_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers[0].lower() in ['s.no', 'sno']:
                headers = headers[1:]

        request.session['csv_path'] = csv_path
        request.session['template_path'] = template_path
        request.session['headers'] = headers

        return redirect('map_fields')  # This should match the name in your urls.py

    return render(request, 'generator/index.html')

import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage

def map_fields(request):
    if request.method == 'POST':
        field_data = request.POST.get('field_data')
        request.session['field_coordinates'] = json.loads(field_data)
        return redirect('choose_font')  # Next step

    template_path = request.session.get('template_path')
    headers = request.session.get('headers')

    if not template_path or not headers:
        return redirect('upload_files')

    template_url = default_storage.url(template_path)

    return render(request, 'generator/map_fields.html', {
        'headers': json.dumps(headers),
        'template_url': template_url,
    })

