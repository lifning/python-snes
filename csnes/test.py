
import numpy
import libsnes

libsnes.load_lib('/usr/lib/libsnes/libsnes-snes9x.so')
print 'libsnes %d.%d' % libsnes.snes_library_revision(), libsnes.snes_library_id()
buf = open('/home/lifning/Hack/Optiness/data/smw.sfc', 'rb').read()
libsnes.load_rom(buf, len(buf))

import pygame

screen = pygame.display.set_mode((256,224))
libsnes.set_surface(screen)
libsnes.set_joymap('0267----1345')

pygame.joystick.init()

pygame.mixer.init( frequency=32040, size=16, channels=2, buffer=512 )
snd = pygame.sndarray.make_sound( numpy.zeros( (512, 2), dtype='uint16', order='C' ) )

libsnes.set_sound(snd)
#snd.play(-1)
clock = pygame.time.Clock()
try:
	while True:
		libsnes.snes_run()
		pygame.display.flip()
		clock.tick(60)
except:
	libsnes.close_lib()

