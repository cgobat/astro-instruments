import os
import re
import json
import psutil
import argparse
import subprocess
import time, datetime as dt
import numpy as np
from astropy.io import fits
from picamera2 import Picamera2
from libcamera import controls, Transform

BOOT_TIME = dt.datetime.utcfromtimestamp(psutil.boot_time())
sensortime_to_datetime = lambda sensortime_ns: BOOT_TIME+dt.timedelta(microseconds=sensortime_ns/1e3)

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--exposure", metavar="<seconds>", type=float, default=1., help="exposure time in seconds")
parser.add_argument("-o", "--out-file", metavar="<path>", type=str, default="test.fits", help="file name/path to save output FITS image")
parser.add_argument("-n", "--number", metavar="<#>", type=int, default=1, help="number of frames to capture in sequence")
parser.add_argument("-g", "--gain", metavar="<setting>", type=float, default=1., help="analog gain setting (default=1.0)")

def get_cpu_temp() -> float:
    proc = subprocess.run(["sensors", "-j"], text=True, capture_output=True)
    sensors = json.loads(proc.stdout)
    return sensors["cpu_thermal-virtual-0"]["temp1"]["temp1_input"]

class PiHQCamera(Picamera2):

    def __init__(self, gain=1.0, dpc=False) -> None:
        self.tuning_dict = self.load_tuning_file("imx477_scientific.json")
        tuning_algorithms = list(map(lambda algo: list(algo.keys()).pop(), self.tuning_dict["algorithms"]))
        self.tuning_dict["algorithms"][tuning_algorithms.index("rpi.dpc")]["rpi.dpc"] = {"strength": int(dpc)}
        super().__init__(tuning=self.tuning_dict)
        self.configuration = self.create_still_configuration(transform=Transform(), #hflip=False, vflip=True),
                                                             main={},
                                                             raw={"size": self.sensor_resolution,
                                                                  "format": self.sensor_format.replace("_CSI2P", "")},
                                                             controls={"AnalogueGain": gain, "ColourGains": (1., 1.),
                                                                       "AwbEnable": False, "AeEnable": False, "Sharpness": 0.,
                                                                       "NoiseReductionMode": controls.draft.NoiseReductionModeEnum.Off})
        self.start()
        print(f"Initial metadata:\n{self.capture_metadata()}")
        self.stop()
    
    @property
    def raw_format(self) -> str:
        return self.configuration["raw"]["format"]

    @property
    def configuration(self) -> dict:
        return self.camera_configuration()
    
    @configuration.setter
    def configuration(self, new_config: dict) -> None:
        # print("Configuring camera:", new_config)
        self.configure(new_config)
    
    @property
    def exposure(self) -> float:
        if hasattr(self.controls, "ExposureTime"):
            return self.controls.ExposureTime/1e6
        else:
            return np.nan
    
    @exposure.setter
    def exposure(self, set_val: float) -> None:
        self.controls.ExposureTime = round(set_val*1_000_000)
    
    @staticmethod
    def onboard_dpc_enabled() -> bool:
        with open("/sys/module/imx477/parameters/dpc_enable", "r") as dpc_file:
            status = dpc_file.read().strip()
        if status == "1":
            return True
        elif status == "0":
            return False
        else:
            raise ValueError(f"Unrecognized DPC status {status!r}")
    
    def pipeline_dpc_enabled(self) -> bool:
        try:
            tuning_file = os.environ["LIBCAMERA_RPI_TUNING_FILE"]
            tuning: dict = self.load_tuning_file(os.path.basename(tuning_file), dir=os.path.dirname(tuning_file))
        except KeyError:
            raise FileNotFoundError("Environment var LIBCAMERA_RPI_TUNING_FILE is not set")
        except RuntimeError:
            tuning = self.tuning_dict
        rpi_dpc_algo: dict = self.find_tuning_algo(tuning, "rpi.dpc")
        return bool(rpi_dpc_algo.get("strength", 1)) # TODO: verify that default strength is indeed 1 if not set
    
    def capture_raw_array(self, metadata=False) -> "np.ndarray|tuple[np.ndarray, dict]":
        print(f"Capture starting at  {dt.datetime.utcnow().isoformat()}")
        request = self.capture_request()
        array: np.ndarray = request.make_array("raw")
        if metadata:
            capture_meta = request.get_metadata()
        print(f"Releasing request at {dt.datetime.utcnow().isoformat()}")
        request.release()
        array_rebuilt = array.view("<u2")
        if metadata:
            return array_rebuilt, capture_meta
        else:
            return array_rebuilt
    
    def capture_hdu(self, crop=True) -> fits.PrimaryHDU:
        array, meta = self.capture_raw_array(metadata=True)
        meta.pop("ColourCorrectionMatrix") # omit from further use
        print(f"\nCapture metadata:\n{meta}\n")
        raw_format = re.match(r"(S)(?P<bayer>[RGB]{4})(?P<bits>\d+)(_CSI2P)?", self.raw_format)
        bpp = int(raw_format.group("bits"))
        black_pt = np.unique(meta["SensorBlackLevels"]).item()//(2**(16-bpp)) # 2**16 / 2**12 = 16
        bayer_order = raw_format.group("bayer")[2:] + raw_format.group("bayer")[:2] # flip vertically to match FITS
        if crop:
            hcrop, vcrop, width, height = meta["ScalerCrop"]
            array = array[vcrop:vcrop+height, hcrop:hcrop+width]
        print(f"Orig. array min/max: {array.min(), array.max()}")
        hdu = fits.PrimaryHDU(data=array[::-1, :].astype(np.uint16))
        hdu.header.set("BUNIT", "DN", "units of array values")
        hdu.header.set("INST-SEP", "-"*19+" INSTRUMENT/OBSERVATORY INFO "+"-"*20)
        # hdu.header.set("FORMAT", raw_format, "configured camera format")
        hdu.header.set("INSTRUME", "Raspberry Pi HQ Camera Module", "camera name")
        hdu.header.set("TELESCOP", None, "telescope model/name")
        hdu.header.set("FOCALLEN", None, "[mm] telescope/lens focal length")
        hdu.header.set("PROGRAM", "AstroHQ by cgobat", "instrument software that generated this HDU")
        hdu.header.set("PLATFORM", self.platform.name, "platform architecture (VC4/PISP)")
        hdu.header.set("DET-SEP", "-"*22 + " DETECTOR CONFIGURATION " + "-"*22)
        hdu.header.set("DETECTOR", self.camera_properties["Model"].upper(), "camera sensor model")
        hdu.header.set("XPIXSIZE", self.camera_properties["UnitCellSize"][0]/1000, "[um] pixel width")
        hdu.header.set("YPIXSIZE", self.camera_properties["UnitCellSize"][1]/1000, "[um] pixel height")
        hdu.header.set("BAYERPAT", bayer_order, "Bayer filter order/layout")
        hdu.header.set("BITDEPTH", bpp, "number of bits per pixel value")
        hdu.header.set("DATAMIN", black_pt, "[DN] sensor black point")
        hdu.header.set("DATAMAX", 2**bpp-1, f"[DN] maximum representable value with {bpp} bits")
        hdu.header.set("GAIN", meta["AnalogueGain"], "analog gain setting")
        hdu.header.set("SONY_DPC", self.onboard_dpc_enabled(), "on-sensor defective pixel correction status")
        hdu.header.set("RPI_DPC", self.pipeline_dpc_enabled(), "libcamera defective pixel correction status")
        hdu.header.set("META-SEP", "-"*23+" OBSERVATION METADATA "+"-"*23)
        hdu.header.set("FRAMELUX", meta["Lux"], "[lx] estimated scene brightness/illuminance")
        hdu.header.set("COLORTMP", meta["ColourTemperature"], "[K] estimated average color temperature")
        hdu.header.set("FOCUSFOM", meta["FocusFoM"], "image focus figure of merit")
        # hdu.header.set("UPTIME", meta["SensorTimestamp"]/1e9, "[s] system uptime since boot")
        hdu.header.set("CPU-TEMP", get_cpu_temp(), "[degC] processor/CPU temperature")
        hdu.header.set("CCD-TEMP", meta["SensorTemperature"], "[degC] sensor/detector temperature")
        hdu.header.set("EXPTIME", meta["ExposureTime"]/1e6, "[s] image exposure time")
        hdu.header.set("DATE-END", sensortime_to_datetime(meta["SensorTimestamp"]).isoformat(),
                       "[ISO UTC] time of first pixel readout")
        hdu.header.set("FILE-SEP", "-"*27 + " FILE METADATA " + "-"*26)
        hdu.header.set("DATE", dt.datetime.utcnow().isoformat(), "[ISO UTC] time of HDU creation")
         
        hdu.add_checksum()
        return hdu
    
    def capture_fits(self, filename: str) -> None:
        hdu = self.capture_hdu()
        hdu.writeto(filename, overwrite=True)
        return
    
    def start_and_capture_fits(self, filename: str) -> None:
        self.start()
        # throwaway = self.capture_metadata()
        # throwaway.pop("ColourCorrectionMatrix")
        # throwaway["SensorTimestamp"] = sensortime_to_datetime(throwaway["SensorTimestamp"])
        # print("Initial metadata:", throwaway)
        self.capture_fits(filename)
        return


if __name__ == "__main__":
    print(f"Execution start: {dt.datetime.utcnow()} UTC")
    args = parser.parse_args()

    hqcam = PiHQCamera(gain=args.gain)
    print("LIBCAMERA_RPI_TUNING_FILE:", os.environ.get("LIBCAMERA_RPI_TUNING_FILE", "<not found>"))
    hqcam.exposure = args.exposure
    print("Configuration:")
    for kw, val in hqcam.configuration.items():
        print(f"  - {kw}: {val}")

    if args.number==1:
        hqcam.start_and_capture_fits(args.out_file)
    else:
        hqcam.start()
        # throwaway = hqcam.capture_metadata()
        # throwaway.pop("ColourCorrectionMatrix")
        # print(f"\nInitial metadata:\n{throwaway}\n")
        for i in range(args.number):
            hqcam.capture_fits(args.out_file.format(i))
            print(f"Captured {args.out_file.format(i)}")
    hqcam.stop()
    hqcam.close()
