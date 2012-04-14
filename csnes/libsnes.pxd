
from pygame cimport *
import pygame

from libcpp cimport bool

cimport numpy

ctypedef short int16_t
ctypedef unsigned char uint8_t
ctypedef unsigned short uint16_t

cdef extern from 'dlfcn.h':
	void *dlopen(char *filename, int flag)
	char *dlerror()
	void *dlsym(void *handle, char *symbol)
	int dlclose(void *handle)

	unsigned RTLD_LAZY
	unsigned RTLD_NOW
	unsigned RTLD_NOLOAD
	unsigned RTLD_DEEPBIND
	unsigned RTLD_GLOBAL
	unsigned RTLD_NODELETE

cdef extern from 'stdlib.h':
	cdef void *malloc(size_t size)

cdef extern from 'string.h':
	cdef void *memcpy(void *dest, void *src, size_t n)

cdef extern from "libsnes.hpp":

	cdef:
		##  Constants           
		enum:
			# These constants represent the two controller ports on the front of the SNES,
			# for use with the snes_set_controller_port_device() function and the
			# snes_input_state_t callback.
			SNES_PORT_1  =0
			SNES_PORT_2  =1

		enum:
			# These constants represent the different kinds of controllers that can be
			# connected to a controller port, for use with the
			# snes_set_controller_port_device() function and the snes_input_state_t
			# callback.
			SNES_DEVICE_NONE         =0
			SNES_DEVICE_JOYPAD       =1
			SNES_DEVICE_MULTITAP     =2
			SNES_DEVICE_MOUSE        =3
			SNES_DEVICE_SUPER_SCOPE  =4
			SNES_DEVICE_JUSTIFIER    =5
			SNES_DEVICE_JUSTIFIERS   =6
			SNES_DEVICE_SERIAL_CABLE =7

		enum:
			# These constants represent the button and axis inputs on various controllers,
			# for use with the snes_input_state_t callback.
			SNES_DEVICE_ID_JOYPAD_B        =0
			SNES_DEVICE_ID_JOYPAD_Y        =1
			SNES_DEVICE_ID_JOYPAD_SELECT   =2
			SNES_DEVICE_ID_JOYPAD_START    =3
			SNES_DEVICE_ID_JOYPAD_UP       =4
			SNES_DEVICE_ID_JOYPAD_DOWN     =5
			SNES_DEVICE_ID_JOYPAD_LEFT     =6
			SNES_DEVICE_ID_JOYPAD_RIGHT    =7
			SNES_DEVICE_ID_JOYPAD_A        =8
			SNES_DEVICE_ID_JOYPAD_X        =9
			SNES_DEVICE_ID_JOYPAD_L       =10
			SNES_DEVICE_ID_JOYPAD_R       =11

			SNES_DEVICE_ID_MOUSE_X      =0
			SNES_DEVICE_ID_MOUSE_Y      =1
			SNES_DEVICE_ID_MOUSE_LEFT   =2
			SNES_DEVICE_ID_MOUSE_RIGHT  =3

			SNES_DEVICE_ID_SUPER_SCOPE_X        =0
			SNES_DEVICE_ID_SUPER_SCOPE_Y        =1
			SNES_DEVICE_ID_SUPER_SCOPE_TRIGGER  =2
			SNES_DEVICE_ID_SUPER_SCOPE_CURSOR   =3
			SNES_DEVICE_ID_SUPER_SCOPE_TURBO    =4
			SNES_DEVICE_ID_SUPER_SCOPE_PAUSE    =5

			SNES_DEVICE_ID_JUSTIFIER_X        =0
			SNES_DEVICE_ID_JUSTIFIER_Y        =1
			SNES_DEVICE_ID_JUSTIFIER_TRIGGER  =2
			SNES_DEVICE_ID_JUSTIFIER_START    =3

		enum:
			# These constants will be returned by snes_get_region(), representing the
			# region of the last loaded cartridge.
			SNES_REGION_NTSC  =0
			SNES_REGION_PAL   =1

		enum:
			# These constants represent the kinds of non-volatile memory a SNES cartridge
			# might have, for use with the snes_get_memory_* functions.
			SNES_MEMORY_CARTRIDGE_RAM       =0
			SNES_MEMORY_CARTRIDGE_RTC       =1
			SNES_MEMORY_BSX_RAM             =2
			SNES_MEMORY_BSX_PRAM            =3
			SNES_MEMORY_SUFAMI_TURBO_A_RAM  =4
			SNES_MEMORY_SUFAMI_TURBO_B_RAM  =5
			SNES_MEMORY_GAME_BOY_RAM        =6
			SNES_MEMORY_GAME_BOY_RTC        =7

		enum:
			# These constants represent the various kinds of volatile storage the SNES
			# offers, to allow libsnes clients to implement things like cheat-searching
			# and certain kinds of debugging. They are for use with the snes_get_memory_*
			# functions.
			SNES_MEMORY_WRAM    =100
			SNES_MEMORY_APURAM  =101
			SNES_MEMORY_VRAM    =102
			SNES_MEMORY_OAM     =103
			SNES_MEMORY_CGRAM   =104

		struct geometry:
			unsigned base_width
			unsigned base_height
			unsigned max_width
			unsigned max_height

		struct system_timing:
			double fps
			double sample_rate


ctypedef bool (*environment_t)(unsigned cmd, void *data)
ctypedef void (*set_environment_t)(environment_t)

ctypedef char* (*library_id_t)()

ctypedef unsigned (*library_revision_major_t)()
ctypedef unsigned (*library_revision_minor_t)()

ctypedef void (*init_t)()
ctypedef void (*term_t)()

ctypedef void (*set_controller_port_device_t)(bool port, unsigned device)

ctypedef void (*power_t)()
ctypedef void (*reset_t)()
ctypedef void (*run_t)()
ctypedef bool (*get_region_t)()

ctypedef unsigned (*serialize_size_t)()
ctypedef bool (*serialize_t)(uint8_t *data, unsigned size)
ctypedef bool (*unserialize_t)(uint8_t *data, unsigned size)

ctypedef void (*cheat_reset_t)()
ctypedef void (*cheat_set_t)(unsigned index, bool enabled, char *code)

ctypedef bool (*load_cartridge_normal_t)(
	char *rom_xml, uint8_t *rom_data, unsigned rom_size
)
ctypedef bool (*load_cartridge_bsx_t)(
	char *rom_xml, uint8_t *rom_data, unsigned rom_size,
	char *bsx_xml, uint8_t *bsx_data, unsigned bsx_size
)
ctypedef bool (*load_cartridge_bsx_slotted_t)(
	char *rom_xml, uint8_t *rom_data, unsigned rom_size,
	char *bsx_xml, uint8_t *bsx_data, unsigned bsx_size
)

ctypedef bool (*load_cartridge_sufami_turbo_t)(
	char *rom_xml, uint8_t *rom_data, unsigned rom_size,
	char *sta_xml, uint8_t *sta_data, unsigned sta_size,
	char *stb_xml, uint8_t *stb_data, unsigned stb_size
)
ctypedef bool (*load_cartridge_super_game_boy_t)(
	char *rom_xml, uint8_t *rom_data, unsigned rom_size,
	char *dmg_xml, uint8_t *dmg_data, unsigned dmg_size
)

ctypedef void (*set_cartridge_basename_t)(char *basename)
ctypedef void (*unload_cartridge_t)()

ctypedef uint8_t* (*get_memory_data_t)(unsigned id)
ctypedef unsigned (*get_memory_size_t)(unsigned id)

ctypedef void (*audio_sample_t)(uint16_t left, uint16_t right)
ctypedef void (*video_refresh_t)(uint16_t *data, unsigned width, unsigned height)
ctypedef void (*input_poll_t)()
ctypedef int16_t (*input_state_t)(bool port, unsigned device, unsigned index, unsigned id)

ctypedef void (*set_audio_sample_t)(audio_sample_t cb)
ctypedef void (*set_video_refresh_t)(video_refresh_t cb)
ctypedef void (*set_input_poll_t)(input_poll_t cb)
ctypedef void (*set_input_state_t)(input_state_t cb)

