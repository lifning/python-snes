"""
A Pythonic interface to libsnes functionality.

libsnes only allows one emulated SNES per process, therefore the interface to
libsnes is a module rather than a class. The usual use of this module runs
something like this:

	1. Call the set_*_cb methods to set up the callbacks that will be notified
	   when the emulated snes has produced a video frame, audio sample, or
	   needs controller input.
	2. Call one of the load_cartridge_* methods to give the emulated SNES
	   a cartridge image to run.
	3. Call run() fifty (PAL) or sixty (NTSC) times a second to cause emulation
	   to occur. Process the output and supply input as the registered
	   callbacks are called.
	4. Call unload() to free the resources associated with the loaded
	   cartridge, and return the contents of the cartridge's non-volatile
	   storage for use with the next session.
	5. If you want to switch to a different cartridge, call a load_cartridge_*
	   method again, and go to step 3.

Constants defined in this module:

	MEMORY_* constants represent the diffent types of non-volatile storage
	a SNES cartridge can use. Not every cartridge uses every kind of storage,
	some cartridges use no storage at all. These constants are useful for
	indexing into the list returned from unload().

	VALID_MEMORY_TYPES is a list of all the valid memory type constants.

	PORT_* constants represent the different ports to which controllers can be
	connected on the SNES. These should be passed to
	set_controller_port_device() and will be given to the callback passed to
	set_input_state_cb()

	DEVICE_* (but not DEVICE_ID_*) constants represent the different kinds of
	controllers that can be connected to a port. These should be passed to
	set_controller_port_device() and will be given to the callback passed to
	set_input_state_cb()

	DEVICE_ID_* constants represent the button and axis inputs on various
	controllers. They will be given to the callback passed to
	set_input_state_cb()
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

# Return values for get_region()
NTSC = False
PAL = True

# Unused memory memory types are reported to have this size on Linux/x86_64.
# TODO: Figure out if this is true everywhere.
_MEMORY_SIZE_UNUSED = 2**32 - 1

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

# This keeps track of which cheats the user wants to apply to this game.
_loaded_cheats = {}

def _reload_cheats():
	"""
	Internal method.

	Reloads cheats in the emulated SNES from the _loaded_cheats variable.
	"""
	W.cheat_reset()

	for index, (code, enabled) in _loaded_cheats.items():
		W.cheat_set(index, enabled, code)

def _memory_to_string(mem_type):
	"""
	Internal method.

	Copies data from the given libsnes memory buffer into a new string.
	"""
	mem_size = W.get_memory_size(mem_type)
	mem_data = W.get_memory_data(mem_type)

	if mem_size == 0:
		return None

	buffer = ctypes.create_string_buffer(mem_size)
	ctypes.memmove(buffer, mem_data, mem_size)

	return buffer.raw

def _string_to_memory(data, mem_type):
	"""
	Internal method.

	Copies the given data into the libsnes memory buffer of the given type.
	"""
	mem_size = get_memory_size(mem_type)
	mem_data = get_memory_data(mem_type)

	if len(data) != mem_size:
		raise SNESException("This cartridge requires %d bytes of memory type "
				"%d, not %d bytes" % (mem_size, mem_type, len(data)))

	ctypes.memmove(mem_data, data, mem_size)

class SNESException(Exception):
	"""
	Something went wrong with libsnes.
	"""

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

def set_video_refresh_cb(callback):
	"""
	Sets the callback that will handle updated video frames.

	The callback should accept the following parameters:

		"data" is a pointer to the top-left of a 512*480 array of pixels. Each
		pixel is an unsigned, 16-bit integer in XBGR1555 format.

		"width" is the number of pixels in each row of the frame. It can be
		either 256 (if the SNES is in "low-res" mode) or 512 (if the SNES is in
		"hi-res" or "psuedo-hi-res" modes).

		"height" is the number of pixel-rows in the frame. It can vary between
		224 and 478, depending on whether the SNES has "interlace" and/or
		"overscan" modes enabled.

		"hires" is True if this frame is "hi-res" or "pseudo-hi-res".

		"interlace" is True if this frame has "interlace" mode enabled.

		"overscan" is True if this frame has "overscan" mode enabled.

		"pitch" is the number of pixels from the beginning of one line to the
		beginning of the text. In non-interlaced modes, every other line of the
		frame-buffer is left blank.

	The callback should return nothing.
	"""
	global _video_refresh_wrapper

	def wrapped_callback(data, width, height):
		hires = (width == 512)
		interlace = (height == 448 or height == 478)
		overscan = (height == 239 or height == 478)
		pitch = 512 if interlace else 1024 # in pixels

		callback(data, width, height, hires, interlace, overscan, pitch)

	_video_refresh_wrapper = W.video_refresh_cb_t(wrapped_callback)
	W.set_video_refresh_cb(_video_refresh_wrapper)

def set_audio_sample_cb(callback):
	"""
	Sets the callback that will handle updated audio frames.

	The callback should accept the following parameters:

		"left" is an integer between 0 and 65535 that specifies the volume in
		the left audio channel.

		"right" is an integer between 0 and 65535 that specifies the volume in
		the right audio channel.

	The callback should return nothing.
	"""
	global _audio_sample_wrapper
	_audio_sample_wrapper = W.audio_sample_cb_t(callback)
	W.set_audio_sample_cb(_audio_sample_wrapper)

def set_input_poll_cb(callback):
	"""
	Sets the callback that will check for updated input events.

	The callback should accept no parameters and return nothing. It should just
	read new input events and store them somewhere so they can be returned by
	the input state callback.
	"""
	global _input_poll_wrapper
	_input_poll_wrapper = W.input_poll_cb_t(callback)
	W.set_input_poll_cb(_input_poll_wrapper)

def set_input_state_cb(callback):
	"""
	Sets the callback that reports the current state of input devices.

	The callback should accept the following parameters:

		"port" is one of the constants PORT_1 or PORT_2, describing which
		controller port is being reported.

		"device" is one of the DEVICE_* constants describing which type of
		device is currently connected to the given port.

		"index" is a number describing which of the devices connected to the
		port is being reported. It's probably only useful for DEVICE_MULTITAP
		and DEVICE_JUSTIFIERS (TODO: check this).

		"id" is one of the DEVICE_ID_* constants for the given device,
		describing which button or axis is being reported (for DEVICE_MULTITAP,
		use the DEVICE_ID_JOYPAD_* IDs)

	The callback should return a number between -32768 and 32767 representing
	the value of the button or axis being reported (TODO: what do button inputs
	return?).
	"""
	global _input_state_wrapper
	_input_state_wrapper = W.input_state_cb_t(callback)
	W.set_input_state_cb(_input_state_wrapper)

# Because libsnes crashes if somebody calls "run" without setting up
# callbacks, let's set them to dummy functions by default.
set_video_refresh_cb(lambda *args: None)
set_audio_sample_cb(lambda *args: None)
set_input_poll_cb(lambda: None)
set_input_state_cb(lambda *args: 0)

def set_controller_port_device(port, device):
	"""
	Connects the given device to the given controller port.

	Connecting a device to a port implicitly removes any device previously
	connected to that port. To remove a device without connecting a new one,
	pass DEVICE_NONE as the device parameter. From this point onward, the
	callback passed to set_input_state_cb() will be called with the appropriate
	device, index and id parameters.

	If this function is never called, the default is to have no controllers
	connected at all. (TODO: is this true?)

	"port" must be one of the PORT_* constants, describing which port the given
	controller will be connected to.

	"device" must be one of the DEVICE_* (but not DEVICE_ID_*) constants,
	describing what kind of device will be connected to the given port.

	TODO: Is there any time it's not safe to call this method? For example, is
	it safe to call this method from inside the input state callback?
	"""
	W.set_controller_port_device(port, device)

def power():
	"""
	Turn the emulated SNES off and back on.

	Requires that a cartridge be loaded.
	"""
	W.power()

def reset():
	"""
	Press the front-panel Reset button on the emulated SNES.

	Requires that a cartridge be loaded.
	"""
	W.reset()

def run():
	"""
	Run the emulated SNES for one frame.

	Before this function returns, the registered callbacks will be called at
	least once each.

	This function should be called fifty (for PAL cartridges) or sixty (for
	NTSC cartridges) times per second for real-time emulation.

	Requires that a cartridge be loaded.
	"""
	W.run()

def unload():
	"""
	Remove the cartridge and return its non-volatile storage contents.

	Returns a list with an entry for each MEMORY_* constant in
	VALID_MEMORY_TYPES. If the current cartridge uses that type of storage, the
	corresponding index in the list will be a string containing the storage
	contents, which can later be passed to load_cartridge_*. Otherwise, the
	corresponding index is None.

	Requires that a cartridge be loaded.
	"""
	res = [_memory_to_string(t) for t in VALID_MEMORY_TYPES]
	W.unload()
	return res

def get_region():
	"""
	Determine the intended region of the loaded cartridge.

	Returns one of the constants NTSC or PAL. NTSC means that you should call
	run() 60 times a second for real-time emulation, PAL means that you should
	call run() 50 times a second.
	"""
	return W.get_region()

def serialize():
	"""
	Serializes the state of the emulated SNES to a string.

	This serialized data can be handed to unserialize() at a later time to
	resume emulation from this point.

	Requires that a cartridge be loaded.
	"""
	size = W.serialize_size()
	buffer = ctypes.create_string_buffer(size)
	res = W.serialize(ctypes.cast(buffer, W.data_p), size)
	if not res:
		raise SNESException("problem in serialize")
	return buffer.raw

def unserialize(state):
	"""
	Restores the state of the emulated SNES from a string.

	Note that the cartridge's SRAM data is part of the saved state.

	Requires that the same cartridge that was loaded when serialize was called,
	be loaded before unserialize is called.
	"""
	res = W.unserialize(ctypes.cast(state, W.data_p), len(state))
	if not res:
		raise SNESException("problem in unserialize")

def cheat_add(index, code, enabled=True):
	"""
	Stores the given cheat code at the given index in the cheat list.

	"index" must be an integer. Only one cheat can be stored at any given
	index.

	"code" must be a string containing a valid Game Genie cheat code, or
	a sequence of them separated with plus signs like "DD62-3B1F+DD12-FA2C".

	"enabled" must be a boolean. It determines whether the cheat code is
	enabled or not.
	"""
	_loaded_cheats[index] = (code, enabled)
	_reload_cheats()

def cheat_remove(index):
	"""
	Removes the cheat at the given index from the cheat list.

	"index" must be an integer previously passed to cheat_add.
	"""
	del _loaded_cheats[index]
	_reload_cheats()

def cheat_set_enabled(index, enabled):
	"""
	Enables or disables the cheat at the given index in the cheat list.

	"index" must be an integer previously passed to cheat_add.

	"enabled" must be a boolean. It determines whether the cheat code is
	enabled or not.
	"""
	code, _ = _loaded_cheats[index]
	_loaded_cheats[index] = (code, enabled)
	_reload_cheats()

def cheat_is_enabled(index):
	"""
	Returns true if the cheat at the given index is enabled.

	"index" must be an integer previously passed to cheat_add.
	"""
	_, enabled = _loaded_cheats[index]
	return enabled

def load_cartridge_normal(data, sram=None, rtc=None, mapping=None):
	"""
	Load an ordinary cartridge into the emulated SNES.

	"data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image.

	"sram" should be a string containing the SRAM data saved from the previous
	session. If not supplied or None, the cartridge will be given a fresh,
	blank SRAM region.

	"rtc" should be a string containing the real-time-clock data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank RTC region (most cartridges don't use an RTC).

	"mapping" should be a string containing an XML document describing the
	required memory-mapping for this cartridge. If not supplied or None,
	a guessed mapping will be used (the guess should be correct for all
	licenced games released in all regions).
	"""
	W.load_cartridge_normal(mapping, ctypes.cast(data, W.data_p), len(data))

	if sram is not None:
		_string_to_memory(sram, MEMORY_CARTRIDGE_RAM)

	if rtc is not None:
		_string_to_memory(rtc, MEMORY_CARTRIDGE_RTC)

def load_cartridge_bsx_slotted(base_data, slot_data, base_sram=None,
		base_rtc=None, bsx_ram=None, bsx_pram=None, base_mapping=None,
		slot_mapping=None):
	"""
	Load a BS-X slotted cartridge into the emulated SNES.

	"base_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the BS-X base cartridge.

	"slot_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the cartridge loaded inside the BS-X base
	cartridge.

	"base_sram" should be a string containing the SRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank SRAM region.

	"base_rtc" should be a string containing the real-time-clock data saved
	from the previous session. If not supplied or None, the cartridge will be
	given a fresh, blank RTC region (most cartridges don't use an RTC).

	TODO: Does the BS-X base cart use SRAM and/or RTC storage?

	"bsx_ram" should be a string containing the BS-X RAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank RAM region.

	"bsx_pram" should be a string containing the BS-X PRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank PRAM region.

	"base_mapping" should be a string containing an XML document describing the
	memory-mapping for the BS-X base cartridge. If not supplied or None,
	a guessed mapping will be used (the guess should be correct for all
	licenced games released in all regions).

	"slot_mapping" should be a string containing an XML document describing the
	memory-mapping for the cartridge loaded inside the BS-X base cartridge. If
	not supplied or None, a guessed mapping will be used (the guess should be
	correct for all licenced games released in all regions).
	"""
	W.load_cartridge_bsx_slotted(
			base_mapping, ctypes.cast(base_data, W.data_p), len(base_data),
			slot_mapping, ctypes.cast(slot_data, W.data_p), len(slot_data),
		)

	if base_sram is not None:
		_string_to_memory(base_sram, MEMORY_CARTRIDGE_RAM)

	if base_rtc is not None:
		_string_to_memory(base_rtc, MEMORY_CARTRIDGE_RTC)

	if bsx_ram is not None:
		_string_to_memory(bsx_ram, MEMORY_BSX_RAM)

	if bsx_pram is not None:
		_string_to_memory(bsx_pram, MEMORY_BSX_PRAM)

def load_cartridge_bsx(base_data, slot_data, base_sram=None,
		base_rtc=None, bsx_ram=None, bsx_pram=None, base_mapping=None,
		slot_mapping=None):
	"""
	Load a BS-X slotted cartridge into the emulated SNES.

	"base_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the BS-X base cartridge.

	"slot_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the cartridge loaded inside the BS-X base
	cartridge.

	"base_sram" should be a string containing the SRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank SRAM region.

	"base_rtc" should be a string containing the real-time-clock data saved
	from the previous session. If not supplied or None, the cartridge will be
	given a fresh, blank RTC region (most cartridges don't use an RTC).

	"bsx_ram" should be a string containing the BS-X RAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank RAM region.

	"bsx_pram" should be a string containing the BS-X PRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank PRAM region.

	"base_mapping" should be a string containing an XML document describing the
	memory-mapping for the BS-X base cartridge. If not supplied or None,
	a guessed mapping will be used (the guess should be correct for all
	licenced games released in all regions).

	"slot_mapping" should be a string containing an XML document describing the
	memory-mapping for the cartridge loaded inside the BS-X base cartridge. If
	not supplied or None, a guessed mapping will be used (the guess should be
	correct for all licenced games released in all regions).

	TODO: How on earth is this different from load_cartridge_bsx_slotted?
	"""
	W.load_cartridge_bsx(
			base_mapping, ctypes.cast(base_data, W.data_p), len(base_data),
			slot_mapping, ctypes.cast(slot_data, W.data_p), len(slot_data),
		)

	if base_sram is not None:
		_string_to_memory(base_sram, MEMORY_CARTRIDGE_RAM)

	if base_rtc is not None:
		_string_to_memory(base_rtc, MEMORY_CARTRIDGE_RTC)

	if bsx_ram is not None:
		_string_to_memory(bsx_ram, MEMORY_BSX_RAM)

	if bsx_pram is not None:
		_string_to_memory(bsx_pram, MEMORY_BSX_PRAM)

def load_cartridge_sufami_turbo(base_data, slot_a_data=None, slot_b_data=None,
		base_sram=None, base_rtc=None, slot_a_sram=None, slot_b_sram=None,
		base_mapping=None, slot_a_mapping=None, slot_b_mapping=None):
	"""
	Load a Sufami Turbo cartridge into the emulated SNES.

	"base_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the Sufami Turbo cartridge.

	"slot_a_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the cartridge loaded into the 'A' slot of the
	Sufami Turbo cartridge.

	"slot_b_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the cartridge loaded into the 'B' slot of the
	Sufami Turbo cartridge.

	"base_sram" should be a string containing the SRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank SRAM region.

	"base_rtc" should be a string containing the real-time-clock data saved
	from the previous session. If not supplied or None, the cartridge will be
	given a fresh, blank RTC region (most cartridges don't use an RTC).

	"slot_a_sram" should be a string containing the SRAM data saved from the
	previous time the cartridge in slot 'A' was loaded. If not supplied or
	None, the cartridge will be given a fresh, blank SRAM region.

	"slot_b_sram" should be a string containing the SRAM data saved from the
	previous time the cartridge in slot 'B' was loaded. If not supplied or
	None, the cartridge will be given a fresh, blank SRAM region.

	"base_mapping" should be a string containing an XML document describing the
	memory-mapping for the Sufami Turbo base cartridge. If not supplied or
	None, a guessed mapping will be used (the guess should be correct for all
	licenced games released in all regions).

	"slot_a_mapping" should be a string containing an XML document describing
	the memory-mapping for the cartridge loaded in slot 'A'.  If not supplied
	or None, a guessed mapping will be used (the guess should be correct for
	all licenced games released in all regions).

	"slot_b_mapping" should be a string containing an XML document describing
	the memory-mapping for the cartridge loaded in slot 'B'.  If not supplied
	or None, a guessed mapping will be used (the guess should be correct for
	all licenced games released in all regions).
	"""
	if slot_a_data is None:
		slot_a_length = 0
	else:
		slot_a_length = len(slot_a_data)

	if slot_b_data is None:
		slot_b_length = 0
	else:
		slot_b_length = len(slot_b_data)

	W.load_cartridge_sufami_turbo(
			base_mapping, ctypes.cast(base_data, W.data_p), len(base_data),
			slot_a_mapping, ctypes.cast(slot_a_data, W.data_p), slot_a_length,
			slot_b_mapping, ctypes.cast(slot_b_data, W.data_p), slot_b_length,
		)

	if base_sram is not None:
		_string_to_memory(base_sram, MEMORY_CARTRIDGE_RAM)

	if base_rtc is not None:
		_string_to_memory(base_rtc, MEMORY_CARTRIDGE_RTC)

	if slot_a_sram is not None:
		_string_to_memory(slot_a_sram, MEMORY_SUFAMI_TURBO_A_RAM)

	if slot_b_sram is not None:
		_string_to_memory(slot_b_sram, MEMORY_SUFAMI_TURBO_B_RAM)


# TODO: Other cart loading methods.
