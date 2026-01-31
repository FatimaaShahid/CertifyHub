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

        # Initialize dict with empty strings for each header
            longest_strings = {header: 0 for header in headers}

            for row in reader:
                # Skip serial number if present
                if len(row) > len(headers):
                    row = row[1:]
                for header, cell in zip(headers, row):
                    if len(cell) > longest_strings[header]:
                        longest_strings[header] = len(cell)

        request.session['longest_strings'] = longest_strings
        request.session['csv_path'] = csv_path
        request.session['template_path'] = template_path
        request.session['headers'] = headers


        return redirect('map_fields')  # This should match the name in urls.py

    return render(request, 'generator/index.html')

import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage

def map_fields(request):
    if request.method == 'POST':
        field_data = request.POST.get('coordinates')
        print("---------------------------------------------")
        print(f"field data : {field_data}")
        if field_data:
            original_data = json.loads(field_data)
            # Calculate center points
            centered_data = {}
            for field, coords in original_data.items():
                centered_data[field] = {
                    'x': coords['x'],
                    'y': coords['y'] ,
                    'width': coords['width'],
                    'height': coords['height'],
                    'default_font_size': coords['height']  # New
                }


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
    longest_strings = request.session.get('longest_strings', {})
    print("-----------------------------------------------------------------------")
    print(f"headers : {headers}")
    print("-----------------------------------------------------------------------")
    print(f"longest_strings : {longest_strings}")
    print("-----------------------------------------------------------------------")
    print(f"coordinates : {coordinates }")

    padded_headers = []
    for header in headers:
        header_len = len(header)
        longest_len = longest_strings.get(header, header_len)

        diff = longest_len - header_len
        if diff > 0:  # Only pad if longest is longer
            if diff % 2 == 0:
                left = right = diff // 2
            else:
                left = diff // 2
                right = left + 1
            padded_header = '-' * left + header + '-' * right
        else:
            padded_header = header

        padded_headers.append(padded_header)
    print("-----------------------------------------------------------------------")
    print("padded headers:" ,padded_headers)

    request.session['padded_headers'] = padded_headers
    fields_combined = list(zip(headers, padded_headers))
    # New: Dynamic default font size calculation & max_font_size
    # ================================
    font_info = {
        'font': 'Roboto',
        'size': 40,
        'color': '#000000',
        'bold': False,
        'italic': False
    }
    font_path = get_font_path(font_info['font'], font_info.get('bold'), font_info.get('italic'))
    for field, padded_text in zip(headers, padded_headers):
        if field in coordinates:
            width = coordinates[field].get('width', 200)
            height = coordinates[field].get('height', 50)

            img = Image.new("RGB", (width, height))
            draw = ImageDraw.Draw(img)

            # === Calculate max possible font size ===
            max_size_try = 500  # Large starting point
            while max_size_try >= 5:
                try:
                    font = ImageFont.truetype(font_path, max_size_try)
                except Exception:
                    font = ImageFont.load_default()

                text_bbox = draw.textbbox((0, 0), padded_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                if text_width <= width and text_height <= height:
                    break
                max_size_try -= 1

            max_font_size = max_size_try

            # === Default font size can be set as 70% of max ===
            default_font_size = int(max_font_size * 0.7)

            coordinates[field]['max_font_size'] = max_font_size
            coordinates[field]['default_font_size'] = default_font_size

            print(f"'{field}' => Max: {max_font_size}, Default: {default_font_size}")


    if not headers or not coordinates:
        return redirect('upload_files')

    if request.method == 'POST':
        if request.POST.get('action') == 'back':
            return redirect('map_fields')

        font_settings = {}
        updated_coordinates = {}

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
            # Coordinates
            adj_x = request.POST.get(f"{field}_adj_x")
            adj_y = request.POST.get(f"{field}_adj_y")
            text_w = request.POST.get(f"{field}_text_width")
            text_h = request.POST.get(f"{field}_text_height")

            updated_coordinates[field] = {
                'x': float(adj_x) if adj_x else float(request.POST.get(f"{field}_x", 0)),
                'y': float(adj_y) if adj_y else float(request.POST.get(f"{field}_y", 0)),
                'width': float(text_w) if text_w else coordinates.get(field, {}).get('width', 200),
                'height': float(text_h) if text_h else coordinates.get(field, {}).get('height', 50),
            }
        print(updated_coordinates,'aaaaaaaa')


        request.session['font_settings'] = font_settings
        request.session['final_coordinates'] = updated_coordinates
        return redirect('generate_certificates')

    return render(request, 'generator/choose_font.html', {
        'fields': headers,
        'display_fields': padded_headers,
        'template_url': template_url,
        'fields_combined': fields_combined,
        'coordinates': coordinates
    })

from PIL import Image, ImageDraw, ImageFont
import os

import csv

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

import glob

def clear_output_folder():
    files = glob.glob('output/*')
    for f in files:
        os.remove(f)


def generate_certificates(request):
    # Retrieve paths and configs
    csv_path = request.session.get('csv_path')
    template_path = request.session.get('template_path')
    coordinates = request.session.get('final_coordinates') or request.session.get('field_coordinates', {})
    font_settings = request.session.get('font_settings', {})

    clear_output_folder()

    # Safety check
    if not all([csv_path, template_path, coordinates, font_settings]):
        return redirect('upload_files')

    csv_full_path = os.path.join(settings.MEDIA_ROOT, csv_path)
    csv_data = []

    with open(csv_full_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row.pop('s.no', None)
            row.pop('S.No', None)
            csv_data.append(row)

    # Ensure output directory
    if not os.path.exists('output'):
        os.makedirs('output')

    for index, row in enumerate(csv_data):
        img = Image.open(os.path.join(settings.MEDIA_ROOT, template_path)).convert("RGB")
        draw = ImageDraw.Draw(img)

        for field, value in row.items():
            field_coords = coordinates.get(field, {})
            font_info = font_settings.get(field, {
                'font': 'Roboto',
                'size': 40,
                'color': '#000000',
                'bold': False,
                'italic': False
            })

            # Get font path + settings
            font_path = get_font_path(font_info['font'], font_info.get('bold'), font_info.get('italic'))
            font_size = int(font_info['size'])
            rgb_color = hex_to_rgb(font_info.get('color', '#000000'))

            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                print(f"Font load error for {font_info['font']} size {font_size}: {e}")
                font = ImageFont.load_default()

            # Use FINAL COORDINATES from frontend (already adjusted)
            x = int(field_coords.get('x', 0))
            y = int(field_coords.get('y', 0))
            text_width = int(field_coords.get('width', 200))
            text_height = int(field_coords.get('height', 50))

            # Reduction loop before drawing text
            max_width = text_width
            max_height = text_height
            current_size = font_size

            while True:
                font = ImageFont.truetype(font_path, current_size)
                bbox = draw.textbbox((0, 0), value, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]

                if tw <= max_width and th <= max_height:
                    break
                current_size -= 1
                if current_size < 8:
                    break

            # Finally, center text within the rectangle (optional)
            text_x = x + (max_width - tw) // 2
            text_y = y + (max_height - th) // 2

            draw.text((text_x, text_y), value, fill=rgb_color, font=font)

            # Draw text at final coordinates
            #draw.text((x, y), value, fill=rgb_color, font=font)

            # Optional: draw bounding boxes (debugging)
            # draw.rectangle([x, y, x + text_width, y + text_height], outline="blue", width=2)

            print(f"Placed field '{field}' at ({x}, {y}) with size {font_size}")

        safe_name = row.get('Name', f"user_{index+1}").replace(' ', '_')
        output_path = f"output/certificate_{index+1}_{safe_name}.pdf"
        img.save(output_path, "PDF")

    return render(request, 'generator/success.html')

from zipfile import ZipFile
from django.http import FileResponse
import io

def download_certificates(request):
    output_folder = 'output'  # Path where certificates are saved
    zip_io = io.BytesIO()  # In-memory zip file

    with ZipFile(zip_io, 'w') as zip_file:
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            zip_file.write(file_path, arcname=filename)

    zip_io.seek(0)
    return FileResponse(zip_io, as_attachment=True, filename='certificates.zip')
