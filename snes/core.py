"""
A Pythonic layer around bsnes' libsnes API.
"""
import ctypes
from snes import _snes_wrapper as W

# ctypes documentation says "Make sure you keep references to CFUNCTYPE objects
# as long as they are used from C code. ctypes doesn't, and if you don't, they
# may be garbage collected, crashing your program when a callback is made."
#
# So here we go.
_video_refresh_wrapper = None
_audio_sample_wrapper = None
_input_poll_wrapper = None
_input_state_wrapper = None

# Python wrapper functions that handle all the ctypes callback casting.
# TODO: add Python wrapper functions that decode the ctypes callback parameters
# into something more pythonic.

def set_video_refresh(callback):
	global _video_refresh_wrapper
	_video_refresh_wrapper = W.video_refresh_cb_t(callback)
	W.set_video_refresh(_video_refresh_wrapper)

def set_audio_sample(callback):
	global _audio_sample_wrapper
	_audio_sample_wrapper = W.audio_sample_cb_t(callback)
	W.set_audio_sample(_audio_sample_wrapper)

def set_input_poll(callback):
	global _input_poll_wrapper
	_input_poll_wrapper = W.input_poll_cb_t(callback)
	W.set_input_poll(_input_poll_wrapper)

def set_input_state(callback):
	global _input_state_wrapper
	_input_state_wrapper = W.input_state_cb_t(callback)
	W.set_input_state(_input_state_wrapper)

def load_cartridge_normal(data, mapping=None):
	W.load_cartridge_normal(mapping, ctypes.cast(data, W.data_p), len(data))

def init(libsnes_path):
	W.init(libsnes_path)

	# Because libsnes crashes if somebody calls "run" without setting up
	# callbacks, let's set them to dummy functions by default.
	set_video_refresh(lambda *args: None)
	set_audio_sample(lambda *args: None)
	set_input_poll(lambda: None)
	set_input_state(lambda *args: 0)

def run():
	W.run()
