#!/usr/bin/python
import sys, time
import pygame

from snes import core as C
from snes.audio.pygame_output import set_audio_sample_cb
import pyximport
pyximport.install()
try:
	from snes.video.pygame_output_cy import get_video_refresh_surf
except:
	sys.exit(1)

framecount = 0.0
start = time.clock()
screen = None

def main():
	core = C.EmulatedSNES('/usr/lib/libsnes/libsnes-snes9x.so')
	game_path = sys.argv[1]

	with open(game_path, "rb") as handle:
		core.load_cartridge_normal(handle.read())


	def paint_frame(surf):
		global screen, framecount, start

		if screen is None:
			screen = pygame.display.set_mode(surf.get_size())

		screen.blit(surf, (0,0))
		pygame.display.flip()

		now = time.clock()
		if now > start + 1:
			fps = framecount / (now - start)
			pygame.display.set_caption("FPS: %0.1f\r" % fps)
			framecount = 0
			start = now
		framecount += 1

	snes_screen = get_video_refresh_surf(core)
	set_audio_sample_cb(core)

	pygame.init()

	# run each frame until closed.
	running = True
	while running:
		core.run()
		print 'ran'
		screen.blit(snes_screen, (0,0))
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

if __name__ == "__main__": main()
