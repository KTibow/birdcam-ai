# Birdcam AI

Have you ever wanted to record every single time a bird comes to your bird feeder?
Have you ever wanted to have your smart speaker let you know about that, too?
And also wanted to be able to view a livestream of snapshots from your bird feeder from your phone?

Well then, I've got the solution for you! And you can even tell your friends you have an ML-powered bird feeder!

This is what it looks like (for me):

![Picture of birdfeeder with Pi](https://i.imgur.com/WR50yb1l.jpg)

## Materials

- [Lobe AI kit](https://www.adafruit.com/product/4963)
- Some way to mount your camera
- Some way to mount your Pi
- A birdfeeder and everything needed to attract birds

## Assembly

1. Attach your fan to your Lobe HAT thingy
2. Attach the longer camera cord to the camera
3. Thread the camera cord through the slot in the HAT and connect it
4. Connect the HAT's gpio sockets to the Pi's
5. Flash an SD card for headless setup (ssh file, wpa_supplicant.conf file)
6. Insert the SD card to the Pi
7. Connect the Pi to power

## First programming steps

First, you should probably roughly follow Adafruit's official guide.
They go through some necessary steps, like installing certain libraries and configuring the fan.

Then, go ahead and start capturing some training data. There's a sub-program in the training-program folder.
Use tmux to run it while you aren't connected. Just run `tmux` to make a new session, run the program, and press `ctrl`+`b` then `d` to detach.
Get into the session again with `tmux attach`.

It'll capture `jpeg` files. Use SCP to copy over the files. Then, when you're ready, import them into [Lobe](lobe.ai).

Export a TensorFlow Lite model once it's done training. SSH into the Pi, and clone this repo.
Then rename the exported model's folder `model`, and SCP it into this repo (as a subfolder)

## More assembly

1. Mount the Raspberry Pi below the camera.
2. Mount the camera so it's at a good angle that'll let it capture the birds at the birdfeeder.

## More programming steps

You'll need to create a folder on the repo in the Pi called `captured_data`. It'll house the videos and pictures of the birds, which you can look at and use to improve the model.
Then, create a file called `secrets.py`. It houses your HA API keys, which are used for the functionality of pressing the up joystick to cast to a TV.

## Use

Run `sudo tmux` inside of the repo, then run `python app.py`. Detach as usual. Endpoints are available via flask (look in the code). I also have some more stuff that I don't want to share now because I'm lazy (a EXE that sends you notifications and some HA automations.

## Final note

Have fun birdwatching.

This guide was somewhat intentionally broad, and the code is a bit dirty (I churned out this repo in an hour), but I'm open to questions and feedback. Just raise an issue and @mention me so I get notified about it.
