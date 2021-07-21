from flask import Flask, request
from flask.helpers import send_file

from rembg.bg import remove
import numpy as np
import io
from PIL import Image

# 옵션을 선언 OSError: image file is truncated
from PIL import ImageFile 
ImageFile.LOAD_TRUNCATED_IMAGES = True

app = Flask(__name__)

@app.route('/api/resume_photo/rembg', methods=['POST'])
def main():
    photo = request.files['photo']
    id = request.form['id']

    input_path = './examples/' + id + '.jpg'
    output_path = './examples/' + id + 'out.png'

    with open(input_path, 'wb') as f:
        f.write(photo.read())

    f = np.fromfile(input_path)
    result = remove(f)
    img = Image.open(io.BytesIO(result)).convert("RGBA")
    img.save(output_path)

    return send_file(output_path, mimetype='image/png')

@app.route('/api/resume_photo/background_synthesis_solid', methods=['POST'])
def background_synthesis_solid():
    photo = request.files['photo']
    id = request.form['id']
    solid_color = request.form['solid_color']

    input_path = './examples/' + id + 'outcolor.png'
    with open(input_path, 'wb') as f:
        f.write(photo.read())

    color = tuple(map(int, solid_color.split(', '))) # str to tuple

    with Image.open(input_path) as fg:
        with Image.new('RGBA', fg.size, color) as bg:
            canvas_img = Image.alpha_composite(bg, fg)
            canvas_img = canvas_img.convert('RGB')
            canvas_img.save(input_path, 'JPEG', quality=20)

    return send_file(input_path, mimetype='image/png')

@app.route('/api/resume_photo/background_synthesis_gradation', methods=['POST'])
def background_synthesis_gradation():
    photo = request.files['photo']
    id = request.form['id']
    gradation_photo = request.files['gradation_photo']

    input_path = './examples/' + id + 'outcolor.png'
    back_path = './examples/' + id + 'outcolorback.png'
    with open(input_path, 'wb') as f:
        f.write(photo.read())
    with open(back_path, 'wb') as f:
        f.write(gradation_photo.read())

    fg = Image.open(input_path).convert('RGBA') # 원본
    bg = Image.open(back_path) # 배경
    w, h = fg.width, fg.height
    bg = bg.resize((w, h))

    for y in range(h):
        for x in range(w):
            r, g, b, a = fg.getpixel((x,y))
            if a>128: # If foreground is opaque, overwrite background with foreground
                bg.putpixel((x,y), (r,g,b))

    bg.save('examples/result.png')

    return send_file('examples/result.png', mimetype='image/png')

app.run(host="127.0.0.1", port="8080", debug=True)
