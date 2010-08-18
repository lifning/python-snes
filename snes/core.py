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
	3. Call get_refresh_rate() to determine the intended refresh rate of the
	   loaded cartridge.
	4. Call run() to cause emulation to occur. Process the output and supply
	   input as the registered callbacks are called. For real-time playback,
	   call run() at the refresh rate returned by get_refresh_rate().
	5. Call unload() to free the resources associated with the loaded
	   cartridge, and return the contents of the cartridge's non-volatile
	   storage for use with the next session.
	6. If you want to switch to a different cartridge, call a load_cartridge_*
	   method again, and go to step 3.

Constants defined in this module:

	MEMORY_* constants represent the diffent types of non-volatile storage
	a SNES cartridge can use. Not every cartridge uses every kind of storage,
	some cartridges use no storage at all. These constants are useful for
	indexing into the list returned from unload().

	VALID_MEMORY_TYPES is a list of all the valid memory type constants.

	PORT_1 and PORT_2 constants represent the different ports to which
	controllers can be connected on the SNES. These should be passed to
	set_controller_port_device() and will be given to the callback passed to
	set_input_state_cb().

	DEVICE_* (but not DEVICE_ID_*) constants represent the different kinds of
	controllers that can be connected to a port. These should be passed to
	set_controller_port_device() and will be given to the callback passed to
	set_input_state_cb().

	DEVICE_ID_* constants represent the button and axis inputs on various
	controllers. They will be given to the callback passed to
	set_input_state_cb().
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

# This keeps track of whether a cartridge is loaded.
_cart_loaded = False

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
	mem_size = W.get_memory_size(mem_type)
	mem_data = W.get_memory_data(mem_type)

	if len(data) != mem_size:
		raise SNESException("This cartridge requires %d bytes of memory type "
				"%d, not %d bytes" % (mem_size, mem_type, len(data)))

	ctypes.memmove(mem_data, data, mem_size)

class SNESException(Exception):
	"""
	Something went wrong with libsnes.
	"""

class NoCartridgeLoaded(SNESException):
	"""
	Can't do this without a loaded cartridge.
	"""

class CartridgeAlreadyLoaded(SNESException):
	"""
	Can't do this with a loaded cartridge.
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

	The callback may be called multiple times per frame with the same
	parameters.

	The callback will not be called if the loaded cartridge does not try to
	probe the controllers.

	The callback will not be called for a particular port if DEVICE_NONE is
	connected to it.

	The callback should accept the following parameters:

		"port" is one of the constants PORT_1 or PORT_2, describing which
		controller port is being reported.

		"device" is one of the DEVICE_* constants describing which type of
		device is currently connected to the given port.

		"index" is a number describing which of the devices connected to the
		port is being reported. It's only useful for DEVICE_MULTITAP and
		DEVICE_JUSTIFIERS - for other device types, it's always 0.

		"id" is one of the DEVICE_ID_* constants for the given device,
		describing which button or axis is being reported (for DEVICE_MULTITAP,
		use the DEVICE_ID_JOYPAD_* IDs; for DEVICE_JUSTIFIERS use the
		DEVICE_ID_JUSTIFIER_* IDs.).

	If "id" represents an analogue input (such as DEVICE_ID_MOUSE_X and
	DEVICE_ID_MOUSE_Y), you should return a value between -32768 and 32767. If
	it represents a digital input such as DEVICE_ID_MOUSE_LEFT or
	DEVICE_ID_MOUSE_RIGHT), return 1 if the button is pressed, and 0 otherwise.

	You are responsible for implementing any turbo-fire features, etc.
	"""
	global _input_state_wrapper
	_input_state_wrapper = W.input_state_cb_t(callback)
	W.set_input_state_cb(_input_state_wrapper)

def set_controller_port_device(port, device):
	"""
	Connects the given device to the given controller port.

	Connecting a device to a port implicitly removes any device previously
	connected to that port. To remove a device without connecting a new one,
	pass DEVICE_NONE as the device parameter. From this point onward, the
	callback passed to set_input_state_cb() will be called with the appropriate
	device, index and id parameters.

	Whenever you call a load_cartridge_* function a DEVICE_JOYPAD will be
	connected to both ports, and devices previously connected using this
	function will be disconnected.

	It's generally safe (that is, it won't crash or segfault) to call this
	function any time, but for sensible operation, don't call it from inside
	the registered input state callback.

	"port" must be either the PORT_1 or PORT_2 constants, describing which port
	the given controller will be connected to. If "port" is set to "PORT_1",
	the "device" parameter should not be DEVICE_SUPER_SCOPE, DEVICE_JUSTIFIER
	or DEVICE_JUSTIFIERS.

	"device" must be one of the DEVICE_* (but not DEVICE_ID_*) constants,
	describing what kind of device will be connected to the given port.
	The devices are:

		- DEVICE_NONE: No device is connected to this port. The registered
		  input state callback will not be called for this port.
		- DEVICE_JOYPAD: A standard SNES gamepad.
		- DEVICE_MULTITAP: A multitap controller, which acts like
		  4 DEVICE_JOYPADs. Your input state callback will be passed "id"
		  parameters between 0 and 3.
		- DEVICE_MOUSE: A SNES mouse controller, as shipped with Mario Paint.
		- DEVICE_SUPER_SCOPE: A Nintendo Super Scope light-gun device (only
		  works properly in port 2).
		- DEVICE_JUSTIFIER: A Konami Justifier light-gun device (only works
		  properly in port 2).
		- DEVICE_JUSTIFIERS: Two Konami Justifier light-gun devices,
		  daisy-chained together (only works properly in port 2). Your input
		  state callback will be passed "id" parameters 0 and 1.
	"""
	W.set_controller_port_device(port, device)

def power():
	"""
	Turn the emulated SNES off and back on.

	Requires that a cartridge be loaded.
	"""
	if _cart_loaded:
		W.power()
	else:
		raise NoCartridgeLoaded("Can't power-cycle before a cartridge is "
				"loaded!")

def reset():
	"""
	Press the front-panel Reset button on the emulated SNES.

	Requires that a cartridge be loaded.
	"""
	if _cart_loaded:
		W.reset()
	else:
		raise NoCartridgeLoaded("Can't reset before a cartridge is loaded!")

def run():
	"""
	Run the emulated SNES for one frame.

	Before this function returns, the registered callbacks will be called at
	least once each.

	This function should be called fifty (for PAL cartridges) or sixty (for
	NTSC cartridges) times per second for real-time emulation.

	Requires that a cartridge be loaded.
	"""
	if _cart_loaded:
		W.run()
	else:
		raise NoCartridgeLoaded("Can't run before a cartridge is loaded!")

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
	global _loaded_cheats
	global _cart_loaded

	if _cart_loaded:
		res = [_memory_to_string(t) for t in VALID_MEMORY_TYPES]
		W.unload()
		_loaded_cheats = {}
		_cart_loaded = False
		return res
	else:
		raise NoCartridgeLoaded("No cartridge loaded.")

def get_refresh_rate():
	"""
	Return the intended refresh-rate of the loaded cartridge.

	Returns either the integer 50 or the integer 60, depending on whether the
	loaded cartridge was designed for a 50Hz region (PAL territories) or a 60Hz
	region (NTSC territories, and Brazil's PAL60).
	"""
	region = W.get_region()
	if region == False:
		# NTSC, or PAL60
		return 60
	else:
		# PAL50
		return 50

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
	blank SRAM region (some cartridges don't use SRAM).

	"rtc" should be a string containing the real-time-clock data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank RTC region (most cartridges don't use an RTC).

	"mapping" should be a string containing an XML document describing the
	required memory-mapping for this cartridge. If not supplied or None,
	a guessed mapping will be used (the guess should be correct for all
	licenced games released in all regions).
	"""
	global _cart_loaded
	if _cart_loaded:
		raise CartridgeAlreadyLoaded("Cartridge already loaded.")

	W.load_cartridge_normal(mapping, ctypes.cast(data, W.data_p), len(data))

	if sram is not None:
		_string_to_memory(sram, MEMORY_CARTRIDGE_RAM)

	if rtc is not None:
		_string_to_memory(rtc, MEMORY_CARTRIDGE_RTC)

	_cart_loaded = True

def load_cartridge_bsx_slotted(base_data, slot_data=None, base_sram=None,
		base_rtc=None,  base_mapping=None, slot_mapping=None):
	"""
	Load a BS-X slotted cartridge into the emulated SNES.

	A "BS-X slotted cartridge" is an ordinary SNES cartridge with a slot in the
	top that accepts the same memory packs that the BS-X cartridge does.

	"base_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the BS-X slotted cartridge.

	"slot_data" should be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the cartridge loaded inside the slotted cartridge's
	slot. If not supplied or None, the slot will be left empty.

	"base_sram" should be a string containing the SRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank SRAM region.

	"base_rtc" should be a string containing the real-time-clock data saved
	from the previous session. If not supplied or None, the cartridge will be
	given a fresh, blank RTC region (most cartridges don't use an RTC).

	"base_mapping" should be a string containing an XML document describing the
	memory-mapping for the BS-X slotted cartridge. If not supplied or None,
	a guessed mapping will be used (the guess should be correct for all
	licenced games released in all regions).

	"slot_mapping" should be a string containing an XML document describing the
	memory-mapping for the cartridge loaded inside the BS-X slotted cartridge.
	If not supplied or None, a guessed mapping will be used (the guess should
	be correct for all licenced games released in all regions).
	"""
	global _cart_loaded
	if _cart_loaded:
		raise CartridgeAlreadyLoaded("Cartridge already loaded.")

	if slot_data is None:
		slot_length = 0
	else:
		slot_length = len(slot_data)

	W.load_cartridge_bsx_slotted(
			base_mapping, ctypes.cast(base_data, W.data_p), len(base_data),
			slot_mapping, ctypes.cast(slot_data, W.data_p), slot_length,
		)

	if base_sram is not None:
		_string_to_memory(base_sram, MEMORY_CARTRIDGE_RAM)

	if base_rtc is not None:
		_string_to_memory(base_rtc, MEMORY_CARTRIDGE_RTC)

	_cart_loaded = True

def load_cartridge_bsx(bios_data, slot_data=None, bios_ram=None,
		bios_pram=None, bios_mapping=None, slot_mapping=None):
	"""
	Load the BS-X base unit cartridge into the emulated SNES.

	The "BS-X base unit cartridge" is the one connected to the BS-X base unit.
	It has a slot which accepts BS-X memory packs.

	"bios_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the BS-X base unit cartridge.

	"slot_data" should be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the cartridge loaded inside the BS-X base
	cartridge's slot. If not supplied or None, the slot will be left empty.

	"bios_ram" should be a string containing the BS-X RAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank RAM region.

	"bios_pram" should be a string containing the BS-X PRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank PRAM region.

	"bios_mapping" should be a string containing an XML document describing the
	memory-mapping for the BS-X base unit cartridge. If not supplied or None,
	a guessed mapping will be used (which is accurate for the offical BS-X base
	unit cartridge).

	"slot_mapping" should be a string containing an XML document describing the
	memory-mapping for the cartridge loaded inside the BS-X base unit
	cartridge. If not supplied or None, a guessed mapping will be used (the
	guess should be correct for all licenced games released in all regions).
	"""
	global _cart_loaded
	if _cart_loaded:
		raise CartridgeAlreadyLoaded("Cartridge already loaded.")

	if slot_data is None:
		slot_length = 0
	else:
		slot_length = len(slot_data)

	W.load_cartridge_bsx(
			bios_mapping, ctypes.cast(bios_data, W.data_p), len(bios_data),
			slot_mapping, ctypes.cast(slot_data, W.data_p), slot_length,
		)

	if bios_ram is not None:
		_string_to_memory(bios_ram, MEMORY_BSX_RAM)

	if bios_pram is not None:
		_string_to_memory(bios_pram, MEMORY_BSX_PRAM)

	_cart_loaded = True

def load_cartridge_sufami_turbo(bios_data, slot_a_data=None, slot_b_data=None,
		slot_a_sram=None, slot_b_sram=None, bios_mapping=None,
		slot_a_mapping=None, slot_b_mapping=None):
	"""
	Load a Sufami Turbo cartridge into the emulated SNES.

	"bios_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the Sufami Turbo cartridge.

	"slot_a_data" should be a string containing the uncompressed,
	de-interleaved, headerless ROM image of the cartridge loaded into the 'A'
	slot of the Sufami Turbo cartridge. This is the actual game that will play.
	If not supplied or left empty, no cartridge will be loaded in this slot.

	"slot_b_data" should be a string containing the uncompressed,
	de-interleaved, headerless ROM image of the cartridge loaded into the 'B'
	slot of the Sufami Turbo cartridge. This game's data will be available to
	the game in slot 'A'. If not supplied or left empty, no cartridge will be
	loaded in this slot.

	"slot_a_sram" should be a string containing the SRAM data saved from the
	previous time the cartridge in slot 'A' was loaded. If not supplied or
	None, the cartridge will be given a fresh, blank SRAM region.

	"slot_b_sram" should be a string containing the SRAM data saved from the
	previous time the cartridge in slot 'B' was loaded. If not supplied or
	None, the cartridge will be given a fresh, blank SRAM region.

	"bios_mapping" should be a string containing an XML document describing the
	memory-mapping for the Sufami Turbo base cartridge. If not supplied or
	None, a guessed mapping will be used (which is correct for the official
	Sufami Turbo cartridge).

	"slot_a_mapping" should be a string containing an XML document describing
	the memory-mapping for the cartridge loaded in slot 'A'.  If not supplied
	or None, a guessed mapping will be used (the guess should be correct for
	all licenced games released in all regions).

	"slot_b_mapping" should be a string containing an XML document describing
	the memory-mapping for the cartridge loaded in slot 'B'.  If not supplied
	or None, a guessed mapping will be used (the guess should be correct for
	all licenced games released in all regions).
	"""
	global _cart_loaded
	if _cart_loaded:
		raise CartridgeAlreadyLoaded("Cartridge already loaded.")

	if slot_a_data is None:
		slot_a_length = 0
	else:
		slot_a_length = len(slot_a_data)

	if slot_b_data is None:
		slot_b_length = 0
	else:
		slot_b_length = len(slot_b_data)

	W.load_cartridge_sufami_turbo(
			bios_mapping, ctypes.cast(bios_data, W.data_p), len(bios_data),
			slot_a_mapping, ctypes.cast(slot_a_data, W.data_p), slot_a_length,
			slot_b_mapping, ctypes.cast(slot_b_data, W.data_p), slot_b_length,
		)

	if slot_a_sram is not None:
		_string_to_memory(slot_a_sram, MEMORY_SUFAMI_TURBO_A_RAM)

	if slot_b_sram is not None:
		_string_to_memory(slot_b_sram, MEMORY_SUFAMI_TURBO_B_RAM)

	_cart_loaded = True

def load_cartridge_super_game_boy(bios_data, dmg_data=None, dmg_sram=None,
		dmg_rtc=None, bios_mapping=None, dmg_mapping=None):
	"""
	Load a Gameboy cartridge in a Super Gameboy into the emulated SNES.

	"bios_data" must be a string containing the uncompressed, de-interleaved,
	headerless ROM image of the Super Gameboy cartridge.

	"dmg_data" should be a string containing the uncompressed, de-interleaved,
	headerless ROM image of a Gameboy cartridge. The emulated Super Gameboy has
	the same compatibility with Gameboy cartridges as the original Super
	Gameboy. If not supplied or None, a null Gameboy cartridge will be
	generated and loaded into the Super Gameboy.

	"dmg_sram" should be a string containing the SRAM data saved from the
	previous session. If not supplied or None, the cartridge will be given
	a fresh, blank SRAM region.

	"dmg_rtc" should be a string containing the real-time-clock data saved from
	the previous session. If not supplied or None, the cartridge will be given
	a fresh, blank RTC region.

	"bios_mapping" should be a string containing an XML document describing the
	memory-mapping for the Super Gameboy cartridge. If not supplied or None,
	a guessed mapping will be used (which is correct for the official Super
	Gameboy cartridge).

	"dmg_mapping" should be a string containing an XML document describing the
	memory-mapping for the Gameboy cartridge. If not supplied or None,
	a guessed mapping will be used (which should be correct for all licenced
	games released in all regions).
	"""
	global _cart_loaded
	if _cart_loaded:
		raise CartridgeAlreadyLoaded("Cartridge already loaded.")

	if dmg_data is None:
		dmg_length = 0
	else:
		dmg_length = len(dmg_data)

	W.load_cartridge_super_game_boy(
			bios_mapping, ctypes.cast(bios_data, W.data_p), len(bios_data),
			dmg_mapping, ctypes.cast(dmg_data, W.data_p), dmg_length,
		)

	if dmg_sram is not None:
		_string_to_memory(dmg_sram, MEMORY_GAME_BOY_RAM)

	if dmg_rtc is not None:
		_string_to_memory(dmg_rtc, MEMORY_GAME_BOY_RTC)

	_cart_loaded = True

def libsnes_reset():
	"""
	Unload and reload the libsnes library.

	This is useful if you want to be completely, absolutely sure that no state
	from one emulation session leaks into the next.

	This unloads any loaded cartridge, removes any registered callbacks,
	discards any set cheats, etc.
	"""
	global _cart_loaded
	global _loaded_cheats

	W.libsnes_reset()

	_cart_loaded = False
	_loaded_cheats = {}
