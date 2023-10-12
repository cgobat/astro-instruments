import numpy as np
from astropy.io import fits
from matplotlib import pyplot as plt

def demosaic(img_array: np.ndarray, bayer_pattern: str = "RGGB") -> np.ndarray:
    R_mask, Gr_mask, Gb_mask, B_mask = [np.zeros((img_array.shape[0], img_array.shape[1]), dtype=np.uint8) for c in bayer_pattern]
    if bayer_pattern == "RGGB":
        R_mask[0::2, 0::2] = 1
        Gr_mask[0::2, 1::2] = 1
        Gb_mask[1::2, 0::2] = 1
        B_mask[1::2, 1::2] = 1
    elif bayer_pattern == "BGGR":
        B_mask[0::2, 0::2] = 1
        Gb_mask[0::2, 1::2] = 1
        Gr_mask[1::2, 0::2] = 1
        R_mask[1::2, 1::2] = 1
    elif bayer_pattern == "GRBG":
        Gr_mask[0::2, 0::2] = 1
        R_mask[0::2, 1::2] = 1
        B_mask[1::2, 0::2] = 1
        Gb_mask[1::2, 1::2] = 1
    elif bayer_pattern == "GBRG":
        Gb_mask[0::2, 0::2] = 1
        B_mask[0::2, 1::2] = 1
        R_mask[1::2, 0::2] = 1
        Gr_mask[1::2, 1::2] = 1
    else:
        raise ValueError(f"{bayer_pattern} is not a valid Bayer pattern")
    G_mask = Gr_mask+Gb_mask
    
    rgb_array = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=img_array.dtype)
    rgb_array[np.where(R_mask)[0], np.where(R_mask)[1], 0] = img_array[np.where(R_mask)]
    rgb_array[np.where(G_mask)[0], np.where(G_mask)[1], 1] = img_array[np.where(G_mask)]/2
    rgb_array[np.where(B_mask)[0], np.where(B_mask)[1], 2] = img_array[np.where(B_mask)]

    return rgb_array

if __name__ == "__main__":
    test_array = np.arange(0, 16).reshape(4, 4)
    test_array, header = fits.getdata("~/Downloads/img_3s.fits", header=True)
    rgb = demosaic(test_array[::-1]/4096)
    plt.imshow(rgb/rgb.max())
    plt.show()
