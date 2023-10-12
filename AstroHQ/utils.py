import numpy as np
from astropy.io import fits
from matplotlib import pyplot as plt

def debayer(img_array: np.ndarray, bayer_pattern: str = "RGGB", how="mosaic") -> np.ndarray:
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
    if how=="mosaic":
        pass
    elif how=="neighbors": # assumes GBRG for the moment
        # first column, second row (green)
        rgb_array[1:-1:2, 0::2, 1] = np.mean([img_array[0:-2:2, 0::2], img_array[2::2, 0::2]], axis=0)
        # second column, first row (green)
        rgb_array[0::2, 1:-1:2, 1] = np.mean([img_array[0::2, 0:-2:2], img_array[0::2, 2::2]], axis=0)

        # fill in R even rows
        rgb_array[0::2, 2::2, 0] = np.mean([img_array[0::2, 1:-2:2], img_array[0::2, 3::2]], axis=0)
        # use that to fill in odd rows
        rgb_array[1::2, :, 0] = np.mean([rgb_array[0:-2:2, :, 0], rgb_array[2::2, :, 0]])

        # fill in B even columns
        rgb_array[2::2, 0::2, 2] = np.mean([img_array[1:-2:2, 0::2], img_array[3::2, 0::2]], axis=0)
        # use that to fill in odd columns
        rgb_array[:, 1:-1:2, 2] = np.mean([rgb_array[:, 0:-2:2, 2], rgb_array[:, 2::2, 2]], axis=0)
    else:
        raise ValueError
    return rgb_array

if __name__ == "__main__":
    test_array = np.arange(0, 16).reshape(4, 4)
    test_array, header = fits.getdata("img_2s.fits", header=True)
    values = test_array.ravel()
    threeSigmaUL = np.mean(values)+3*np.std(values)
    rgb = debayer(np.clip(test_array[::-1], 0, threeSigmaUL), header["BAYERPAT"], "neighbors")
    plt.imshow(rgb/rgb.max())
    plt.show()
