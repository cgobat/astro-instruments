import argparse
import numpy as np
from astro_hq import PiHQCamera

parser = argparse.ArgumentParser()
parser.add_argument("--start", type=float, default=1.0)
parser.add_argument("--stop", type=float, default=31.0)
parser.add_argument("-N", type=int, default=16)
parser.add_argument("--gain", type=float, default=1.0)

if __name__ == "__main__":
    args = parser.parse_args()
    camera = PiHQCamera(gain=args.gain)

    for exp_time in np.linspace(args.start, args.stop, args.N, endpoint=True):
        camera.exposure = exp_time
        camera.start_and_capture_fits(f"bracket_{exp_time:05.2f}s.fits")
        camera.stop()

    camera.close()
