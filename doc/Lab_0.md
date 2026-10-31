# **![][image1]**

# **CSCI E-11: Artificial Intelligence, the Internet-of-Things, and Cybersecurity** **Harvard Extension School** **Spring 2027**

# **Lab \#0**

This lab has two goals:

1. You will register on the CSCI E-11 dashboard, at [https://csci-e-11.org/](https://csci-e-11.org)
2. You will purchase a small computer that you can use for Lab 7 and 8.

## 1. Register for the dashboard

Please go to [https://csci-e-11.org/](https://csci-e-11.org) and log
in using your Harvard Key. You will automatically get an an email
welcoming you to the class.

## 2. Purchase a Raspberry Pi

You will be using the Raspberry Pi:
* in [Lab #7](Lab_7.md) to register on a Wi-Fi network and send a message to the [CSCI E-11 Leaderboard](https://leaderboard.csci-e-11.org).
* in [Lab #8](Lab_8.md) to take a photograph and post to both your [CSCI E-11 Dashboard](https://csci-e-11.org) and to the image board you created in [Lab #6](Lab_6.md).

For these labs you will need a Raspberry Pi computer. For this class,
you can use any of these versions:

| Model | Size (Dimensions) | CPU | Memory (RAM) | I/O & Connectivity |
| --- | --- | --- | --- | --- |
| **Pi Zero** | 65 x 30 x 5mm | 1 GHz single-core ARM11 (BCM2835) | 512 MB | Mini-HDMI, Micro-USB OTG, Micro-USB power, MicroSD, unpopulated 40-pin GPIO, composite/reset test pads |
| **Pi Zero W** | 65 x 30 x 5mm | 1 GHz single-core ARM11 (BCM2835) | 512 MB | 2.4 GHz 802.11n Wi-Fi, BT 4.1/BLE, Mini-HDMI, Micro-USB OTG, Micro-USB power, MicroSD, CSI camera port, unpopulated 40-pin GPIO |
| **Pi Zero 2** | 65 x 30mm | 1 GHz quad-core 64-bit ARM Cortex-A53 (RP3A0) | 512 MB | Mini-HDMI, Micro-USB OTG, Micro-USB power, MicroSD, CSI-2 camera connector, unpopulated 40-pin GPIO |
| **Pi Zero 2W** | 65 x 30mm | 1 GHz quad-core 64-bit ARM Cortex-A53 (RP3A0) | 512 MB | 2.4 GHz 802.11n Wi-Fi, BT 4.2/BLE, Mini-HDMI, Micro-USB OTG, Micro-USB power, MicroSD, CSI-2 camera connector, unpopulated 40-pin GPIO |
| **Pi 3B** | \approx85 x 56mm | 1.2 GHz quad-core 64-bit ARM Cortex-A53 (BCM2837) | 1 GB | 10/100 Ethernet, 2.4 GHz Wi-Fi, BT 4.1, 4× USB 2.0, full-size HDMI, 3.5mm audio/composite jack, MicroSD, CSI/DSI ports, 40-pin GPIO |
| **Pi 4** | 85 x 56 x 19.5mm | 1.5–1.8 GHz quad-core 64-bit ARM Cortex-A72 (BCM2711) | 1 GB, 2 GB, 4 GB, or 8 GB LPDDR4 | Gigabit Ethernet, dual-band Wi-Fi, BT 5.0, 2× USB 3.0, 2× USB 2.0, 2× micro-HDMI, 3.5mm audio/composite jack, MicroSD, CSI/DSI ports, USB-C power, 40-pin GPIO |
| **Pi 5** | 85 x 56mm | 2.4 GHz quad-core 64-bit ARM Cortex-A76 (BCM2712) | 2 GB, 4 GB, 8 GB, or 16 GB LPDDR4X | Gigabit Ethernet, dual-band Wi-Fi, BT 5.0, 2× USB 3.0, 2× USB 2.0, 2× micro-HDMI, PCIe 2.0 x1 interface, MicroSD, 2× MIPI camera/display transceivers, USB-C power (PD), RTC battery connector, power button, 40-pin GPIO |

Which version should you get? Honestly, get whatever you can! You'll
see prices all over the map for these machines. We've tried all of
them with the labs, and they all work fine --- but there are minor
differences regarding how you will get them online, and how you
connect the camera for lab 8.

### Connecting to the Internet with a Raspberry Pi

To connect to the Internet, you have multiple choices:
1. You can also connect the to the Internet using your laptop as a router. You then connect the Raspberry Pi to your computer over the USB port. The USB port provides power and routes the network. This may be easiest, but it requires installing software on your laptop.

2. You can use your home Wi-Fi if you have a Wi-Fi network that does not have a captive portal --- that is, you must be able to get to the Internet solely with a Wi-Fi username and password that are configured into the operating system (and not typed in a web browser)

   The Pi Zero, Pi Zero 2 and Pi 3B do not have built-in or WiFi, but you can use a USB WiFi adapter. With the Pi Zero and Pi Zero 2, you will need a special Micro-USB On The Go adapter which costs about $15.

3. You can use a hardwired Ethernet connector, if you have access to a router with an RJ-45 Ethernet jack. All Pi Zeros require a USB OTG and Ethernet USB adapter connect to Ethernet; the other Pis have an Ethernet socket that can either run at 10/100 or Gigabit. (Most routers can deliver either 100 or Gigabit on the RJ45 jack.)

### Connected a camera to a Raspberry Pi

All Raspberry Pi computers have a  MIPI CSI interface.
* MIPI is the Mobile Industry Processor Interface, the alliance that develops interface specifications for mobile and embedded devices.
* CSI is the Camera Serial Interface, the specific protocol standard used for high-speed transmission of video and image data from a camera to a processor.

To connect a camera, you should use a camera designed for the Raspberry Pi.
1. If you have a Raspberry Pi Zero / Zero W / Zero 2 W or a Pi 5, you will need camera with a 22-pin cable. This uses a 0.5mm pitch mini-connector.
2. If you have a Raspberry Pi 2, 3 or 4, you will need a camera with a 15-pin cable. This cable uses a standard full-size CSI connector.

### Displaying the output of a Pi

You can connect a full-size computer screen (or television!) to the Raspberry Pi using its built-in HDMI interface (although you may need a mini-HDMI or micro-HDMI to full-size HDMI adapter). You can also connect much smaller screens directly to the GPIO header (General Purpose Input/Output header):

* Raspberry Pi 2, 3, 4, and 5 computers have a 40-pin header. The Pi Zero has 40 holes for you to solder on your own 40-pin header, although you can buy the Pi Zero WH ("with header") model that comes With the Header already installed.

* The much older Raspberry PI Model A and B have a 26-pin header.

You can use the header to attach individual devices to your Pi, but you can also attach a HAT (Hardware Attached on Top), which is typically another card that plugs into the header and provides additional functionality. (The Pi Zero uses a mechanically different form factor called a pHAT, short for Plug-in Hardware Attached Top.) Some HATs you might find fun include:

* [Ada Fruit's Raspberry Pi Sense HAT](https://www.adafruit.com/product/2738), a HAT with an LED array and movement sensors
* [Tinkersphere's Gameboy-Styled HAT](https://tinkersphere.com/raspberry-pi-hats/2901-gameboy-style-gamepad-hat-for-raspberry-pi.html) which has tiny video game controls and a small screen
* [A 3.5 Inch 480x320 Touch Screen TFT LCD Display Panel](https://www.amazon.com/480x320-Touch-Screen-Display-Raspberry/dp/B0DY5BVGNH) which lets you have a self-contained computer that displays information and accepts input that fits in the palm of your hand (minus the power supply, alas).

Please post what you bought to the [Lab #0 discussion on Ed Discussion](https://edstem.org/us/courses/108391/discussion?category=Lab+%230).

# **Get an A**

Tell us (by taking the Lab 0 Quiz) that you’ve purchased your Raspberry Pi. Beyond submitting the Lab 0 Quiz, no other submission steps are required.

[image1]: <images/0-logo.png>

