# Camera stuff
from picamera import PiCamera
from io import BytesIO
from PIL import Image, ImageChops
from time import sleep, strftime, time
import numpy as np
# Streaming stuff
from threading import Thread
from flask import Flask, Response

res_amount = round(224 * 2.5)
cam = PiCamera(resolution=(res_amount, res_amount), framerate=10)
cam.start_preview()

app = Flask(__name__)


def get_image():
    stream = BytesIO()
    stream.seek(0)
    cam.capture(stream, format="jpeg")
    return Image.open(stream)


def image_entropy(img):
    w, h = img.size
    a = np.array(img.convert("RGB")).reshape((w * h, 3))
    h, e = np.histogramdd(a, bins=(16,) * 3, range=((0, 256),) * 3)
    prob = h / np.sum(h)  # normalize
    prob = prob[prob > 0]  # remove zeros
    return -np.sum(prob * np.log2(prob))


@app.route("/")
def serve_image():
    global new_image
    stream = BytesIO()
    try:
        new_image.save(stream, format=new_image.format)
    except Exception as e:
        print("Error getting image to serve.")
        return serve_image()
    stream.seek(0)
    resp = Response(stream.read(), mimetype="image/jpeg", direct_passthrough=True)
    return resp

@app.route("/interactive")
def serve_live():
    return open("index.html").read()

def main_loop():
    global new_image
    old_image = get_image()
    last_motion = 0
    while is_running:
        new_image = get_image()
        try:
            diff = ImageChops.difference(old_image, new_image)
            motion_amount = image_entropy(diff)
        except Exception as e:
            print("Error determining motion amount.")
            new_image = old_image
            continue
        print(motion_amount)
        if motion_amount > 1.5:
            print("Motion detected, saving")
            new_image.save(strftime("%j-%-I-%M-%S-%p") + "-motion.jpeg")
            diff.save(strftime("%j-%-I-%M-%S-%p") + "-diff.jpeg")
            last_motion = time()
        elif time() - last_motion < 30 and motion_amount > 0.66:
            print("Saving slight motion")
            new_image.save(strftime("%j-%-I-%M-%S-%p") + "-slight-motion.jpeg")
            diff.save(strftime("%j-%-I-%M-%S-%p") + "-diff.jpeg")
        elif round(time()) % 600 == 0: # Take a nothing photo every 10 minutes
            print("Saving nothing")
            new_image.save(strftime("%j-%-I-%M-%S-%p") + "-nothing.jpeg")
            sleep(1)
        old_image = new_image
        sleep(0.1) # Allow stuff to catch up

is_running = True
new_image = None

if  __name__ == "__main__":
    sleep(1) # Wait for camera
    loop = Thread(target=main_loop)
    loop.start()
    app.run(host="0.0.0.0", port=5483)
    is_running = False
    cam.close()
