# Server
from flask import Flask, send_file, make_response, Response

# Camera
from picamera import PiCamera
from io import BytesIO
from PIL import Image

# General
from threading import Thread
from time import strftime, sleep

# Clips
import glob, os

# AI
import lobe

# Hardware
import requests
import board
from digitalio import DigitalInOut, Direction, Pull
import neopixel

# Secrets
from secrets import ha_endpoint, token

app = Flask(__name__)
model = lobe.ImageModel.load("/home/pi/birdcam-ai/model/")
cam = PiCamera(resolution=(224 * 2,) * 2, framerate=15)
cam.image_effect = "denoise"
cam.exposure_mode = "night"
cam.start_preview()

latest_image = None
image_index = 0
prediction = "Nothing"
light_is_on = False
running = True

joystick_up = DigitalInOut(board.D24)
main_button = DigitalInOut(board.D17)
light = neopixel.NeoPixel(board.D12, 7)

for pin in [joystick_up, main_button]:
  pin.direction = Direction.INPUT
  pin.pull = Pull.UP


def convert_clips():
  print("Converting clips...")
  for clip in glob.glob("captured_data/*.mjpeg"):
    new_clip_name = clip.replace("mjpeg", "mp4")
    os.system(f'ffmpeg -y -r 15 -i "{clip}" "{new_clip_name}"')
    os.remove(clip)


def camera_loop():
  global latest_image
  global image_index
  while running:
    stream = BytesIO()
    stream.seek(0)
    cam.capture(stream, format="jpeg")
    image = Image.open(stream)
    latest_image = image.copy()
    image_index += 1


def predict_loop():
  global prediction
  last_result_index = image_index
  about_to_end = False
  previous_image = None
  while running:
    # Wait to update
    while last_result_index == image_index:
      pass
    result_index = image_index
    # Label
    test_image = latest_image.copy()
    result = model.predict(test_image)
    label = result.prediction
    conf = round(result.labels[0][1] * 100)
    # Do stuff
    last_prediction = prediction
    prediction = label

    cam.annotate_text = f"{label} {conf}%"

    time.sleep(1 / 14)

    if last_prediction != label:
      print(cam.annotate_text)
      test_image.save(f"captured_data/{label} {strftime('%j %-I-%M-%S %p')}.jpeg")
      if previous_image is not None:
        previous_image.save(f"captured_data/{label} before {strftime('%j %-I-%M-%S %p')}.jpeg")

    if label in ["Dark Eyed Junco", "Spotted Towhee"] and not cam.recording:
      cam.start_recording(
        f"captured_data/{label} {strftime('%j-%-I-%M-%S-%p')}.mjpeg", format="mjpeg"
      )
    elif label == "Nothing" and cam.recording and about_to_end:
      sleep(0.1)
      cam.stop_recording()
      convert_clips()
      about_to_end = False
    elif label == "Nothing" and cam.recording and not about_to_end:
      about_to_end = True
    previous_image = test_image

def hardware_loop():
  last_up_value = True
  last_button_value = True
  while running:
    if not joystick_up.value and last_up_value != joystick_up.value:
      print("Playing feed on cast")
      response = requests.post(
        ha_endpoint + "/api/services/media_player/play_media",
        json={
          "entity_id": "media_player.family_room_cast",
          "media_content_id": "http://192.168.1.49:5000/feed",
          "media_content_type": "image/jpeg",
        },
        headers={
          "Authorization": f"Bearer {token}",
          "Content-Type": "application/json",
        },
      )
      print(response.text)
      response.raise_for_status()
    if not main_button.value and last_button_value != main_button.value:
      print("Toggling NeoPixel")
      if light_is_on:
        light.fill(0)
      else:
        light.fill((250, 250, 150))
      light_is_on = not light_is_on
    last_up_value = joystick_up.value
    last_button_value = main_button.value
    sleep(0.05)


@app.route("/")
def send_index():
  return send_file("index.html", mimetype="text/html")


@app.route("/image")
def send_image():
  raw_file = BytesIO()
  latest_image.save(raw_file, "JPEG")
  raw_file.seek(0)
  # Send image
  image_response = send_file(raw_file, mimetype="image/jpeg")
  image_response = make_response(image_response)
  image_response.headers["Cache-Control"] = "no-store"
  return image_response


def generate_feed():
  while True:
    frame = BytesIO()
    latest_image.save(frame, "JPEG")
    frame.seek(0)
    yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame.read() + b"\r\n")


@app.route("/feed")
def stream_feed():
  return Response(generate_feed(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/prediction")
def send_prediction():
  return prediction


@app.route("/property/<name>/<value>")
def change_property(name, value):
  try:
    cam.__setattr__(name, int(value))
  except ValueError:
    cam.__setattr__(name, value)
  return str(cam.__getattribute__(name))


convert_clips()

camera_thread = Thread(target=camera_loop)
predict_thread = Thread(target=predict_loop)
hardware_thread = Thread(target=hardware_loop)
server_thread = Thread(target=app.run, kwargs={"host": "0.0.0.0"}, daemon=True)

camera_thread.start()
predict_thread.start()
hardware_thread.start()
server_thread.start()

try:
  while True:
    pass
except KeyboardInterrupt:
  running = False
  print("Exiting soon.")
  cam.close()
