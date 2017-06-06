from astropy.io import fits
import argparse
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--open", action="store_true")
args = parser.parse_args()

def output(filename):
    if args.open:
        plt.show()
    else:
        plt.savefig(filename, bbox_inches='tight', dpi=300)

realhdus = fits.open("/Users/adamwheeler/Dropbox/y1_test/DECam_00241238_01.fits.fz")
realhdus.verify('silentfix')
print(realhdus.info())

simhdus = fits.open("output/sim_DECam_00241238_01.fits")
simhdus.verify('silentfix')
print(simhdus.info())

#zero out nans and infs in sim data
print(np.count_nonzero(simhdus[0].data[np.isinf(simhdus[0].data)]))
simhdus[0].data[np.isinf(simhdus[0].data)] = 0
print(np.count_nonzero(simhdus[0].data[np.isinf(simhdus[0].data)]))

print("building image. . .")
#get average pixel value
av = np.average(realhdus[1].data)
print("average pixel value: " + str(av))
av_weight = np.average(realhdus[3].data)
sigma = 1/np.sqrt(av_weight)
print("av weight: {}".format(av_weight))
print("=> sigma = {}".format(sigma))

f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
ax1.imshow(realhdus[1].data, cmap='Greys_r', 
           norm=LogNorm(vmax=av+10*sigma, vmin=av))

print("simulated av: {}".format(av))
ax2.imshow(simhdus[0].data, cmap='Greys_r',
           norm=LogNorm(vmax=av+10*sigma, vmin=av))
output("image.png")
plt.clf()

print("building histogram of pixel values. . .")
r = (200, 400)
plt.hist(realhdus[1].data.flatten(), range=r, bins=100, label="real", alpha=0.5)
plt.hist(simhdus[0].data.flatten(), range=r, bins=100, label="simulated", alpha=0.5)
plt.ylabel("pixels")
plt.legend(frameon=False)
output("histogram.png")
    

