"""
Calculate the on-screen dimensions of the SNES frame.
"""

# Numbers stolen from bsnes.
NTSC_ASPECT = 54.0 / 47.0
PAL_ASPECT = 32.0 / 23.0

# The SNES also has a 512px hi-res mode, but it does not change the width of
# the image on-screen, so we can do all our calculations for the 256px image.
SNES_WIDTH = 256
SNES_HEIGHT = 240

def scale_max(windowW, windowH, imageW, imageH, integerOnly=False):
	"""
	Scale the image as large as possible, regardless of aspect ratio.
	"""
	if integerOnly and windowW > imageW:
		width = (windowW // imageW) * imageW
	else:
		width = windowW
		
	if integerOnly and windowH > imageH:
		height = (windowH // imageH) * imageH
	else:
		height = windowH

	return width, height

def scale_raw(windowW, windowH, imageW, imageH, integerOnly=False):
	"""
	Scale the image as large possible, maintaining a 1:1 pixel ratio.
	"""
	multiplier = min(
			float(windowW) / SNES_WIDTH,
			float(windowH) / SNES_HEIGHT,
		)

	if integerOnly and (windowW > imageW and windowH > imageH):
		multiplier = int(multiplier)

	return int(imageW * multiplier), int(imageH * multiplier)
