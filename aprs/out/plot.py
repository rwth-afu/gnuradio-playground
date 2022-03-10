import numpy as np
import matplotlib.pyplot as plt

SR = 50e3
DR = 1200

def data_recovery_nrzi(data, sr, dr):
    """
        data: input data made up of 0 and 1 values with NRZI coding
        sr:   sample rate of data
        dr:   baud rate of the encoded data stream
    """
    symbol_duration = sr/dr
    
    changes = np.array( np.nonzero(data[1:]-data[:-1])[0] )
    print(len(changes))

    change_interval = changes[1:] - changes[:-1]

    bits = [[1]*int(np.round(interval/symbol_duration)-1) + [0] for interval in change_interval]
    bits = sum(bits, [])

    '''
    plt.figure()
    plt.hist(change_interval/sr, bins=200)
    for x in np.arange(1, 10)/dr:
        plt.axvline(x, c='r')
    plt.xlabel('interval [s]')
    plt.ylabel('occurence [1]')
    '''

    return bits

def bitstream_to_bytes_big_endian(bitstream):
    assert len(bitstream)%8 == 0
    data = np.reshape(bitstream, (len(bitstream)//8, 8))
    data = np.sum(data * np.array([2**(i) for i in range(8)]), axis=1)
    return data

def extract_frames(bitstream):
    sync_pos = []
    idx = 0
    synced = False

    acc = []
    frames = []
    stuffing_count_ones = 0
    while idx < len(bitstream)-8:
        # check for sync
        if bitstream[idx:idx+8] == [0, 1, 1, 1, 1, 1, 1, 0]:
            if len(acc) > 0:
                frames.append(acc)
                acc = []
                stuffing_count_ones = 0
            idx += 8
        else:

            if bitstream[idx]:
                stuffing_count_ones += 1
                acc.append(bitstream[idx])
            else:
                if stuffing_count_ones < 5: # handle bit stuffing
                    acc.append(bitstream[idx])
                else:
                    print('skipping stuffed one')
                stuffing_count_ones = 0

            idx += 1

    # keep only frames of correct length
    frames = [f for f in frames if len(f)%8 ==0]

    for i in frames:
        print('len', len(i), len(i)%8)

    frames = [bitstream_to_bytes_big_endian(f) for f in frames]

    for i in frames:
        print('len', len(i), bytes(list(i)))

    return frames
            
def parse_packet(data):
    # determine the digipeater lenght (I'm absolutely not sure that this is the intended way!)
    control_field_idx = None
    for idx in range(14,len(data)-1):
        if (data[idx:idx+2] == [0x03, 0xf0]).all():
            control_field_idx = idx
            break
    if control_field_idx is None:
        return None

    # parse package
    package = {}
    package['dst_addr'] = bytes(list(data[:7]>>1))
    package['src_addr'] = bytes(list(data[7:14]>>1))
    package['digipeater_addr'] = bytes(list(data[14:control_field_idx]>>1))
    package['data'] = bytes(list(data[control_field_idx+2:-1]))
    package['fcs'] = data[-1]

    return package 

X = np.fromfile("afsk_signal_demod_out.f32", np.float32)
HP = np.fromfile("afsk_signal_demod_out_hp.f32", np.float32)
LP = np.fromfile("afsk_signal_demod_out_lp.f32", np.float32)


bitstream = data_recovery_nrzi((X>0).astype(np.int8), SR, DR)
frames = extract_frames(bitstream)
packages = [parse_packet(f) for f in frames]

for p in packages:
    print(p)

'''
fig, ax = plt.subplots(3, sharex=True)
ax[0].plot(X)
ax[0].plot(X>0)
#ax[1].plot(HP)
#ax[2].plot(LP)
'''

plt.show()
