from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = 'files/ticket-base.png'
FONT_PATH = 'files/Abel-Regular.ttf'
FONT_PATH_NAME = 'files/Roboto-Regular.ttf'
FONT_SIZE = 60

BLACK = (0, 0, 0, 255)
NAME_OFFSET = (800, 610)
EMAIL_OFFSET = (800, 770)

AVATAR_SIZE = 200
AVATAR_OFFSET = (410, 670)


def generate_ticket(name, email):
    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    font_name =  ImageFont.truetype(FONT_PATH_NAME, FONT_SIZE)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    draw = ImageDraw.Draw(base)
    draw.text(NAME_OFFSET, name, font=font_name, fill=BLACK)
    draw.text(EMAIL_OFFSET, email, font=font, fill=BLACK)

    response = requests.get(url=f'https://api.adorable.io/avatars/{AVATAR_SIZE}/{email}')
    avatar_file_like = BytesIO(response.content)
    avatar = Image.open(avatar_file_like)

    base.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file