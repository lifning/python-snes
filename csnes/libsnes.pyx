#cython: boundscheck=False
#cython: cdivision=True

cdef nogil:
	set_environment_t set_environment

	library_id_t library_id

	library_revision_major_t library_revision_major
	library_revision_minor_t library_revision_minor

	init_t init
	term_t term

	set_controller_port_device_t set_controller_port_device

	power_t      power
	reset_t      reset
	run_t        run
	get_region_t get_region

	serialize_size_t serialize_size
	serialize_t      serialize
	unserialize_t    unserialize

	cheat_reset_t cheat_reset
	cheat_set_t   cheat_set

	load_cartridge_normal_t      load_cartridge_normal
	load_cartridge_bsx_t         load_cartridge_bsx
	load_cartridge_bsx_slotted_t load_cartridge_bsx_slotted

	load_cartridge_sufami_turbo_t   load_cartridge_sufami_turbo
	load_cartridge_super_game_boy_t load_cartridge_super_game_boy

	set_cartridge_basename_t set_cartridge_basename
	unload_cartridge_t       unload_cartridge

	get_memory_data_t get_memory_data
	get_memory_size_t get_memory_size

	set_audio_sample_t  set_audio_sample
	set_video_refresh_t set_video_refresh
	set_input_poll_t    set_input_poll
	set_input_state_t   set_input_state





# audio
cdef Mix_Chunk* snd_chunk = NULL
cdef uint16_t* snd_data16 = NULL
cdef int snd_pos = 0
cdef bool snd_playing = 0

# video
cdef SDL_Surface *vidsurf = NULL
cdef SDL_Surface *bufsurf = NULL

# input
cdef int16_t digipads[2][16]
cdef char* joy_map = NULL
cdef SDL_Joystick* joy_id = NULL




cdef void audio_sample(uint16_t left, uint16_t right):
	global snd_chunk, snd_data16, snd_pos, snd_playing
	if snd_chunk:
		snd_data16[snd_pos  ] = left
		snd_data16[snd_pos+1] = right
		snd_pos = (snd_pos+2) & 0x3FF
		if not snd_pos:
			Mix_Pause(0)
			memcpy(snd_chunk.abuf, snd_data16, 512*2*2)
			if not snd_playing:
				snd_playing = 1
				Mix_PlayChannel(0, snd_chunk, -1)
			Mix_Resume(0)

cdef void video_refresh(uint16_t *data, unsigned width, unsigned height) nogil:
	global vidsurf, bufsurf
	cdef int pitch = 2048 # in bytes for SDL
	if vidsurf:
		if not bufsurf:
			if (height == 448 or height == 478):  pitch = 1024
			bufsurf = SDL_CreateRGBSurfaceFrom(data, width, height, 15, pitch,
			                                   0x7c00, 0x03e0, 0x001f, 0)
		SDL_BlitSurface(bufsurf, NULL, vidsurf, NULL)

cdef void input_poll() nogil:
	global digipads, joy_map, joy_id
	cdef int i, hat
	if joy_map and joy_id:
		SDL_JoystickUpdate()
		hat = SDL_JoystickGetHat(joy_id, 0)
		digipads[0][SNES_DEVICE_ID_JOYPAD_UP]    = 1 if hat & SDL_HAT_UP else 0
		digipads[0][SNES_DEVICE_ID_JOYPAD_DOWN]  = 1 if hat & SDL_HAT_DOWN else 0
		digipads[0][SNES_DEVICE_ID_JOYPAD_LEFT]  = 1 if hat & SDL_HAT_LEFT else 0
		digipads[0][SNES_DEVICE_ID_JOYPAD_RIGHT] = 1 if hat & SDL_HAT_RIGHT else 0
		for i in xrange(4):
			digipads[0][i] = SDL_JoystickGetButton( joy_id, joy_map[i]-0x30 )
		for i in xrange(8,12):
			digipads[0][i] = SDL_JoystickGetButton( joy_id, joy_map[i]-0x30 )

cdef int16_t input_state(bool port, unsigned device, unsigned index, unsigned id) nogil:
	global digipads
	return digipads[port][id]



cdef void* handle = NULL

cpdef load_lib(char *path):
	global handle
	global set_environment, library_id, library_revision_major, library_revision_minor
	global init, term, set_controller_port_device, power, reset, run, get_region
	global serialize_size, serialize, unserialize, cheat_reset, cheat_set
	global load_cartridge_normal, load_cartridge_bsx, load_cartridge_bsx_slotted
	global load_cartridge_sufami_turbo, load_cartridge_super_game_boy
	global set_cartridge_basename, unload_cartridge
	global get_memory_data, get_memory_size
	global set_audio_sample, set_video_refresh, set_input_poll, set_input_state

	handle = dlopen(path, RTLD_LAZY)

	cdef char* err = dlerror()
	if err:
		close_lib()
		return err

	set_environment = <set_environment_t> dlsym(handle, 'snes_set_environment')

	library_id = <library_id_t> dlsym(handle, 'snes_library_id')

	library_revision_major = <library_revision_major_t> dlsym(handle, 'snes_library_revision_major')
	library_revision_minor = <library_revision_minor_t> dlsym(handle, 'snes_library_revision_minor')

	init = <init_t> dlsym(handle, 'snes_init')
	term = <term_t> dlsym(handle, 'snes_term')

	set_controller_port_device = <set_controller_port_device_t> dlsym(handle, 'snes_set_controller_port_device')

	power = <power_t> dlsym(handle, 'snes_power')
	reset = <reset_t> dlsym(handle, 'snes_reset')
	run = <run_t> dlsym(handle, 'snes_run')
	get_region = <get_region_t> dlsym(handle, 'snes_get_region')

	serialize_size = <serialize_size_t> dlsym(handle, 'snes_serialize_size')
	serialize = <serialize_t> dlsym(handle, 'snes_serialize')
	unserialize = <unserialize_t> dlsym(handle, 'snes_unserialize')

	cheat_reset = <cheat_reset_t> dlsym(handle, 'snes_cheat_reset')
	cheat_set = <cheat_set_t> dlsym(handle, 'snes_cheat_set')

	load_cartridge_normal = <load_cartridge_normal_t> dlsym(handle, 'snes_load_cartridge_normal')
	load_cartridge_bsx = <load_cartridge_bsx_t> dlsym(handle, 'snes_load_cartridge_bsx')
	load_cartridge_bsx_slotted = <load_cartridge_bsx_slotted_t> dlsym(handle, 'snes_load_cartridge_bsx_slotted')

	load_cartridge_sufami_turbo = <load_cartridge_sufami_turbo_t> dlsym(handle, 'snes_load_cartridge_sufami_turbo')
	load_cartridge_super_game_boy = <load_cartridge_super_game_boy_t> dlsym(handle, 'snes_load_cartridge_super_game_boy')

	set_cartridge_basename = <set_cartridge_basename_t> dlsym(handle, 'snes_set_cartridge_basename')
	unload_cartridge = <unload_cartridge_t> dlsym(handle, 'snes_unload_cartridge')

	get_memory_data = <get_memory_data_t> dlsym(handle, 'snes_get_memory_data')
	get_memory_size = <get_memory_size_t> dlsym(handle, 'snes_get_memory_size')

	set_audio_sample = <set_audio_sample_t> dlsym(handle, 'snes_set_audio_sample')
	set_video_refresh = <set_video_refresh_t> dlsym(handle, 'snes_set_video_refresh')
	set_input_poll = <set_input_poll_t> dlsym(handle, 'snes_set_input_poll')
	set_input_state = <set_input_state_t> dlsym(handle, 'snes_set_input_state')

	err = dlerror()
	if err:
		close_lib()
		return err

	init()
	set_audio_sample(&audio_sample)
	set_video_refresh(&video_refresh)
	set_input_poll(&input_poll)
	set_input_state(&input_state)



cpdef close_lib():
	global handle, term, bufsurf
	if term:     term()
	if bufsurf:  SDL_FreeSurface(bufsurf)
	if handle:   dlclose(handle)



cpdef snes_library_id():
	global library_id
	return library_id()

cpdef snes_library_revision():
	global library_revision_major, library_revision_minor
	return (int(library_revision_major()), int(library_revision_minor()))

cpdef load_rom(unsigned char* data, int size):
	global load_cartridge_normal, power
	load_cartridge_normal(NULL, data, size)
	power()

cpdef snes_run():
	global run
	run()



cpdef set_sound(pgsound):
	global snd_chunk, snd_pos, snd_data16
	snd_chunk = PySound_AsChunk(pgsound)
	snd_pos = 0
	snd_data16 = <uint16_t*>malloc(512*2*2) # stereo 16bit
	#<uint16_t*>(snd_chunk.abuf)



cpdef set_surface(pgsurf):
	global vidsurf
	vidsurf = PySurface_AsSurface(pgsurf)



cpdef set_joymap(char *jmap, int index = 0):
	global joy_map, joy_id
	joy_map = jmap
	SDL_Init(SDL_INIT_JOYSTICK)
	joy_id = SDL_JoystickOpen(index)
	print SDL_GetError()

cpdef pad_down(int button, bool port=0, int val = 1):
	global digipads
	digipads[port][button] = val

cpdef pad_up(int button, bool port=0):
	global digipads
	digipads[port][button] = 0

cpdef pad_state(int16_t val, bool port=0):
	global digipads
	cdef int button
	for button in xrange(12):
		digipads[port][button] = 0
		if val & (1<<button):  digipads[port][button] = 1



cdef extern from 'stdio.h':
	int snprintf(char *str, size_t size, char *format, ...)

# don't use, not worth it:
cpdef run_forever():
	global run, vidsurf
	cdef char fps[5]
	cdef int frames = 0
	fps[4] = 0
	while True:
		run()
		SDL_Flip(vidsurf)
		frames += 1000
		snprintf(fps, 4, "%d", frames/SDL_GetTicks() )
		SDL_WM_SetCaption(fps, NULL)

