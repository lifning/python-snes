#!/usr/bin/python
import sys, time
import pygame

from retro import core as C
from retro.video.pygame_output import set_video_refresh_cb
from retro.audio.pygame_output import set_audio_sample_cb

framecount = 0.0
start = time.clock()
screen = None

def main():
	core = C.EmulatedSystem('/usr/lib/libretro/libretro-bsnes-compat.so')
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

	set_video_refresh_cb(core, paint_frame)
	set_audio_sample_cb(core)

	pygame.init()

	# run each frame until closed.
	running = True
	while running:
		core.run()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

if __name__ == "__main__": main()
