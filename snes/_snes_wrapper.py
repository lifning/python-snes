"""
A CTypes wrapper for the raw libsnes API.
"""
import ctypes, atexit

# Define some ctypes data types the libsnes API uses
data_p = ctypes.POINTER(ctypes.c_ubyte)
pixel_p = ctypes.POINTER(ctypes.c_uint16)

video_refresh_cb_t = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_uint16),
		ctypes.c_uint, ctypes.c_uint)

audio_sample_cb_t = ctypes.CFUNCTYPE(None, ctypes.c_uint16, ctypes.c_uint16)

input_poll_cb_t = ctypes.CFUNCTYPE(None)

input_state_cb_t = ctypes.CFUNCTYPE(ctypes.c_int16, ctypes.c_bool,
		ctypes.c_uint, ctypes.c_uint, ctypes.c_uint)

# At the first import, we haven't loaded any functions.
set_video_refresh = None
set_audio_sample = None
set_input_poll = None
set_input_state = None
unload = None
run = None
set_controller_port_device = None
serialize_size = None
serialize = None
unserialize = None
cheat_reset = None
cheat_set = None
load_cartridge_normal = None

# When we're given a library path, set everything up.
def init(libsnes_path):
	global init, set_video_refresh, set_audio_sample
	global set_input_poll, set_input_state, unload, run
	global set_controller_port_device, serialize_size, serialize
	global cheat_reset, cheat_set, load_cartridge_normal

	libsnes = ctypes.cdll.LoadLibrary(libsnes_path)

	# Check the libsnes version matches the API we're defining here.
	library_revision = libsnes.snes_library_revision
	library_revision.restype = ctypes.c_uint
	library_revision.argtypes = []

	libsnes_version = library_revision()
	if libsnes_version != 1:
		raise RuntimeError("Unsupported libsnes version %r" % libsnes_version)

	# Set up prototypes for all the libsnes functions.
	set_video_refresh = libsnes.snes_set_video_refresh
	set_video_refresh.restype = None
	set_video_refresh.argtypes = [video_refresh_cb_t]

	set_audio_sample = libsnes.snes_set_audio_sample
	set_audio_sample.restype = None
	set_audio_sample.argtypes = [audio_sample_cb_t]

	set_input_poll = libsnes.snes_set_input_poll
	set_input_poll.restype = None
	set_input_poll.argtypes = [input_poll_cb_t]

	set_input_state = libsnes.snes_set_input_state
	set_input_state.restype = None
	set_input_state.argtypes = [input_state_cb_t]

	unload = libsnes.snes_unload
	unload.restype = None
	unload.argtypes = []

	run = libsnes.snes_run
	run.restype = None
	run.argtypes = []

	set_controller_port_device = libsnes.snes_set_controller_port_device
	set_controller_port_device.restype = None
	set_controller_port_device.argtypes = [ctypes.c_bool, ctypes.c_uint]

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

	# TODO: Other cartridge types

	# TODO: retrieving SRAM data

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

	# Now that we've set up this module, clobber this init() method so it can't
	# be called again.
	init = lambda path: None
