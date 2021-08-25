####################################################################################################
# File:     sp.py
# Purpose:  Signal processing tools (including spectrogram plotting).
#
# Author:   Luke Poeppel
#
# Location: Kent, 2021
####################################################################################################
"""
Signal processing tools. Some of these tools are from Dr. Nori Jacoby's Computational Auditory
Perception group. These are noted with "CAP" in the docstring.
"""
import librosa
import librosa.display
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

from scipy.signal import (
	resample,
	butter,
	filtfilt
)

mpl.style.use("bmh")

SAMPLE_RATE = 44100

def resample_(samples, source_rate, target_rate):
	"""
	Function for resampling an array (with fs ``source_rate``) to ``target_rate``.

	:param samples: an array of samples.
	:param int source_rate: the sample rate of the source samples.
	:param int target_rate: the desired sample rate of the resampled array.
	"""
	resample_factor = float(target_rate) / float(source_rate)
	resampled = resample(samples, int(len(samples) * resample_factor))
	return resampled

def pad_samples(samples, final_duration, fs=44100):
	"""
	Function for zero-padding a list of samples.

	:param samples: an array of samples.
	:param float expected_duration: the desired final duration (with padding) in ms.
	:param int fs: sample rate. Default is 44.1k.
	"""
	expected_length = int(fs * (1000 / fs) * final_duration)
	if len(samples) < expected_length:
		diff = expected_length - len(samples)
		padding = np.zeros(diff)
		padded_samples = np.concatenate((samples, padding))
	else:
		padded_samples = samples[:expected_length]

	return padded_samples

def ms_to_samples(ms, fs):
	"""
	Function for converting a given number of milliseconds to the number of samples (with
	sample rate ``fs``). CAP.

	>>> ms_to_samples(107, fs=44100)
	4719
	"""
	return int(np.floor(ms / 1000 * fs) + 1)

def samples_to_ms(sample, fs):
	"""
	Function for converting a given number of samples (and a sample rate `fs`) to milliseconds.
	CAP.
	"""
	return sample * 1000 / fs

def freq2midi(f0):
	"""
	Function for converting a frequency to MIDI. CAP.

	:param f0: frequency in Hertz.
	:return: ``f0`` in MIDI.
	:rtype: float
	"""
	if f0 <= 0:
		return 0
	else:
		res = 12 * (np.log2(f0) - np.log2(440)) + 69
		if not(res < 0):
			return res
		else:
			return 0

def midi2freq(midi):
	"""
	Function for converting a MIDI number to the associated frequency. CAP.

	:param midi: MIDI number.
	:return: ``midi`` in Hertz.
	:rtype: float
	"""
	return (440 / 32) * (2 ** ((midi - 9) / 12))

def freq2nyq(freq, fs):
	"""
	Calculates the nyquist frequency.
	"""
	nyquist = fs / 2.0
	return freq / nyquist

def build_filter(window):
	b, a = butter(2, window, btype='band', analog=False, output="ba")
	return (b, a)

def band_pass_sharp(samples, lower, upper, fs=44100):
	"""
	Doubly-applied (i.e. sharp) butterworth bandpass filter. CAP.

	:param samples: an array of samples.
	:param lower: lowest frequency in Hertz.
	:param upper: highest frequency in Hertz.
	:param int fs: sample rate.
	"""
	window = [freq2nyq(lower, fs), freq2nyq(upper, fs)]
	b, a = build_filter(window)
	filtered_signal_1 = filtfilt(b, a, samples)
	filtered_signal_2 = filtfilt(b, a, filtered_signal_1)
	return filtered_signal_2

def plot_audio_file(filepath, title=None, save_path=None):
	"""
	Function for plotting an audio file.

	:param str filepath: a path to an audio file.
	:param str title: optional title for the plot. Default is ``None``.
	:param str save_path: optional path to save the plot. Default is ``None``.
	"""
	samples, fs = librosa.load(filepath)
	samples = resample_(samples, source_rate=fs, target_rate=SAMPLE_RATE)

	plt.plot(samples)

	plt.title(title, fontname="Times", fontsize=14)
	plt.xlabel("Time", fontname="Times", fontsize=12)
	plt.ylabel("Amplitude", fontname="Times", fontsize=12)

	if save_path:
		plt.savefig(save_path, dpi=350)

	return plt

def plot_spectrogram(
		filepath,
		max_freq=8000,
		title=None,
		save_path=None
	):
	"""
	Function for plotting the spectrogram of an audio file.
	"""
	samples, fs = librosa.load(filepath)
	samples = resample_(samples, source_rate=fs, target_rate=SAMPLE_RATE)
	S = librosa.feature.melspectrogram(y=samples, sr=SAMPLE_RATE, fmax=max_freq)

	S_dB = librosa.power_to_db(S, ref=np.max)
	img = librosa.display.specshow(
		S_dB,
		x_axis="time",
		y_axis="mel",
		sr=SAMPLE_RATE,
		fmax=max_freq,
	)
	cbar = plt.colorbar(img, format="%+2.0f dB")
	for t in cbar.ax.get_yticklabels():
		t.set_fontsize(10)
		t.set_fontname("Times")

	plt.xticks(fontname="Times")
	plt.xlabel("Time (s)", fontname="Times", fontsize=12)
	plt.yticks(list(range(0, 9000, 1000)), fontname="Times")
	plt.ylabel("Frequency (Hz)", fontname="Times", fontsize=12)
	plt.title(title, fontname="Times", fontsize=14)
	if save_path:
		plt.savefig(save_path, dpi=350)

	return plt