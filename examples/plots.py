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

realhdus = fits.open("DECam_00158414_01.fits.fz")
realhdus.verify('silentfix')
print(realhdus.info())

simhdus = fits.open("output/sim_DECam_00158414_01.fits.fz")
simhdus.verify('silentfix')
print(simhdus.info())


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
ax2.imshow(simhdus[1].data, cmap='Greys_r',
           norm=LogNorm(vmax=av+10*sigma, vmin=av))
output("image.png")
plt.clf()

print("building histogram of pixel values. . .")
r = (1900, 2300)
plt.hist(realhdus[1].data.flatten(), range=r, bins=100, label="real", alpha=0.5)
plt.hist(simhdus[1].data.flatten(), range=r, bins=100, label="simulated", alpha=0.5)
plt.ylabel("pixels")
plt.legend(frameon=False)
output("histogram.png")
    

