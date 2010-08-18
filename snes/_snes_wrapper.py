"""
A low-level ctypes wrapper for the libsnes API.

You probably want to use the Python API in snes.core instead of this.
"""
import ctypes, atexit

# Define some ctypes data types the libsnes API uses
data_p = ctypes.POINTER(ctypes.c_ubyte)
pixel_p = ctypes.POINTER(ctypes.c_uint16)

video_refresh_cb_t = ctypes.CFUNCTYPE(None, pixel_p, ctypes.c_uint,
		ctypes.c_uint)

audio_sample_cb_t = ctypes.CFUNCTYPE(None, ctypes.c_uint16, ctypes.c_uint16)

input_poll_cb_t = ctypes.CFUNCTYPE(None)

input_state_cb_t = ctypes.CFUNCTYPE(ctypes.c_int16, ctypes.c_bool,
		ctypes.c_uint, ctypes.c_uint, ctypes.c_uint)

# Load the libsnes library.
libsnes = ctypes.cdll.LoadLibrary("libsnes.so")

# Check the libsnes version matches the API we're defining here.
library_revision_major = libsnes.snes_library_revision_major
library_revision_major.restype = ctypes.c_uint
library_revision_major.argtypes = []
library_revision_minor = libsnes.snes_library_revision_minor
library_revision_minor.restype = ctypes.c_uint
library_revision_minor.argtypes = []

libsnes_api_version = library_revision_major()
if libsnes_api_version != 1:
	raise RuntimeError("Unsupported libsnes version %d.%d" % (
		library_revision_major(), library_revision_minor()))

# Set up prototypes for all the libsnes functions.
set_video_refresh_cb = libsnes.snes_set_video_refresh
set_video_refresh_cb.restype = None
set_video_refresh_cb.argtypes = [video_refresh_cb_t]

set_audio_sample_cb = libsnes.snes_set_audio_sample
set_audio_sample_cb.restype = None
set_audio_sample_cb.argtypes = [audio_sample_cb_t]

set_input_poll_cb = libsnes.snes_set_input_poll
set_input_poll_cb.restype = None
set_input_poll_cb.argtypes = [input_poll_cb_t]

set_input_state_cb = libsnes.snes_set_input_state
set_input_state_cb.restype = None
set_input_state_cb.argtypes = [input_state_cb_t]

set_controller_port_device = libsnes.snes_set_controller_port_device
set_controller_port_device.restype = None
set_controller_port_device.argtypes = [ctypes.c_bool, ctypes.c_uint]

power = libsnes.snes_power
power.restype = None
power.argtypes = []

reset = libsnes.snes_reset
reset.restype = None
reset.argtypes = []

run = libsnes.snes_run
run.restype = None
run.argtypes = []

serialize_size = libsnes.snes_serialize_size
serialize_size.restype = ctypes.c_uint
serialize_size.argtypes = []

serialize = libsnes.snes_serialize
serialize.restype = ctypes.c_bool
serialize.argtypes = [data_p, ctypes.c_uint]

unserialize = libsnes.snes_unserialize
unserialize.restype = ctypes.c_bool
unserialize.argtypes = [data_p, ctypes.c_uint]

cheat_reset = libsnes.snes_cheat_reset
cheat_reset.restype = None
cheat_reset.argtypes = []

cheat_set = libsnes.snes_cheat_set
cheat_set.restype = None
cheat_set.argtypes = [ctypes.c_uint, ctypes.c_bool, ctypes.c_char_p]

load_cartridge_normal = libsnes.snes_load_cartridge_normal
load_cartridge_normal.restype = None
load_cartridge_normal.argtypes = [ctypes.c_char_p, data_p, ctypes.c_uint]

load_cartridge_bsx_slotted = libsnes.snes_load_cartridge_bsx_slotted
load_cartridge_bsx_slotted.restype = None
load_cartridge_bsx_slotted.argtypes = [
		ctypes.c_char_p, data_p, ctypes.c_uint,
		ctypes.c_char_p, data_p, ctypes.c_uint,
	]

load_cartridge_bsx = libsnes.snes_load_cartridge_bsx
load_cartridge_bsx.restype = None
load_cartridge_bsx.argtypes = [
		ctypes.c_char_p, data_p, ctypes.c_uint,
		ctypes.c_char_p, data_p, ctypes.c_uint,
	]

load_cartridge_sufami_turbo = libsnes.snes_load_cartridge_sufami_turbo
load_cartridge_sufami_turbo.restype = None
load_cartridge_sufami_turbo.argtypes = [
		ctypes.c_char_p, data_p, ctypes.c_uint,
		ctypes.c_char_p, data_p, ctypes.c_uint,
		ctypes.c_char_p, data_p, ctypes.c_uint,
	]

load_cartridge_super_game_boy = libsnes.snes_load_cartridge_super_game_boy
load_cartridge_super_game_boy.restype = None
load_cartridge_super_game_boy.argtypes = [
		ctypes.c_char_p, data_p, ctypes.c_uint,
		ctypes.c_char_p, data_p, ctypes.c_uint,
	]

unload = libsnes.snes_unload_cartridge
unload.restype = None
unload.argtypes = []

get_region = libsnes.snes_get_region
get_region.restype = ctypes.c_bool
get_region.argtypes = []

get_memory_data = libsnes.snes_get_memory_data
get_memory_data.restype = data_p
get_memory_data.argtypes = [ctypes.c_uint]

get_memory_size = libsnes.snes_get_memory_size
get_memory_size.restype = ctypes.c_uint
get_memory_size.argtypes = [ctypes.c_uint]

# The init method must only be called once, so we'll call it here but not
# export it from this module.
libsnes.snes_init.restype = None
libsnes.snes_init.argtypes = []
libsnes.snes_init()

# The term method must only be called once, so we'll call it when Python
# exits and not export it from this module.
libsnes.snes_term.restype = None
libsnes.snes_term.argtypes = []
atexit.register(libsnes.snes_term)

# It's sometimes useful to reset libsnes, so we'll export a function that does
# both.
def libsnes_reset():
	libsnes.snes_term()
	libsnes.snes_init()
