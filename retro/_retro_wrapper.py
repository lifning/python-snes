"""
A low-level ctypes wrapper for the libretro API.

You probably want to use the Python API in retro.core instead of this.
"""
import ctypes
from retro import exceptions as EX


# structures
class retro_message(ctypes.Structure):
	_fields_ = [
		("msg",    ctypes.c_char_p),
		("frames", ctypes.c_uint),
	]

class retro_system_info(ctypes.Structure):
	_fields_ = [
		("library_name",     ctypes.c_char_p),
		("library_version",  ctypes.c_char_p),
		("valid_extensions", ctypes.c_char_p),
		("need_fullpath",    ctypes.c_bool),
		("block_extract",    ctypes.c_bool),
	]

class retro_game_geometry(ctypes.Structure):
	_fields_ = [
		("base_width",   ctypes.c_uint),
		("base_height",  ctypes.c_uint),
		("max_width",    ctypes.c_uint),
		("max_height",   ctypes.c_uint),
		("aspect_ratio", ctypes.c_float),
	]

class retro_system_timing(ctypes.Structure):
	_fields_ = [
		("fps",         ctypes.c_double),
		("sample_rate", ctypes.c_double),
	]

class retro_system_av_info(ctypes.Structure):
	_fields_ = [
		("geometry", retro_game_geometry),
		("timing",   retro_system_timing),
	]

class retro_variable(ctypes.Structure):
	_fields_ = [
		("key",   ctypes.c_char_p),
		("value", ctypes.c_char_p),
	]

class retro_game_info(ctypes.Structure):
	_fields_ = [
		("path", ctypes.c_char_p),
		("data", ctypes.c_void_p),
		("size", ctypes.c_size_t),
		("meta", ctypes.c_char_p),
	]

retro_message_p        = ctypes.POINTER(retro_message)
retro_system_info_p    = ctypes.POINTER(retro_system_info)
retro_game_geometry_p  = ctypes.POINTER(retro_game_geometry)
retro_system_timing_p  = ctypes.POINTER(retro_system_timing)
retro_system_av_info_p = ctypes.POINTER(retro_system_av_info)
retro_variable_p       = ctypes.POINTER(retro_variable)
retro_game_info_p      = ctypes.POINTER(retro_game_info)

# callbacks
retro_environment_t = ctypes.CFUNCTYPE(ctypes.c_bool,
                                       ctypes.c_uint,   # cmd
									   ctypes.c_void_p) # data
retro_video_refresh_t = ctypes.CFUNCTYPE(None,
                                         ctypes.c_void_p, # data
										 ctypes.c_uint,   # width
										 ctypes.c_uint,   # height
										 ctypes.c_size_t) # pitch
retro_audio_sample_t = ctypes.CFUNCTYPE(None,
                                        ctypes.c_int16, # left
										ctypes.c_int16) # right
retro_audio_sample_batch_t = ctypes.CFUNCTYPE(ctypes.c_size_t,
                                              ctypes.POINTER(ctypes.c_int16), # data
											  ctypes.c_uint16)                # frames
retro_input_poll_t = ctypes.CFUNCTYPE(None)
retro_input_state_t = ctypes.CFUNCTYPE(ctypes.c_int16,
									   ctypes.c_uint, # port
									   ctypes.c_uint, # device
									   ctypes.c_uint, # index
									   ctypes.c_uint) # id

class LowLevelWrapper(object):
	_lib_active = False

	def __init__(self, libname):
		self._libname = libname
		self._lib = ctypes.cdll.LoadLibrary(libname)

		# Check the self._lib version matches the API we're defining here.
		self._lib.retro_api_version.restype = ctypes.c_uint
		self._lib.retro_api_version.argtypes = []

		self.api_version = self._lib.retro_api_version()
		if self.api_version != 1:
			raise EX.LibraryVersionMismatch("Unsupported libretro API version "
					"%d" % (self.api_version,)
				)

		# Set up prototypes for all the self._lib functions.
		self._lib.retro_set_environment.restype = None
		self._lib.retro_set_environment.argtypes = [retro_environment_t]

		self._lib.retro_set_video_refresh.restype = None
		self._lib.retro_set_video_refresh.argtypes = [retro_video_refresh_t]

		self._lib.retro_set_audio_sample.restype = None
		self._lib.retro_set_audio_sample.argtypes = [retro_audio_sample_t]

		self._lib.retro_set_audio_sample_batch.restype = None
		self._lib.retro_set_audio_sample_batch.argtypes = [retro_audio_sample_batch_t]

		self._lib.retro_set_input_poll.restype = None
		self._lib.retro_set_input_poll.argtypes = [retro_input_poll_t]

		self._lib.retro_set_input_state.restype = None
		self._lib.retro_set_input_state.argtypes = [retro_input_state_t]

		self._lib.retro_init.restype = None
		self._lib.retro_init.argtypes = []

		self._lib.retro_deinit.restype = None
		self._lib.retro_deinit.argtypes = []

		self._lib.retro_get_system_info.restype = None
		self._lib.retro_get_system_info.argtypes = [retro_system_info_p]

		self._lib.retro_get_system_av_info.restype = None
		self._lib.retro_get_system_av_info.argtypes = [retro_system_av_info_p]

		self._lib.retro_set_controller_port_device.restype = None
		self._lib.retro_set_controller_port_device.argtypes = [ctypes.c_uint, ctypes.c_uint]

		self._lib.retro_reset.restype = None
		self._lib.retro_reset.argtypes = []

		self._lib.retro_run.restype = None
		self._lib.retro_run.argtypes = []

		self._lib.retro_serialize_size.restype = ctypes.c_size_t
		self._lib.retro_serialize_size.argtypes = []

		self._lib.retro_serialize.restype = ctypes.c_bool
		self._lib.retro_serialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

		self._lib.retro_unserialize.restype = ctypes.c_bool
		self._lib.retro_unserialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

		self._lib.retro_cheat_reset.restype = None
		self._lib.retro_cheat_reset.argtypes = []

		self._lib.retro_cheat_set.restype = None
		self._lib.retro_cheat_set.argtypes = [
				ctypes.c_uint, ctypes.c_bool, ctypes.c_char_p
			]

		self._lib.retro_load_game.restype = ctypes.c_bool
		self._lib.retro_load_game.argtypes = [retro_game_info_p]

		self._lib.retro_load_game_special.restype = ctypes.c_bool
		self._lib.retro_load_game_special.argtypes = [ctypes.c_uint, retro_game_info_p, ctypes.c_size_t]

		self._lib.retro_unload_game.restype = None
		self._lib.retro_unload_game.argtypes = []

		self._lib.retro_get_region.restype = ctypes.c_uint
		self._lib.retro_get_region.argtypes = []

		self._lib.retro_get_memory_data.restype = ctypes.c_void_p
		self._lib.retro_get_memory_data.argtypes = [ctypes.c_uint]

		self._lib.retro_get_memory_size.restype = ctypes.c_size_t
		self._lib.retro_get_memory_size.argtypes = [ctypes.c_uint]

		# Now that we've configured our library, we can start it up.
		self._lib.retro_init()

		self._lib_active = True

	def close(self):
		self._lib.retro_deinit()
		self._lib_active = False

	def __del__(self):
		if self._lib_active:
			self.close()
