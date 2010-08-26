"""
Python Imaging Library (PIL) output for SNES Video.
"""

from PIL import Image
from snes.util import snes_framebuffer_to_RGB888

def _snes_to_image(data, width, height, hires, interlace, overscan, pitch):
	return Image.fromstring("RGB", (width, height),
			snes_framebuffer_to_RGB888(data, width, height, pitch))

def set_video_refresh_cb(core, callback):
	"""
	Sets the callback that will handle updated video frames.

	Unlike core.EmulatedSNES.set_video_refresh_cb, the callback passed to this
	function should accept only one parameter:
		
		"image" is an instance of PIL.Image containing the frame data.
	"""
	def wrapper(*args):
		callback(_snes_to_image(*args))

	core.set_video_refresh_cb(wrapper)

def image_difference(imageA, imageB):
	"""
	Determine the differences (if any) between two images.

	"imageA" and "imageB" should be PIL Image objects.

	If the images are identical, returns None.

	If the images differ in mode or size, returns a string describing the
	differences.

	If the images differ in pixel data, returns a 1-bit Image with the same
	dimensions as the input images. Where the two source images have different
	pixel values, those pixels are set to "1" in the resulting image while all
	the equal pixels are set to "0".
	"""
	if imageA.mode != imageB.mode:
		return "Images have different modes (%r vs. %r)" % (
				imageA.mode, imageB.mode,
			)

	if imageA.size != imageB.size:
		return "Images have different sizes (%dx%d vs. %dx%d)" % (
				imageA.size[0], imageA.size[1],
				imageB.size[0], imageB.size[1],
			)


	diffFound = False
	diffMap = Image.new("1", imageA.size)

	pixelsA = imageA.load()
	pixelsB = imageB.load()
	pixelsDiff = diffMap.load()
	width, height = imageA.size

	for y in xrange(height):
		for x in xrange(width):
			if pixelsA[x,y] != pixelsB[x,y]:
				diffFound = True
				pixelsDiff[x,y] = 1
			else:
				pixelsDiff[x,y] = 0

	if diffFound:
		return diffMap

	return None
