import math
import uuid
import requests
from io import BytesIO
import io
import os
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from flask import Flask, redirect, url_for, render_template, request, session
from flask_cors import CORS, cross_origin

# NB: host url is not prepended with \"https\" nor does it have a trailing slash.
os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

app = Flask(__name__)
cors = CORS(app)
@app.route('/', methods = ['POST','GET'])
#app.config['CORS_HEADERS'] = 'Content-Type'

@cross_origin()

def sa_backend():
    prompt = request.get_json().get('prompt')
    print(prompt)
    url = request.get_json().get('url')
    print(url)
    keyval = request.get_json().get('key')
    print(keyval)
    nasa_id = request.get_json().get('nasa_id')

    # To get your API key, visit https://beta.dreamstudio.ai/membership
    os.environ['STABILITY_KEY'] = keyval

    stability_api = client.StabilityInference(
        key=os.environ['STABILITY_KEY'],
        verbose=True,
    )

    return_url = 'http://34.68.47.35/nasa_pic.png'
    response = requests.get(url)
    orig_image = Image.open(BytesIO(response.content))

    # Get it resized and cropped down to 512 x 512
    # orig_image = Image.open('PIA21474_orig.jpg')
    width, height = orig_image.size

    minval = min([height, width])
    factor = 512.0 / float(minval)
    new_height = math.ceil(float(height) * factor)
    new_width = math.ceil(float(width) * factor)
    newsize = (new_width, new_height)
    im1 = orig_image.resize(newsize)

    top = 0
    left = 0

    if new_height > 512:
        top = (new_height - 512) / 2

    if new_width > 512:
        left = (new_width - 512) / 2

    right = left + 512
    bottom = top + 512

    img = im1.crop((left, top, right, bottom))

    # img = Image.open("D:/junk/spaceapps22/ciaran2.jpg")
    answers = stability_api.generate(
        prompt=prompt,
        init_image=img,
        start_schedule=0.6,  # this controls the "strength" of the prompt relative to the init image
    )

    # iterating over the generator produces the api response
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img2 = Image.open(io.BytesIO(artifact.binary))
                myuuid = uuid.uuid4()
                filename = '/var/www/html/spaceapps/' + str(myuuid) + '.png'
                return_url = 'http://34.68.47.35/spaceapps/'  + str(myuuid) + '.png'
                print(filename)
                img2.save(filename)

    return return_url

