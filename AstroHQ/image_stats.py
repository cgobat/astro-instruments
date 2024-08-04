import argparse
import numpy as np
from astropy.io import fits
from scipy import optimize, stats
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str, help="FITS file to process")

def bimodal_norm_pdf(x, A1, mu1, sigma1, A2, mu2, sigma2):
    dist1 = stats.norm(mu1, sigma1)
    dist2 = stats.norm(mu2, sigma2)
    return A1*dist1.pdf(x) + A2*dist2.pdf(x)

if __name__ == "__main__":
    args = parser.parse_args()
    data_array = fits.getdata(args.filename)
    print(f"Average: {np.mean(data_array):.2f} ± {np.std(data_array):.2f}")
    print(f"Summary: {stats.describe(data_array.ravel())}")
    print("Percentiles:")
    for percentile, value in zip([0.25, 0.5, 0.75, 0.99],
                                 np.quantile(data_array,
                                             [0.25, 0.5, 0.75, 0.999])):
        print(f"  {percentile:.0%}: {value}")
    clipped = np.clip(data_array.ravel(), 256, np.quantile(data_array, 0.999))
    clipped -= 256
    hist_vals, hist_bins = np.histogram(clipped, 40)
    hist_bins = np.mean([hist_bins[1:], hist_bins[:-1]], axis=0)
    try:
        fit_params, cov = optimize.curve_fit(bimodal_norm_pdf, hist_bins, hist_vals, p0=[2e6, 16, 2, 1e6, 40, 10])
        print("Fit parameters:")
        for kw, i in zip(["A1", "μ1", "σ1", "A2", "μ2", "σ2"], [1, 2, 4, 5]):
            print(f"  {kw}: {fit_params[i]:6.3f}")
    except RuntimeError:
        print("Curve fit did not converge.")
    plt.hist(clipped, 40)
    plt.plot(np.linspace(0, clipped.max(), 100), bimodal_norm_pdf(np.linspace(0, clipped.max(), 100), *fit_params))
    plt.ylim(0,)
    plt.show()
