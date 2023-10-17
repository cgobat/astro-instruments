import numpy as np
from scipy.ndimage import convolve
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
    rgb_array[np.where(G_mask)[0], np.where(G_mask)[1], 1] = img_array[np.where(G_mask)]
    rgb_array[np.where(B_mask)[0], np.where(B_mask)[1], 2] = img_array[np.where(B_mask)]
    fig, axs = plt.subplots(2, 2)
    axs[0, 0].imshow(img_array, cmap="binary_r")
    axs[0, 1].imshow(img_array[np.where(R_mask)].reshape(3040//2, 4056//2), cmap="Reds_r")
    axs[1, 0].imshow(img_array[np.where(G_mask)].reshape(3040, 4056//2), cmap="Greens_r")
    axs[1, 1].imshow(img_array[np.where(B_mask)].reshape(3040//2, 4056//2), cmap="Blues_r")
    plt.show(block=False)
    if how=="mosaic":
        pass
    elif how=="bilinear":
        kernel_G = np.array([[0.00, 0.25, 0.00],
                             [0.25, 1.00, 0.25],
                             [0.00, 0.25, 0.00]])

        kernel_RB = np.array([[0.25, 0.50, 0.25],
                              [0.50, 1.00, 0.50],
                              [0.25, 0.50, 0.25]])
        
        rgb_array[:,:,0] = convolve(rgb_array[:,:,0], kernel_RB, mode="nearest")
        rgb_array[:,:,1] = convolve(rgb_array[:,:,1], kernel_G, mode="nearest")
        rgb_array[:,:,2] = convolve(rgb_array[:,:,2], kernel_RB, mode="nearest")
    else:
        raise ValueError
    return rgb_array

if __name__ == "__main__":
    test_array = np.arange(0, 16).reshape(4, 4)
    test_array, header = fits.getdata("~/Downloads/img_2s.fits", header=True)
    values = test_array.ravel()
    threeSigmaUL = np.mean(values)+3*np.std(values)
    array_clipped = np.clip(test_array[::-1, :], 0, threeSigmaUL)
    rgb = debayer(test_array[::-1], header["BAYERPAT"], "mosaic")
    fig = plt.figure()
    plt.imshow(rgb/(0.5*threeSigmaUL))
    plt.show()
