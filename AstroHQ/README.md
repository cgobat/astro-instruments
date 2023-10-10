# AstroHQ camera control module

**Author:** [Caden Gobat](https://github.com/cgobat)

This is a [`picamera2`](https://github.com/raspberrypi/picamera2) (and, by extension, [`libcamera`](https://libcamera.org/))-based Python module for controlling the [Raspberry Pi HQ camera module](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/), with a specific focus on astronomy/astrophotography.

This software is designed to be run *on* the Raspberry Pi that the camera module is attached to. The main functionality lies in the `PiHQCamera` class, which subclasses `picamera2.Picamera2`. This work is currently in active development.