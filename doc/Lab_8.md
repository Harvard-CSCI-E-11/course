# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2027**

# **Lab \#8: AI and IoT meet cybersecurity: Making the MEMENTO upload photos to your website**

[Introduction and Lab Objectives](#introduction-and-lab-objectives)

[How you will be graded](#how-you-will-be-graded)

[Read The Docs](#read-the-docs)

[Run our camera code\!](#run-our-camera-code!)

[Get an A](#get-an-a)

# **Introduction and Lab Objectives** {#introduction-and-lab-objectives}

Welcome to the eighth and final lab. In this lab we will drop three programs onto your MEMENTO that exercise the camera. The last program will upload photos up to both the CSCI-E-11 dashboard and to the AI-enabled photoboard you developed for Lab 6\.

**To get an A you’ll need to re-create the Lab 6 messageboard with a new virtual host on your own, without using any templates. That is, you will be creating it in the /home/ubuntu/course/lab8 directory and with the lab8 smashed email domain.**

Objectives for this lab:

* Take photos with your MEMENTO
* Upload the photos

# **How you will be graded** {#how-you-will-be-graded}

* When you run the `e11 grade lab8` command, we will check the dashboard and your photoboard at [`smashedemail-lab8.csci-e-11.org`](http://smashedemail-lab6.csci-e-11.org) for a photo from your MEMENTO.
* The code we have given you will upload to both. To get an A, you need to set up a photoboard at [`smashedemail-lab8.csci-e-11.org`](http://smashedemail-lab6.csci-e-11.org) that receives an uploaded photo.

# **Read The Docs** {#read-the-docs}

Please read the following:

* Please re-read the MEMENTO documentation: [Overview | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board)
* For formatting your microSD card: [microSD Card Formatting Notes | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board/formatting-notes)
* How to factory reset your MEMENTO: [Factory Reset | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board/factory-reset)
* Installing CircuitPython: [Install CircuitPython | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board/install-circuitpython)

# **Run our camera code\!** {#run-our-camera-code!}

In the lab8/memento directory you will find some code to get you started.  For each of these programs, open them with Thonny, copy the program’s source code, and paste it into the `code.py` file on your MEMENTO.

* [`camera1.py`](https://github.com/Harvard-CSCI-E-11/spring27/blob/main/lab8_memento/camera1.py) — This is Adafruit’s MEMENTO camera demo with minor modifications to make it work a little more reliably with the current version of CircuitPython. The program is not well documented, so we used Google’s GEMINI3 to review the code and write documentation, which you can view in the file [`camera1.md`](https://github.com/Harvard-CSCI-E-11/spring27/blob/main/lab8_memento/camera1.md).
* [`camera2.py`](https://github.com/Harvard-CSCI-E-11/spring27/blob/main/lab8_memento/camera2.py) —This is a bare-bones point-and-shoot camera program. When you point the camera and press the shutter it focuses the lens and then takes a picture. We’ve added audio feedback to the program using the `pycam.tone()` functions built in to the `adafruit_pycamera` python module. We also moved from the `neopixel` library used in Lab \#7 to using the `pycam.pixels[]`  array to control the pixels. Check it out\!
* [`camera3.py`](https://github.com/Harvard-CSCI-E-11/spring27/blob/main/lab8_memento/camera3.py) — This is the final program that takes a photo and uploads it to the dashboard and the lab6 imageboard.

You will also need to edit the file settings.toml on the CircuitPython device. When you are finished with camera3.py and have it uploading to your lab6 image board, it should look something like this:

`CIRCUITPY_WIFI_SSID = "xxxxxx"`
`CIRCUITPY_WIFI_PASSWORD = "xxxxx"`
`API_KEY = "lab8:xxxxxxaxxxxxx"`
`API_SECRET_KEY = "xxxxxxxxxxxx"`
`EMAIL = "xxxxx@xxxxxx"`
`COURSE_KEY = "xxxxx"`
`TZ = "America/New_York"`
`LAB = "lab8"`

Of course, everything that is an `x` above should be something real. The `EMAIL` and `COURSE_KEY` should be taken from the CSCI-E-11 dashboard.

Note:

* After you paste in the code and save, you may need to click the run button to have the code run.
* Sometimes you can’t get access to the file system on the MEMENTO until you click the stop button,
* Sometimes you need to wait a bit of time for the MEMENTO after clicking the stop button for circuitpython to come back up.
* Sometimes you need to click the reset button on the MEMENTO.

# **Get an A** {#get-an-a}

To get an A, you’ll need to bring up your imageboard on the lab8 domain, [`smashedemail-lab8.csci-e-11.org`](http://smashedemail-lab8.csci-e-11.org) and make a new API\_KEY. Then your `settings.toml` file will look like this:

`CIRCUITPY_WIFI_SSID = "xxxxxx"`
`CIRCUITPY_WIFI_PASSWORD = "xxxxx"`
`API_KEY = "lab8:xxxxxxaxxxxxx"`
`API_SECRET_KEY = "xxxxxxxxxxxx"`
`EMAIL = "xxxxx@xxxxxx"`
`COURSE_KEY = "xxxxx"`
`TZ = "America/New_York"`
`LAB = "lab8"`

To set up the photoboard, you will need to:

* Set up nginx for lab8 and get a new Let’s Encrypt certificate
* Set up a lab8 service with gunicorn
* Set up the application
* Make an API key and store it in the appropriate file
* Put a copy of the API key on your MEMENTO, so it can upload to your photoboard.

To grade your lab, log in to your instance and type `e11 grade lab8`.

[image1]: <images/8-logo.png>