
import pstats, cProfile

import pygame_demo as test

cProfile.runctx("test.main()", globals(), locals(), "Profile.prof")

s = pstats.Stats("Profile.prof")
s.strip_dirs().sort_stats("time").print_stats(0.1)

