import time
import argparse
import numpy as np
from astropy.io import fits
from picamera2 import Picamera2, libcamera

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--exposure", type=int, default=1, help="exposure time in seconds")
parser.add_argument("-o", "--out-file", type=str, default="test.fits", help="file name/path to save output FITS image")

class PiHQCamera(Picamera2):

    def __init__(self) -> None:
        super().__init__()
        self.configuration = self.create_still_configuration(raw={"size": self.sensor_resolution,
                                                                  "format": self.sensor_format.replace("_CSI2P", "")},
                                                             controls={"AnalogueGain": 1.0, "ColourGains": (1., 1.), "AwbEnable": False,
                                                                       "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Off})

    @property
    def configuration(self) -> dict:
        return self.camera_config
    
    @configuration.setter
    def configuration(self, new_config: dict) -> None:
        self.configure(new_config)
    
    @property
    def exposure(self) -> float:
        if hasattr(self.controls, "ExposureTime"):
            return self.controls.ExposureTime/1e6
        else:
            return np.nan
        
    @exposure.setter
    def exposure(self, set_val: float) -> None:
        self.controls.ExposureTime = int(set_val*1e6)
    
    def capture_raw_array(self, metadata=False) -> np.ndarray:
        request = self.capture_request()
        array = request.make_array("raw")
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
        hdu = fits.PrimaryHDU(data=array[vcrop:vcrop+height, hcrop:hcrop+width])
        hdu.header.set("DATE", time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), "[ISO cal] UTC time of HDU creation")
        # hdu.header.set("DATE-OBS")
        hdu.header.set("DETECTOR", self.camera_properties["Model"].upper(), "camera sensor model")
        hdu.header.set("XPIXSIZE", self.camera_properties["UnitCellSize"][0]/1000, "[um] pixel width")
        hdu.header.set("YPIXSIZE", self.camera_properties["UnitCellSize"][1]/1000, "[um] pixel height")
        hdu.header.set("BAYER", ["RGGB", "GRBG", "GBRG", "BGGR", None][self.camera_properties["ColorFilterArrangement"]],
                       "Bayer matrix layout")
        hdu.header.set("UPTIME", meta["SensorTimestamp"]/1e9, "[s] system uptime since boot")
        hdu.header.set("CCD-TEMP", meta["SensorTemperature"], "[degC] SensorTemperature")
        hdu.header.set("EXPTIME", meta["ExposureTime"]/1e6, "[s] ExposureTime")
        hdu.header.set("DURATION", meta["FrameDuration"]/1e6, "[s] FrameDuration")
        hdu.header.set("BLACKPT", meta["SensorBlackLevels"][0], "black point")
        hdu.header["HISTORY"] = "Values scaled by factor of 16 to use full 16-bit range for original 12-bit pixels."
        # hdu.scale(bzero=meta["SensorBlackLevels"][0])
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

    hqcam.start_and_capture_fits(args.out_file)
    hqcam.stop()
