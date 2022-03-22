from flask import Flask, request
from flask.helpers import send_file
from flask_restx import Api, Resource
import json

from rembg.bg import remove
import numpy as np
import io
import os
from PIL import Image

# 옵션을 선언 OSError: image file is truncated
from PIL import ImageFile 
ImageFile.LOAD_TRUNCATED_IMAGES = True

from base64 import encodebytes

app = Flask(__name__)

""" swagger-ui """
api = Api(app, version='0.0.1', title='[ Chuibbo-Flask-Rembg ]', description='Chuibbo API 명세서', doc="/swagger-ui")
remove_background_api = api.namespace('api/resume-photos/remove-background', description='Remove Background Controller')
background_synthesis_solid_api = api.namespace('api/resume-photos/background-synthesis-solid', description='Background Synthesis Solid Controller')
background_synthesis_gradation_api = api.namespace('api/resume-photos/background-synthesis-gradation', description='Background Synthesis Gradation Controller')

def transform_encoded_image(file, RGB_type):
    pil_img = Image.open(io.BytesIO(file))
    pil_img = pil_img.convert(RGB_type)
    byte_arr = io.BytesIO()
    pil_img.save(byte_arr, format='PNG')
    encoded_img = encodebytes(byte_arr.getvalue())
    return encoded_img

def delete_image(path):
    if os.path.exists(path):
        os.remove(path)
    else:
        print("The file does not exist")


@remove_background_api.route('')
class RemoveBackground(Resource):
    def post(self):
        """배경 제거"""
        photo = request.files['photo']
        id = request.form['id']

        input_path = f'./examples/{id}_in.jpg'
        output_path = f'./examples/{id}_out.png'

        with open(input_path, 'wb') as f:
            f.write(photo.read())

        f = np.fromfile(input_path)
        result = remove(f)

        pil_img = Image.open(io.BytesIO(result))
        pil_img.save(output_path)

        encoded_img = transform_encoded_image(result, "RGBA")

        delete_image(input_path)

        return json.dumps({ "code": 1, "message": "", "data": encoded_img.decode('ascii') }), 200


@background_synthesis_solid_api.route('')
class BackgroundSynthesisSolid(Resource):
    def post(self):
        """단색 배경 합성"""
        photo = request.files['photo']
        id = request.form['id']
        solid_color = request.form['solid_color']

        color = tuple(map(int, solid_color.split(', '))) # str to tuple

        input_path = f'./examples/{id}_out.png'

        # TODO: photo로 받은 사진이 배경이 검정으로 되는 문제
        # input_path = f'./examples/{id}_color.png'
        # with open(input_path, 'wb') as f:
        #     f.write(photo.read())

        f = np.fromfile(input_path)
        with Image.open(io.BytesIO(f)).convert("RGBA") as fg:
            with Image.new('RGBA', fg.size, color) as bg:
                canvas_img = Image.alpha_composite(bg, fg)
                canvas_img = canvas_img.convert('RGB')
                canvas_img.save(input_path, 'JPEG', quality=95)

        file = np.fromfile(input_path)
        encoded_img = transform_encoded_image(file, "RGB")

        delete_image(input_path)

        return json.dumps({ "code": 1, "message": "", "data": encoded_img.decode('ascii') }), 200

@background_synthesis_gradation_api.route('')
class BackgroundSynthesisGradation(Resource):
    def post(self):
        """그라데이션 배경 합성"""
        photo = request.files['photo']
        id = request.form['id']
        gradation_photo = request.files['gradation_photo']

        # input_path = f'./examples/{id}_input.png'
        input_path = f'./examples/{id}_out.png'
        output_path = f'./examples/{id}_gradation.png'

        # TODO: photo로 받은 사진이 배경이 검정으로 되는 문제
        # with open(input_path, 'wb') as f:
        #     f.write(photo.read())
        with open(output_path, 'wb') as f:
            f.write(gradation_photo.read())

        fg = Image.open(input_path).convert('RGBA') # 원본
        bg = Image.open(output_path) # 배경
        w, h = fg.width, fg.height
        bg = bg.resize((w, h))

        for y in range(h):
            for x in range(w):
                r, g, b, a = fg.getpixel((x,y))
                if a > 128: # If foreground is opaque, overwrite background with foreground
                    bg.putpixel((x,y), (r,g,b))
        bg.save(input_path)

        file = np.fromfile(input_path)
        encoded_img = transform_encoded_image(file, "RGB")

        delete_image(input_path)
        delete_image(output_path)

        return json.dumps({ "code": 1, "message": "", "data": encoded_img.decode('ascii') }), 200

app.run(host="127.0.0.1", port="8080", debug=True)
