from PIL import Image, ImageDraw, ImageFont
import os

def generate_certificates(template_path, data_rows):
    font = ImageFont.truetype("arial.ttf", 40)

    if not os.path.exists('output'):
        os.makedirs('output')

    for index, row in enumerate(data_rows):
        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)

        draw.text((500, 300), row['Name'], fill='black', font=font)
        draw.text((500, 400), row['Winning Category'], fill='black', font=font)

        name_safe = row['Name'].replace(' ', '_').replace('/', '_')
        output_path = f"output/certificate_{index + 1}_{name_safe}.pdf"
        img.save(output_path, "PDF")
