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

app.run(host="127.0.0.1", port="8080", debug=True)
