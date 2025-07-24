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

def choose_font(request):
    if request.method == 'POST':
        font_settings = {}
        headers = request.session.get('headers', [])

        for field in headers:
            font = request.POST.get(f"{field}_font")
            size = request.POST.get(f"{field}_size")
            font_settings[field] = {'font': font, 'size': int(size)}

        request.session['font_settings'] = font_settings
        return redirect('generate_certificates')

    headers = request.session.get('headers', [])
    if not headers:
        return redirect('upload_files')

    return render(request, 'generator/choose_font.html', {'fields': headers})
from PIL import Image, ImageDraw, ImageFont
import os

import csv

def generate_certificates(request):
    # Retrieve paths and configs
    csv_path = request.session.get('csv_path')
    template_path = request.session.get('template_path')
    coordinates = request.session.get('field_coordinates', {})
    font_settings = request.session.get('font_settings', {})

    # Safety check
    if not all([csv_path, template_path, coordinates, font_settings]):
        return redirect('upload_files')

    csv_full_path = os.path.join(settings.MEDIA_ROOT, csv_path)
    csv_data = []

    with open(csv_full_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 's.no' in row:
                del row['s.no']
            elif 'S.No' in row:
                del row['S.No']
            csv_data.append(row)

    # Ensure output directory
    if not os.path.exists('output'):
        os.makedirs('output')

    # Generate certificates
    for index, row in enumerate(csv_data):
        img = Image.open(os.path.join(settings.MEDIA_ROOT, template_path)).convert("RGB")
        draw = ImageDraw.Draw(img)

        for field, value in row.items():
            x, y = coordinates.get(field, (0, 0))
            font_info = font_settings.get(field, {'font': 'arial.ttf', 'size': 40})
            try:
                font = ImageFont.truetype(font_info['font'], font_info['size'])
            except:
                font = ImageFont.load_default()
            draw.text((x, y), value, fill='black', font=font)

        safe_name = row.get('Name', f"user_{index+1}").replace(' ', '_')
        output_path = f"output/certificate_{index+1}_{safe_name}.pdf"
        img.save(output_path, "PDF")

    return render(request, 'generator/success.html')



