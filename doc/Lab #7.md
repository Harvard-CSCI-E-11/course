# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2026**

# **Lab \#7: Calling your API from a microcontroller**

[Introduction and Lab Objectives](#introduction-and-lab-objectives)

[Get Started: Buy an Adafruit Memento](#get-started:-buy-an-adafruit-memento)

[HISTORICAL NOTE: Arduino, Adafruit, MicroPython and Circuit Python](#historical-note:-arduino,-adafruit,-micropython-and-circuit-python)

[Check your MEMENTO\!](#check-your-memento!)

[Read The Docs\!](#read-the-docs!)

[Make sure your MEMENTO works](#make-sure-your-memento-works)

[Setting up on a Macintosh](#setting-up-on-a-macintosh)

[Setting up on Windows](#setting-up-on-windows)

[Setting up on Windows with WSL](#setting-up-on-windows-with-wsl)

[Installing Circuit Python on the MEMENTO](#installing-circuit-python-on-the-memento)

[Using Thonny](#using-thonny)

[Installing CircuitPython Libraries with circup](#installing-circuitpython-libraries-with-circup)

[Installing circup with pipx](#$-pipx-ensurepath)

[The Leaderboard Application — Functional Specifications](#the-leaderboard-application-—-functional-specifications)

[Updating your MEMENTO](#updating-your-memento)

[Connecting the MEMENTO to the Wi-Fi](#connecting-the-memento-to-the-wi-fi)

[Where’s the Leaderboard Server?](#where’s-the-leaderboard-server?)

[Get an A](#get-an-a)

[CircuitPython Programming Notes](#circuitpython-programming-notes)

[Going Further](#going-further)

[AWS Lambda Resources](#aws-lambda-resources)

# **Introduction and Lab Objectives** {#introduction-and-lab-objectives}

Welcome to the seventh lab\! In this lab, we will use an ESP-32 computer with a display to connect to a web-based service and create an “internet of things” for the entire class.

Objectives for this lab:

* Learn about the ESP32-S3, an exciting platform for many Internet-of-Things projects.
* Learn about Circuit Python and the difference between Circuit Python and Micropython.
* Get some software working on the MEMENTO single-board microcontroller that you purchased.
* Have your MEMENTO connect to a “leaderboard” application that we wrote for this course.

In this lab, you will run a small program on your ESP-32 computer that will:

1. Register itself with the class “leaderboard.”
2. Check every minute and report that it is still up.
3. Report to you its position on the leaderboard.

The server for this lab ([https://leaderboard.csci-e-11.org](https://leaderboard.csci-e-11.org)) will run a dashboard, showing who is at the top of the leaderboard.

How you will be graded:

* If, for some reason, you cannot get a physical device, you can register with the web-based JavaScript client for partial credit.
* Once your device registers with the leaderboard, you will receive 4.5 points.
* If you can figure out how to change your device string, you will get 5.0 points.

# **Get Started: Buy an Adafruit Memento** {#get-started:-buy-an-adafruit-memento}

For these labs you will need a small microcontroller that runs Circuit Python and has a small screen and WiFi. The screen makes it somewhat more fun to use\! And there’s even a camera\! We’ll use that too.

We recommend:

* [MEMENTO \- Python Programmable DIY Camera \- Bare Board : ID 5420](https://www.adafruit.com/product/5420) ($34.95)
* [Adafruit MEMENTO Camera Enclosure & Hardware Kit : ID 5843](https://www.adafruit.com/product/5843) ($9.95) \- Optional but **highly recommended for the labs\!**
* [Lithium Ion Polymer Battery \- 3.7v 500mAh: ID 1578](https://www.adafruit.com/product/1578) ($7.95) \- Optional but useful if you want to disconnect the MEMENTO from your power supply and carry it around the room

If you can’t get the MEMENTO, you can accomplish this lab with any Adafruit device that:

* has Wi-Fi
* has a screen
* can run CircuitPython.

However for Lab 8 you will need to have a device that runs CircuitPython and has a camera. (Last year we used a device that ran MicroPython, but this year we decided to standardize on a single platform rather than require students to learn two different embedded-Python environments.)

Here’s a third-party review of the MEMENTO:

* [Getting Started with Adafruit MEMENTO: Python Programmable DIY Camera Board](https://circuitdigest.com/review/getting-started-with-adafruit-memento-full-guide-to-features-and-pinouts)

## **HISTORICAL NOTE: Arduino, Adafruit, MicroPython and Circuit Python** {#historical-note:-arduino,-adafruit,-micropython-and-circuit-python}

There are four popular environments for programming microcontrollers today:

* C/C++ using the [Arduino IDE](https://www.arduino.cc/en/software)
* [Rust](https://rust-dd.com/post/introduction-to-embedded-systems-with-rust-a-beginner-s-guide-using-esp32)
* [MicroPython](https://micropython.org/)
* [Circuit Python](https://circuitpython.org/).

When using CircuitPython, it is common to use [Thonny](https://thonny.org/) as a developer environment. There is also good support for [VS Code](https://learn.adafruit.com/using-the-circuitpython-extension-for-visual-studio-code/overview) (more appropriate for advanced students), and a [web-based Circuit Python editor](https://learn.adafruit.com/getting-started-with-web-workflow-using-the-code-editor/overview) which works well on Chromebooks.

MicroPython is an implementation of the Python language that runs on small systems. In broad strokes, MicroPython:

* Supports multi-core processors on several platforms (e.g. RP2040, some ESP32 variants).
* Has broader hardware support, targeting many different microcontroller families and boards.
* Aims to stay close to standard Python (CPython) in language features and the standard library, within embedded constraints.

CircuitPython is a fork of Micropython maintained by Adafruit. CircuitPython:

* Is optimized for teaching: excellent beginner-oriented online tutorials and relatively simple installers.
* Works best with AdaFruit's devices that offer native USB mass-storage (“CIRCUITPY” shows up as a USB drive, and you can just editor you code directly with Notepad or another editor).
* Provides a large collection of drivers and libraries for AdaFruit hardware (sensors, LEDs, displays, etc.)
* Is programmable with Thonny, VS Code, or Adafuit’s web-based editor.
* Has a friendly, responsive developer community, especially via Adafruit’s forums and Discord.

In this course we are going to be using Circuit Python (CP). For more background on CircuitPython and how it differs from MicroPython and standard Python, see:

* [https://en.wikipedia.org/wiki/CircuitPython](https://en.wikipedia.org/wiki/CircuitPython)

# **Check your MEMENTO\!** {#check-your-memento!}

Next, plug in your MEMENTO to make sure that it works:

![][image2]

After a few moments the camera will start running:

![][image3]

This is a program written in C. We need to replace it with CircuitPython.

# **Read The Docs\!** {#read-the-docs!}

The MEMENTO is powered by an [ESP32-S3](https://www.espressif.com/en/products/socs/esp32-s3) processor with 8MB Flash and 2MB of PSRAM. It has an OV5640 camera with 72 degree view auto-focus camera, and a 1.54” 240x240 Color TFT [and lots more](https://www.adafruit.com/product/5420#:~:text=Images%20and%20Video-,Description,-Make%20memories%2C%20or). The ESP32-S3 is a 240 MHz dual core Tensilica.

Now head over to the Adafuit website and check out these overviews:

* [Overview | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board/overview)
* [Install CircuitPython | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board/install-circuitpython)
* [Welcome to CircuitPython\! | Adafruit Learning System](https://learn.adafruit.com/welcome-to-circuitpython)
* [CircuitPython Documentation | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board/circuitpython-documentation)

And if you get really stuck…

* How to factory reset your MEMENTO: [Factory Reset | Adafruit MEMENTO Camera Board](https://learn.adafruit.com/adafruit-memento-camera-board/factory-reset)

# **Make sure your MEMENTO works** {#make-sure-your-memento-works}

Plug it in. Watch it boot. Make sure the camera works.

You should also try plugging the MEMENTO into your computer to make sure that the USBc interface is detected. If you are using a Macintosh, you can use the terminal and see its virtual serial port appear.

## **Setting up on a Macintosh** {#setting-up-on-a-macintosh}

Some students noted that they needed to set a **Privacy & Security** setting on their Mac to allow the MEMENTO to connect:

# ![][image4]

Once you have done that, go to the command line on your Mac and type:

`% ls -l /dev/c*`

On Simson’s Macintosh, this is before the MEMENTO was plugged in:

simsong@Seasons-2 e11 % ls \-l /dev/c\*

crw--w--w-  1 simsong  staff          0 Dec  6 20:12 /dev/console
crw-rw-rw-  1 root     wheel  0x9000007 Dec  6 20:12 /dev/cu.Bluetooth-Incoming-Port
crw-rw-rw-  1 root     wheel  0x9000001 Dec  6 19:03 /dev/cu.debug-console
crw-rw-rw-  1 root     wheel  0x9000003 Dec  6 20:12 /dev/cu.DockingK10C
crw-rw-rw-  1 root     wheel  0x9000005 Dec  6 20:12 /dev/cu.Shokz

and this is afterwards:

simsong@Seasons-2 e11 % ls \-l /dev/c\*
crw--w--w-  1 simsong  staff          0 Dec  6 20:12 /dev/console
crw-rw-rw-  1 root     wheel  0x9000007 Dec  6 20:12 /dev/cu.Bluetooth-Incoming-Port
crw-rw-rw-  1 root     wheel  0x9000001 Dec  6 19:03 /dev/cu.debug-console
crw-rw-rw-  1 root     wheel  0x9000003 Dec  6 20:12 /dev/cu.DockingK10C
crw-rw-rw-  1 root     wheel  0x9000005 Dec  6 20:12 /dev/cu.Shokz
crw-rw-rw-  1 root     wheel  0x9000009 Dec  9 18:32 /dev/cu.usbmodem2101

Notice the new device  `/dev/cu.usbmodem2101`. That’s the port for the MEMENTO, which is how we will program it.

## **Setting up on Windows** {#setting-up-on-windows}

It’s a bit tricker to use detect the MEMENTO on Windows, as the device names are not as descriptive. However, you should see a new COM port appear after you plug in the MEMENTO.

Before:

PS C:\\Users\\simsong\> Get-CimInstance Win32\_SerialPort | Format-Table DeviceID, Name

DeviceID Name
\-------- \----
COM1     Communications Port (COM1)

After:

PS C:\\Users\\simsong\> Get-CimInstance Win32\_SerialPort | Format-Table DeviceID, Name

DeviceID Name
\-------- \----
COM1     Communications Port (COM1)
COM4     USB Serial Device (COM4)

##

## **Setting up on Windows with WSL** {#setting-up-on-windows-with-wsl}

Right now we do not recommend using WSL with the MEMENTO because it’s hard to get the USB ports to map properly.

# **Installing Circuit Python on the MEMENTO** {#installing-circuit-python-on-the-memento}

We will be using Circuit Python on the MEMENTO. Fortunately, you read about it above (right?).

Remember, **it’s very important to use the version of Circuit Python for your machine, because** CircuitPython is compiled with the device drivers for each specific machine.

To install CP on your MEMENTO, go to [https://circuitpython.org/board/adafruit\_esp32s3\_camera/](https://circuitpython.org/board/adafruit_esp32s3_camera/).

1. Download the **.u2f** file for the MEMENTO.  It will be named something like `adafruit-circuitpython-adafruit_esp32s3_camera-en_US-10.0.3.u2f`.
2. Plug the MEMENTO into your USB port and double-click on the RESET button.

You will see the boot loader on the TFT screen:

![][image5]

3. A new USB drive (possibly called CAMERABOOT) should appear on your computer’s desktop:

![][image6]

4. Drag the **.u2f** file (possibly named) onto the USB drive.

The copy operation is surprisingly slow, but once it fully arrives on the device, the USB drive will disappear, your MEMENTO will reboot. The CAMERABOOT drive will disappear and a new drive for CIRCUITPY will appear:

![][image7]

On the MEMENTO, you will notice that it is now running CircuitPython:

![][image8]

**Look at the virtual CIRCUITPY drive:**

**![][image9]**

**Let’s look at that file [code.py](http://code.py):**

**![][image10]**

**Pretty neat, huh?**

You can do all of the programming for this lab by simply editing the file `code.py`  and saving it to the drive. However, we recommend that you get to learn Thonny…

## **Using Thonny** {#using-thonny}

Thonny is an IDE that was developed by Aivar Annamaa to help people learn programming. Annamaa wrote a paper back in 2015 describing the program and its philosophy. You can find a 1-page paper about the program here: [Thonny,: a Python IDE for Learning Programming](https://dl.acm.org/doi/10.1145/2729094.2754849)

[Download and Install Thonny](https://thonny.org/).  Thonny makes it easy to edit programs and immediately run them on the MEMENTO. It also gives a REPL (Read Eval Print Loop) that lets you type python and run it directly on the device. This makes it easy to try things out.

When you first run Thonny, you need to tell it that you are using a MEMENTO with Circuit Python.

Here Thonny is confused — it thinks that I’m using MicroPython with /dev/cu.usbserial-1310. That’s wrong, and it’s printing an error message:

![][image11]

Click on the pop-up on the lower-right:

![][image12]

I select “CircuitPython (generic) • Camera …” and then Thonny finds it:

![][image13]

On Windows Click on Tools \-\> Options \-\> Interpreter

![][image14]

Then select CircuitPython(Generic) and the Port your MEMENTO is on.

![][image15]

Meanwhile, the screen of the MEMENTO shows that it is talking to Thonny:

![][image16]

CLick in the Thonny Shell window and type:

`print("Hello from the desktop")`

You will see:

![][image17]

And on the MEMENTO you will see:

![][image18]

Ada Fruit has created many tutorials for the MEMENTO. You can find them here: [https://learn.adafruit.com/search?q=memento](https://learn.adafruit.com/search?q=memento)

The basic MEMENTO has a single neopixel light. You can use this program to set it to green:

import board
import digitalio
import neopixel\_write

pin \= digitalio.DigitalInOut(board.NEOPIXEL)
pin.direction \= digitalio.Direction.OUTPUT
neopixel\_write.neopixel\_write(pin, bytearray(\[50,0,0\]))

This will turn the LED to red:

neopixel\_write.neopixel\_write(pin, bytearray(\[0,50,0\]))

And this will turn the LED to blue:

neopixel\_write.neopixel\_write(pin, bytearray(\[0,0,50\]))

You can paste this code directly into the Thonny Shell window and it should work.

# **Installing CircuitPython Libraries with circup** {#installing-circuitpython-libraries-with-circup}

At this point, you should install the CircuitPython Libraries. You can find information here:

* [CircuitPython \- Libraries](https://circuitpython.org/libraries)

There are two ways to install the libraries:

1. You can just download the ZIP files, unzip them, and then move the specific libraries you want from the adafruit-circuitpython-bundle-10.x-mpy/lib folder into the CIRCUITPY lib/ folder. Don’t move them all, because there are many and together they take up too much space.
2. Alternatively, you can use the python `circup` Circuit Python package manager to install just what you want.

If you are comfortable with the command line (and you should be by this point), you will find it easiest to use  `circup` package on your desktop or laptop. You will find more information about circup here:

* [circup · PyPI](https://pypi.org/project/circup/) \- The Circuit Python package manager


You will install circup with the **`pipx`** command. But first you need to install **`pipx`**\!

## **Windows: install pipx Scoop Install: From a Powershell:**

If you are on Windows, you can install pipx with scoop:

`$ Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
`$ Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression`
	**`Pipx Install using Scoop`**`:`

`$ scoop install pipx`

## `$ pipx ensurepath` {#$-pipx-ensurepath}

##

## **MacOS: Install pipx with brew**

If you are on MacOS, we recommend installing pipx using the **brew** system.

First, install Homebrew using the instructions here: [https://brew.sh/](https://brew.sh/)

Next, use brew to install pipx:

`$ brew install pipx`

## **MacOS: Installing circup with pipx**

Once you have the `pipx` command installed, you can use it to install `circup`:

`$  pipx install circup`

Remember — you need to run this command *on your desktop computer* (and not on the computer in AWS).

## **Windows: Install Python directly or with scoop**

If you are using Windows and have never run Python on your computer before, you will need to install the Python language. You can do this from the Python website, from the Windows store, or using Scoop.

Full details of running Python on windows is here: [https://docs.python.org/3/using/windows.html](https://docs.python.org/3/using/windows.html)

One approach is to download it from the Windows store, You can also download the Python install manager from here: [https://www.python.org/downloads/release/python-31313/](https://www.python.org/downloads/release/python-31313/)

An alternative is to install Scoop, which is a command-line downloader for Windows. Details of installing scoop and using that to install python are here: [https://scoop.sh/](https://scoop.sh/).

You should install Python 3.14, as that is the version used in this course. You need to have it installed so that you can use it from the command line.

## **Windows: Install pipx and circup**

Once you have installed Python, you will need to install [pipx](https://pipx.pypa.io/stable/installation/). After you have installed pipx, you can use it to install `circup`:

	`$ pipx install circup`

## **Using circup**

The **`circup`** command allows you to download CP modules from the Internet and install them on your board. Use **`circup --help`** to learn more about it.

The **`ampy`** command that lets you navigate through the device’s file system, get and fetch files, and even run commands, without using Mu or having the USB storage mounted. It's useful to have. Use **`ampy --help`** to learn more about it.

Once you have circup installed at your command line, you can use these commandsZ:

	**`circup --help`** 		Print commands available

	**`circup list`**		Lists available models

	**`circup install`**		Installs a module

	**`circup uninstall`**	Uninstalls a model

So if you bought the neopixel ring for the memento and want to play with it, you could install the neopixel library:

	**`circup install neopixel`**

If you don’t have `pipx`, you can install poetry on your desktop ([installation guide here](https://python-poetry.org/docs/)):

(These commands would also work on Windows…)

`$ mkdir tools`
`$ cd tools`
`$ poetry init`
`This command will guide you through creating your pyproject.toml config.`

`Package name [fun]:`
`Version [0.1.0]:`
`Description []:`
`Author [Simson Garfinkel <simsong@acm.org>, n to skip]:`
`License []:`
`Compatible Python versions [>=3.13]:`

`Would you like to define your main dependencies interactively? (yes/no) [yes] no`
**`...`**
`$ poetry add circup adafruit-ampy`
`$ poetry run circup install neopixel`

And then you could paste this small program into [code.py](http://code.py) using Thonny to spin the Neopixel wheel (don’t forget to click ![][image19])

import time
import board
import neopixel

PIXEL\_PIN \= board.A1   \# Try A0 if A1 does not work
NUM\_PIXELS \= 8

pixels \= neopixel.NeoPixel(
    PIXEL\_PIN,
    NUM\_PIXELS,
    bpp=4,
    pixel\_order=neopixel.GRBW,
)

current \= 0

for i in range(NUM\_PIXELS \* 4):
    \# Clear all pixels
    pixels.fill((0, 0, 0, 0))

    \# Light the current pixel red
    pixels\[current\] \= (255, 0, 0, 0\)

    \# Add a 1-pixel green tail behind it
    pixels\[(current \- 1\) % NUM\_PIXELS\] \= (0, 40, 0, 0\)

    pixels.show()
    time.sleep(0.08)

    \# Advance to next pixel
    current \= (current \+ 1\) % NUM\_PIXELS

![][image20]

This is kind of fun:

![][image21]

# **The Leaderboard Application — Functional Specifications** {#the-leaderboard-application-—-functional-specifications}

Our goal in developing the Leaderboard Application was to have a simple dashboard that recorded when each student of the class connected to it with a small program running on their MEMENTO. We wanted the top of the leaderboard to be the student who is connected the longest. We also wanted to have a way for students who don’t have a MEMENTO to participate.

So here’s our design ideas.

1. The leaderboard operates a three API endpoints: **leaderboard** which returns the current leaderboard, **register** where clients can register that they are present, and **update** that clients can use to to say that they are still alive.
2. We will have each client store how long that client has been running. To prevent clients from cheating, we will digitally sign this information with an HMAC and a secret key known only to the server. We will do this using the Python package `itsdangerous` which was developed specifically for this purpose
   * [Learn about It’s Dangerous](https://itsdangerous.palletsprojects.com/en/stable/concepts/)
3. We store the leaderboard’s secret key on Amazon’s infrastructure using the AWS Secrets Manager.
   * [Learn about the AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
4. We also want to avoid writing any code to deal with moderation or deleting inappropriate user-generated content, so we have the server server will assign a name to each client and that’s the name the client and the leaderboard will display.

We host the leaderboard at [https://leaderboard.csci-e-11.org/](https://leaderboard.csci-e-11.org/). When you connect, a JavaScript client is downloaded into your browser and joins in the fun. You can use your browser’s “view-source” command to look at the contents of the page.

Here are the details of the three APIs:

`GET /api/leaderboard`
Returns the leaderboard as a JSON object array. Each object in the array will have two values:
	`leaderboard` — An array of leader objects, where each object has:
	`.name` — the name of the leader
	`.first_seen` — When the leader was first seen.
	`.active` — If the leader is active or inactive (inactive may be removed without notice)
	`message` — An optional message to display (currently not implemented)
`POST /api/register`
 — Register a new client. This will return to the client:
`.name` — The client’s name
`.opaque` — A signed data object that contains information used by the server

`POST /api/update`
— Tells the leaderboard that the client is still alive.
— Client provides the opaque data
— Server returns the leaderboard.

If a client doesn’t call **/api/update** within 90 seconds, they go from being active to being inactive and are taken off the leaderboard.

The application running on the MEMENTO will:

1. Boot
2. Initialize the WiFi with a provided 802.11 SSID and Wi-Fi password.
3. Run `/api/register` on the leaderboard to register.
4. Using the values from `/api/register`, call `/api/update` every 60 seconds.
5. Display the results

# **Updating your MEMENTO** {#updating-your-memento}

At this point, you'll need to take more control of your MEMENTO. To complete this lab you'll need to get it on your Wi-Fi network and give it a copy of the CircuitPython `requests` library so that it can make connections to our server.

We find it easiest to manage these devices using a combination of the command-line on a laptop running MacOS and using the Thonny editor (allowing you to edit files and use the REPL).

* Remember that when you are using the REPL, the device will not automatically run `code.py` when you save it. You must exit the REPL with ^d first (or click the RUN button).

We recommend that you install:

`$ circup install adafruit_ntp` 		— adafruit NTP client

`$ circup install adafruit_requests` 		— Support for internet

`$ circup install adafruit_display_text` 	— Drawing text

`$ circup install adafruit_sdcard`		— managing the SD card. If you want it for lab8\!

`$ circup install adafruit_pycamera`		— Full support for the camera

Remember:

1. Your MEMENTO must be connected to your computer and have CP installed and running or the **install** command will not work.
2. If you are running **`circup`** under **`poetry`**, change **`circup`** above to `poetry run circup`

Here is a fun program to try on your MEMENTO:

	[code\_bounce.py](https://github.com/Harvard-CSCI-E-11/spring26/blob/main/lab7_memento/code_bounce.py)

Just paste it into code.py, save it and hit the run button in Thonny. If that doesn’t work, reset the board (sometimes this is needed). To exit the program, click the ![][image22] (STOP) button in Thonny or click the shutter button (the button with the ✌(OKAY) along the edge).

# **Connecting the MEMENTO to the Wi-Fi** {#connecting-the-memento-to-the-wi-fi}

The MEMENTO connects to the Internet using your local Wi-Fi. To do this, it needs to know the network name (called the SSID) and the network password. We find it easiest to keep the WiFi configuration in the CP file `settings.toml` located in the root directory of your MEMENTO’s file system.

Your `settings.toml` file should look like this:

`CIRCUITPY_WIFI_SSID = "your_wifi_network_name"`
`CIRCUITPY_WIFI_PASSWORD = "your_wifi_password"`
`E11_EMAIL = "your email address"`
`E11_COURSE_KEY = "your course key"`

(As a reminder, you can find your E11 email address and course key on the E11 dashboard at [https://csci-e-11.org/](https://csci-e-11.org/)).

Circuit python reads this file when it starts up and assigns each to an environment variable that can be read with the  `getenv()` function.

Now, load this program into code.py:

	[code\_leaderboard\_client.py](https://github.com/Harvard-CSCI-E-11/spring26/blob/main/lab7_memento/code_leaderboard_client.py)

Run it\! You can monitor the leaderboard at [https://leaderboard.csci-e-11.org/](https://leaderboard.csci-e-11.org/) .

You will get email with your grade when your MEMENTO successfully registers itself with the leaderboard

If you didn’t purchase an MEMENTO or another a computer that can run Circuit Python, fear not\! There is a python client that you can run on a Mac or Windows or Linux computer. Just download it and run it:

	[linux\_client.py](https://github.com/Harvard-CSCI-E-11/spring26/blob/main/lab7_linux/linux_client.py)

Here are some web pages we found particularly helpful:

* [Adafruit CircuitPython API Reference](https://docs.circuitpython.org/en/latest/docs/index.html) \- CircuitPython Libraries primary documentation
* [Adafruit NeoPixel Überguide](https://learn.adafruit.com/adafruit-neopixel-uberguide/the-magic-of-neopixels) — Learn how to control LED strips.  (Yes\! You can control an LED strip with your Feather.)
* [https://circuitpython.org/libraries](https://circuitpython.org/libraries) — A list of the up-to-date CircuitPython libraries

You can also learn more about Adafruit’s CircuitPython Bundle:

* [GitHub \- adafruit/Adafruit\_CircuitPython\_Bundle](https://github.com/adafruit/Adafruit_CircuitPython_Bundle)
* [Todbot's CircuitPython Tricks | Adafruit Learning System](https://learn.adafruit.com/todbot-circuitpython-tricks?view=all)  (also check out [Todbot’s github repo](https://github.com/todbot/circuitpython-tricks))

# **Where’s the Leaderboard Server?** {#where’s-the-leaderboard-server?}

The server for this lab ([https://leaderboard.csci-e-11.org](https://leaderboard.csci-e-11.org)) is written with Python and Flask and running on a “serverless” instance on AWS using the Lambda service.

Lambda is a system that automatically spins up an instance the moment it is needed and then shuts it down after a period of inactivity (typically 4 minutes). One advantage of Lambda is that it will automatically scale for any number of clients who access the server. A disadvantage is that you pay for each of those accesses — typically somewhere between a thousandth and a hundredth of a cent. So please feel free to use the Leaderboard, but don’t send it a hundred updates every second\!

The leaderboard uses Amazon’s DynamoDB as its database. DynamoDB is a “document” database that stores JSON objects. It works with Lambda. Although we could have used an SQL database, Amazon’s serverless database offerings start at around $50/month, whereas DynamoDB is free for many uses.

You can find the code that we are using here: [https://github.com/Harvard-CSCI-E-11/spring26/tree/main/staff/leaderboard](https://github.com/Harvard-CSCI-E-11/spring26/tree/main/staff/leaderboard)

When you go to the leaderboard, a JavaScript client that implements our API will run in your browser and register itself. You can view the source code for that client [here](https://github.com/Harvard-CSCI-E-11/spring25/blob/main/staff/leaderboard/leaderboard_app/templates/leaderboard.html) (the JavaScript is embedded in the HTML file).

# **Get an A** {#get-an-a}

It turns out that you can put arbitrary messages on the dashboard. Figure out how and change include the word “magic” somewhere on the leaderboard message associated with your MEMENTO.

# **CircuitPython Programming Notes** {#circuitpython-programming-notes}

We’ve given you a few programs that you can run on your ESP-32:

[https://github.com/Harvard-CSCI-E-11/spring26/tree/main/lab7\_memento/demos](https://github.com/Harvard-CSCI-E-11/spring26/tree/main/lab7_memento/demos)

Our leaderboard client uses the `adafruit_connection_manager`.  To use our leaderboard client(below), you will need to install the connection manager first.

Instructions for downloading the connection manager are here:

* [Introduction — Adafruit CircuitPython ConnectionManager Library 1.0 documentation](https://docs.circuitpython.org/projects/connectionmanager/en/latest/)

You can learn more about it here:

* [Adafruit Connection Manager](https://adafruit-playground.com/u/justmobilize/pages/adafruit-connection-manager)

The leaderboard client is here:

	[https://github.com/Harvard-CSCI-E-11/spring26/blob/main/lab7\_linux/linux\_client.py](https://github.com/Harvard-CSCI-E-11/spring26/blob/main/lab7_linux/linux_client.py)

If you do not install the connections manager, you will see an error message like this:

![][image23]

To run the client, paste it into the `code.py` window of your Thonny editor and save it to the MEMENTO, and run it.

# **Going Further** {#going-further}

The leaderboard on the MEMENTO is printing messages with the wrong time\! That’s because time is not set on the MEMENTO. Fix this\!. There are several ways you can do this:

* You can install the [Circuit Python NTP client](https://docs.circuitpython.org/projects/ntp/en/latest/) and then add these two lines to your leaderboard\_client.py program:
  `pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)`
  `ntp = adafruit_ntp.NTP(pool, tz_offset=0, cache_seconds=3600)`
* The time is returned in the /api/update call. Find where it is returned and use it to set the time (or at least fix the output).
* Draw on your feather's TFT with pretty fonts. Post the photos to the forum. (Hint: you'll need to load fonts onto your feather\! See: [Using Fonts | Adafruit GFX Graphics Library](https://learn.adafruit.com/adafruit-gfx-graphics-library/using-fonts) )


## **AWS Lambda Resources** {#aws-lambda-resources}

If you want to learn more about Lambda:

* [GitHub \- awslabs/aws-lambda-web-adapter](https://github.com/awslabs/aws-lambda-web-adapter) — Useful templates for deploying flask, fastapi and other servers in Lambda, using either the ZIPFILE or the Docker Image deployment.

[image1]: <images/7-logo.png>
[image2]: <images/7-memento.png>
[image3]: <images/7-camera.png>
[image4]: <images/7-privacy.png>
[image5]: <images/7-bootloader.png>
[image6]: <images/7-cameraboot.png>
[image7]: <images/7-circuitpy.png>
[image8]: <images/7-circuitpython.png>
[image9]: <images/7-files.png>
[image10]: <images/7-code.png>
[image11]: <images/7-thonnyerror.png>
[image12]: <images/7-interpreter.png>
[image13]: <images/7-thonny.png>
[image14]: <images/7-toolsmenu.png>
[image15]: <images/7-options.png>
[image16]: <images/7-console.png>
[image17]: <images/7-shell.png>
[image18]: <images/7-display.png>
[image19]: <images/7-runbutton.png>
[image20]: <images/7-neopixelcode.png>
[image21]: <images/7-neopixels.png>
[image22]: <images/7-stopbutton.png>
[image23]: <images/7-feather.png>
