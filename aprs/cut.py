import numpy as np
import matplotlib.pyplot as plt
from afsk_demod_test import lowpass

def downsample(X, n):
    nblocks = int(len(X)//n)
    X = X[:nblocks*n]
    X = X.reshape((nblocks, n))
    X = np.mean(X, axis=1)
    return X

def filter_closest(X, min_dist):
    retval = []
    for x in X:
        if len(retval) == 0 or min(abs(r-x) for r in retval) > min_dist:
            retval.append(x)
    return retval

##############################
## Settings
SR = 50e3
THRESHOLD = 0.05
DOWNSAMPLE = 50
MIN_LEN = 1000

PADDING = int(0.3*SR)

# load signal
X = np.fromfile("in/gnuradio_aprs.c64", np.complex64)

# calculate amplitude
AMPLITUDE = downsample(np.abs(X), DOWNSAMPLE)

# find the blocks with a signal
jump = AMPLITUDE[1:] - AMPLITUDE[:-1]

starts = np.where(jump > THRESHOLD)[0]
starts = filter_closest(starts, MIN_LEN)
ends = np.where(jump < -THRESHOLD)[0]
ends = filter_closest(ends, MIN_LEN)

print(len(starts))
print(starts)
print(len(ends))
print(ends)

assert len(starts) == len(ends)
     
# select only the blocks with signal
selected_ranges = [[s*DOWNSAMPLE-PADDING, e*DOWNSAMPLE+PADDING] for s,e in zip(starts, ends)]
print(selected_ranges)
selected_signal = np.concatenate([X[s*DOWNSAMPLE-PADDING:e*DOWNSAMPLE+PADDING] for s,e in zip(starts, ends)])

# save to file
selected_signal.tofile('in/gnuradio_aprs_cut.c64')

# plot
plt.figure()
plt.plot(AMPLITUDE)

for x in starts:
    plt.axvline(x, c='g')
for x in ends:
    plt.axvline(x, c='r')

plt.figure()
AMPLITUDE_result = downsample(np.abs(selected_signal), DOWNSAMPLE)
plt.plot(AMPLITUDE_result)

plt.show()
