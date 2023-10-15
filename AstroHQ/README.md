# AstroHQ camera control module

**Author:** [Caden Gobat](https://github.com/cgobat)

This is a [`picamera2`](https://github.com/raspberrypi/picamera2) (and, by extension, [`libcamera`](https://libcamera.org/))-based Python module for controlling the [Raspberry Pi HQ camera module](https://www.raspberrypi.com/products/raspberry-pi-high-quality-camera/), with a specific focus on astronomy/astrophotography.

This software is designed to be run *on* the Raspberry Pi that the camera module is attached to. The main functionality lies in the `PiHQCamera` class, which subclasses `picamera2.Picamera2`. This work is currently in active development.

The data contained in [`spectral_response.npy`](./spectral_response.npy) is sourced from the [`IMX477.json`](https://github.com/raspberrypi/picamera2/files/12910224/IMX477.json) CFA transmission curves, along with [Hoya IR filter transmission measurements](https://github.com/raspberrypi/picamera2/files/12910217/HQ.Cam.IR_Filter_Transmission_UV.und.VIS.csv) by @cpixip. See [this comment](https://github.com/raspberrypi/picamera2/issues/462#issuecomment-1763456298) for details.