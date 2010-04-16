"""
A Pythonic layer around bsnes' libsnes API.
"""
import ctypes
from snes import _snes_wrapper as W

# Constants used by this interface
MEMORY_CARTRIDGE_RAM = 0
MEMORY_CARTRIDGE_RTC = 1
MEMORY_BSX_RAM = 2
MEMORY_BSX_PRAM = 3
MEMORY_SUFAMI_TURBO_A_RAM = 4
MEMORY_SUFAMI_TURBO_B_RAM = 5
MEMORY_GAME_BOY_RAM = 6
MEMORY_GAME_BOY_RTC = 7

VALID_MEMORY_TYPES = range(8)

PORT_1 = False
PORT_2 = True

DEVICE_NONE = 0
DEVICE_JOYPAD = 1
DEVICE_MULTITAP = 2
DEVICE_MOUSE = 3
DEVICE_SUPER_SCOPE = 4
DEVICE_JUSTIFIER = 5
DEVICE_JUSTIFIERS = 6

VALID_DEVICES = range(7)

DEVICE_ID_JOYPAD_B = 0
DEVICE_ID_JOYPAD_Y = 1
DEVICE_ID_JOYPAD_SELECT = 2
DEVICE_ID_JOYPAD_START = 3
DEVICE_ID_JOYPAD_UP = 4
DEVICE_ID_JOYPAD_DOWN = 5
DEVICE_ID_JOYPAD_LEFT = 6
DEVICE_ID_JOYPAD_RIGHT = 7
DEVICE_ID_JOYPAD_A = 8
DEVICE_ID_JOYPAD_X = 9
DEVICE_ID_JOYPAD_L = 10
DEVICE_ID_JOYPAD_R = 11

DEVICE_ID_MOUSE_X = 0
DEVICE_ID_MOUSE_Y = 1
DEVICE_ID_MOUSE_LEFT = 2
DEVICE_ID_MOUSE_RIGHT = 3

DEVICE_ID_SUPER_SCOPE_X = 0
DEVICE_ID_SUPER_SCOPE_Y = 1
DEVICE_ID_SUPER_SCOPE_TRIGGER = 2
DEVICE_ID_SUPER_SCOPE_CURSOR = 3
DEVICE_ID_SUPER_SCOPE_TURBO = 4
DEVICE_ID_SUPER_SCOPE_PAUSE = 5

DEVICE_ID_JUSTIFIER_X = 0
DEVICE_ID_JUSTIFIER_Y = 1
DEVICE_ID_JUSTIFIER_TRIGGER = 2
DEVICE_ID_JUSTIFIER_START = 3

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

	def wrapped_callback(data, width, height):
		hires = (width == 512)
		interlace = (height == 448 or height == 478)
		overscan = (height == 239 or height == 478)
		pitch = 512 if interlace else 1024 # in pixels

		callback(data, width, height, hires, interlace, overscan, pitch)

	_video_refresh_wrapper = W.video_refresh_cb_t(wrapped_callback)
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

# Because libsnes crashes if somebody calls "run" without setting up
# callbacks, let's set them to dummy functions by default.
set_video_refresh(lambda *args: None)
set_audio_sample(lambda *args: None)
set_input_poll(lambda: None)
set_input_state(lambda *args: 0)

def load_cartridge_normal(data, mapping=None):
	W.load_cartridge_normal(mapping, ctypes.cast(data, W.data_p), len(data))

def run():
	W.run()
