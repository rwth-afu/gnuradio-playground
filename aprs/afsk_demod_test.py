#!/usr/bin/python3 
"""
    generate a dummy AFSK signal that encodes a 010101.. datastream
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt

##############################
# Settings
SR = 50e3
DT = 1/SR

DATA_RATE = 1200
DATA_DT = 1/DATA_RATE

HUB = 2.5e3

NOISE_AMPLITUDE = [0.0, 0.3, 0.8]

DURATION = 0.007

##############################
# Functions

def lowpass(sr, upper_freq, order):
    coefficients = butter(order, upper_freq, btype='lowpass', analog=False, output='sos', fs=sr)
    return lambda sig: sosfilt(coefficients, sig)

def highpass(sr, upper_freq, order):
    coefficients = butter(order, upper_freq, btype='highpass', analog=False, output='sos', fs=sr)
    return lambda sig: sosfilt(coefficients, sig)

for noise_amplitude in NOISE_AMPLITUDE:
    ##############################
    # Setup
    T = np.arange(0, DURATION, DT)

    DATA = list()
    AUDIO = list()
    RF = list()

    ##############################
    # Generate
    audio_phase = 0
    rf_phase = 0
    for t in T:
        # determine if we are in a one or 0
        bit = (t%(DATA_DT*2))/(DATA_DT*2) > 0.5

        mod_freq = 1200 + bit*1000

        audio_phase += 2*np.pi*mod_freq * DT

        audio = np.sin(audio_phase)
        
        rf_freq = HUB * audio
        rf_phase += 2*np.pi *rf_freq * DT
        rf = np.e**(2*np.pi * 1j * rf_phase)

        rf_noise = np.random.normal(scale=noise_amplitude)

        DATA.append(bit)
        AUDIO.append(audio)
        RF.append(rf+rf_noise)

    ##############################
    # Save to disk
    DATA = np.array(DATA)
    AUDIO = np.array(AUDIO)
    RF = np.array(RF)

    RF.tofile('out/dummy_afsk_signal.c64')

    ##############################
    # try demodulation
    RF_lowpass = RF # lowpass(SR, 20e3, 7)(RF)
    demod_audio = np.angle(RF_lowpass[1:]/RF_lowpass[:-1])/np.pi*2
    demod_audio = lowpass(SR, (1200+500)*2, 4)(demod_audio)

    lower_signal_audio = lowpass(SR, 1200+500, 7)(demod_audio)
    higher_signal_audio = highpass(SR, 1200+500, 7)(demod_audio)

    recovered_data_signal = lowpass(SR, 2400, 7)(lower_signal_audio**2 - higher_signal_audio**2)

    ##############################
    # Plot
    fig, ax = plt.subplots(7, sharex=True, figsize=(7, 13))

    for axi in ax:
        axi.grid(axis='x')
        axi.set_ylim(-1.5, 1.5)

    ax[0].plot(T, DATA)
    ax[0].set_ylabel("In Data")
    ax[0].set_ylabel("In Data")
    ax[0].set_ylim(-0.2, 1.2)

    ax[1].plot(T, AUDIO)
    ax[1].set_ylabel("In Audio")

    ax[2].plot(T, RF.real, label='I')
    ax[2].plot(T, RF.imag, label='Q')
    ax[2].legend(loc=3)
    ax[2].set_ylabel("RF I/Q\nwith noise")
    ax[2].set_ylim(-3, 3)

    ax[3].plot(T[:len(demod_audio)], demod_audio)
    ax[3].set_ylabel("Demod Audio")

    ax[4].plot(T[:-1], lower_signal_audio**2, label='lower')
    ax[4].plot(T[:-1], higher_signal_audio**2, label='higher')
    ax[4].legend(loc=3)
    ax[4].set_ylabel("Audio FSK demod\nFilter output")
    ax[4].set_ylim(0, 2)

    ax[5].plot(T[:-1], recovered_data_signal, label='diff')
    ax[5].set_ylabel("Audio FSK\ndemod\nlow-high")

    ax[6].plot(T[:-1], recovered_data_signal>0, label='recovered_data')
    ax[6].plot(T, DATA, label='input', ls=':')
    ax[6].set_ylabel("recovered\ndata signal")
    ax[6].legend(loc=3)
    ax[6].set_ylim(-0.2, 1.2)

    ax[-1].set_xlabel("Time [s]")

    ax[0].set_xlim(DURATION*0.3, DURATION)

    ax[0].set_title(f"Simple AFSK demodulation test (relative noise amplitude = {noise_amplitude})")

    plt.tight_layout()

    for filetype in ['png', 'svg']:
        plt.savefig(f"images/afsk_demod_sim_noise-{noise_amplitude:.1f}.{filetype}")


# plt.show()
