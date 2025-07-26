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

        with open(csv_full_path, newline='', encoding='latin1') as f:
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
        field_data = request.POST.get('coordinates')
        if field_data:
            original_data = json.loads(field_data)
            # Calculate center points
            centered_data = {}
            for field, coords in original_data.items():
                x = coords['x'] + coords['width'] / 2
                y = coords['y'] + coords['height'] / 2
                centered_data[field] = {'x': x, 'y': y}

            # Save center coordinates to session
            request.session['field_coordinates'] = centered_data
            return redirect('choose_font')  # Proceed to next step

    template_path = request.session.get('template_path')
    headers = request.session.get('headers')

    if not template_path or not headers:
        return redirect('upload_files')

    template_url = default_storage.url(template_path)

    return render(request, 'generator/map_fields.html', {
        'headers': json.dumps(headers),
        'template_url': template_url,
    })
# Font family → style → TTF file mapping
FONT_FILES = {
    'Roboto': {
        'normal': 'Roboto-Regular.ttf',
        'bold': 'Roboto-Bold.ttf',
        'italic': 'Roboto-Italic.ttf',
        'bold_italic': 'Roboto-BoldItalic.ttf',
    },
    'Pacifico': {
        'normal': 'Pacifico-Regular.ttf',
    },
    'Playfair Display': {
        'normal': 'PlayfairDisplay-Regular.ttf',
        'italic': 'PlayfairDisplay-Italic.ttf',
    },
    'Caveat': {
        'normal': 'Caveat-VariableFont_wght.ttf',
    },
    'Great Vibes': {
        'normal': 'GreatVibes-Regular.ttf',
    },
    'Raleway': {
        'normal': 'Raleway-VariableFont_wght.ttf',
        'italic': 'Raleway-Italic-VariableFont_wght.ttf',
    },
    'Poppins': {
        'normal': 'Poppins-Regular.ttf',
        'bold': 'Poppins-Bold.ttf',
        'italic': 'Poppins-Italic.ttf',
    },
    'Dancing Script': {
        'normal': 'DancingScript-VariableFont_wght.ttf',
    },
    'Oswald': {
        'normal': 'Oswald-VariableFont_wght.ttf',
    },
}
def get_font_path(font_family, bold, italic):
    style = 'normal'
    if bold and italic:
        style = 'bold_italic'
    elif bold:
        style = 'bold'
    elif italic:
        style = 'italic'

    font_styles = FONT_FILES.get(font_family, {})
    font_file = font_styles.get(style) or font_styles.get('normal')

    if not font_file:
        return os.path.join(settings.BASE_DIR, 'static/fonts/Roboto-Regular.ttf')  # fallback

    return os.path.join(settings.BASE_DIR, 'static/fonts', font_file)


def choose_font(request):
    template_path = request.session.get('template_path')
    template_url = default_storage.url(template_path)
    coordinates = request.session.get('field_coordinates', {})
    headers = request.session.get('headers', [])

    if not headers or not coordinates:
        return redirect('upload_files')

    if request.method == 'POST':
        font_settings = {}
        for field in headers:
            font = request.POST.get(f"{field}_font")
            size = request.POST.get(f"{field}_size")
            try:
                size = int(size)
            except (TypeError, ValueError):
                size = 40
            color = request.POST.get(f"{field}_color")
            bold = request.POST.get(f"{field}_bold") == 'on'
            italic = request.POST.get(f"{field}_italic") == 'on'
            font_settings[field] = {
                'font': font,
                'size': int(size),
                'color': color,
                'bold' : bold,
                'italic' : italic

            }

        request.session['font_settings'] = font_settings
        return redirect('generate_certificates')

    return render(request, 'generator/choose_font.html', {
        'fields': headers,
        'template_url': template_url,
        'coordinates': coordinates
    })

from PIL import Image, ImageDraw, ImageFont
import os

import csv

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

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
            x = int(coordinates.get(field, {}).get('x', 0))
            y = int(coordinates.get(field, {}).get('y', 0))

            # Get font settings with default fallback
            font_info = font_settings.get(field)
            if not font_info:
                # Default font settings if none provided
                font_info = {
                    'font': 'Roboto',
                    'size': 40,
                    'color': '#000000',
                    'bold': False,
                    'italic': False
                }

            font_path = get_font_path(font_info['font'], font_info.get('bold'), font_info.get('italic'))


            try:
                font = ImageFont.truetype(font_path, font_info['size'])
            except Exception as e:
                print(f"Font load error for {font_info['font']}: {e}" )
                font = ImageFont.load_default()
            print(font,field)

            rgb_color = hex_to_rgb(font_info.get('color', '#000000'))
            draw.text((x, y), value, fill=rgb_color, font=font)


            safe_name = row.get('Name', f"user_{index+1}").replace(' ', '_')
            output_path = f"output/certificate_{index+1}_{safe_name}.pdf"
            img.save(output_path, "PDF")

    return render(request, 'generator/success.html')




