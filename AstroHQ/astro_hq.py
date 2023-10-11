import time
import psutil
import argparse
import numpy as np
from astropy.io import fits
from picamera2 import Picamera2, libcamera

BOOT_TIME = psutil.boot_time()

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--exposure", type=float, default=1., help="exposure time in seconds")
parser.add_argument("-o", "--out-file", type=str, default="test.fits", help="file name/path to save output FITS image")
parser.add_argument("-n", "--number", type=int, default=1, help="number of frames to capture in sequence")

class PiHQCamera(Picamera2):

    def __init__(self) -> None:
        super().__init__()
        self.configuration = self.create_still_configuration(raw={"size": self.sensor_resolution,
                                                                  "format": self.sensor_format.replace("_CSI2P", "")},
                                                             controls={"AnalogueGain": 1.0, "ColourGains": (1., 1.), "AwbEnable": False,
                                                                       "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Off})

    @property
    def format(self) -> str:
        return self.sensor_format.split("_")[0]

    @property
    def configuration(self) -> dict:
        return self.camera_config
    
    @configuration.setter
    def configuration(self, new_config: dict) -> None:
        print("Configuring camera:", new_config)
        self.configure(new_config)
    
    @property
    def exposure(self) -> float:
        if hasattr(self.controls, "ExposureTime"):
            return self.controls.ExposureTime/1e6
        else:
            return np.nan
        
    @exposure.setter
    def exposure(self, set_val: float) -> None:
        self.controls.ExposureTime = int(set_val*1_000_000)
    
    def capture_raw_array(self, metadata=False) -> "np.ndarray|tuple[np.ndarray, dict]":
        request = self.capture_request()
        array: np.ndarray = request.make_array("raw")
        if metadata:
            capture_meta = request.get_metadata()
        request.release()
        low_bytes = array[:, 0::2].astype(np.uint16) & 255
        high_bytes = array[:, 1::2].astype(np.uint16) << 8
        array_rebuilt = high_bytes + low_bytes
        if metadata:
            return array_rebuilt, capture_meta
        else:
            return array_rebuilt
            
    def capture_hdu(self) -> fits.PrimaryHDU:
        array, meta = self.capture_raw_array(metadata=True)
        hcrop, vcrop, width, height = meta["ScalerCrop"]
        bpp = 12 # TODO
        black_pt = np.unique(meta["SensorBlackLevels"]).item()//(2**(16-bpp)) # 2**16 / 2**12 = 16
        array_cropped = array[vcrop:vcrop+height, hcrop:hcrop+width]
        print(f"Orig. array min/max: {array_cropped.min(), array_cropped.max()}")
        hdu = fits.PrimaryHDU(data=array_cropped.astype(np.uint16))
        hdu.header.set("BUNIT", "DN", "units of array values")
        hdu.header.set("FORMAT", self.format, "configured camera format")
        hdu.header.set("INSTRUME", "Raspberry Pi HQ Camera Module", "camera name")
        hdu.header.set("TELESCOP", None, "telescope model/name")
        hdu.header.set("DETECTOR", self.camera_properties["Model"].upper(), "camera sensor model")
        hdu.header.set("XPIXSIZE", self.camera_properties["UnitCellSize"][0]/1000, "[um] pixel width")
        hdu.header.set("YPIXSIZE", self.camera_properties["UnitCellSize"][1]/1000, "[um] pixel height")
        hdu.header.set("BAYER", ["RGGB", "GRBG", "GBRG", "BGGR", None][self.camera_properties["ColorFilterArrangement"]],
                       "Bayer matrix layout")
        hdu.header.set("FRAMELUX", meta["Lux"], "[lx] estimated scene brightness/illuminance")
        hdu.header.set("UPTIME", meta["SensorTimestamp"]/1e9, "[s] system uptime since boot")
        hdu.header.set("CCD-TEMP", meta["SensorTemperature"], "[degC] SensorTemperature")
        hdu.header.set("DATE-OBS", time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(BOOT_TIME+meta["SensorTimestamp"]/1e9)),
                       "[ISO cal] observation timestamp, UTC")
        hdu.header.set("EXPTIME", meta["ExposureTime"]/1e6, "[s] ExposureTime")
        hdu.header.set("DATAMIN", black_pt, "sensor black point")
        hdu.header.set("DATAMAX", 2**bpp-1, f"maximum representable value with {bpp} bits")
        hdu.header.set("DATE", time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), "[ISO cal] UTC time of HDU creation")
 
        hdu.add_checksum()
        return hdu
    
    def capture_fits(self, filename: str) -> None:
        hdu = self.capture_hdu()
        hdu.writeto(filename, overwrite=True)
        return

    def start_and_capture_fits(self, filename: str) -> None:
        self.start()
        self.capture_fits(filename)
        return


if __name__ == "__main__":
    args = parser.parse_args()

    hqcam = PiHQCamera()
    hqcam.exposure = args.exposure
    print("Exposure time:", hqcam.exposure)
    print("Configuration:", hqcam.configuration)

    if args.number==1:
        hqcam.start_and_capture_fits(args.out_file)
    else:
        hqcam.start()
        for i in range(args.number):
            hqcam.capture_fits(args.out_file.format(i))
            print(f"Captured {args.out_file.format(i)}")
    hqcam.stop()
    hqcam.close()
