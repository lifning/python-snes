"""
Python Imaging Library (PIL) output for SNES Video.


"""
from PIL import Image
from snes import core

def _decode_pixel(pixel):
	r = (pixel & 0x001f) << 3
	g = (pixel & 0x03e0) >> 2
	b = (pixel & 0x7c00) >> 7

	return (
			r | (r >> 5),
			g | (g >> 5),
			b | (b >> 5),
		)

rgb_lookup = [_decode_pixel(p) for p in xrange(32768)]

def _snes_to_image(data, width, height, hires, interlace, overscan, pitch):
	res = Image.new("RGB", (width, height))

	res.putdata([
			rgb_lookup[data[pitch * y + x]]
			for y in xrange(height)
			for x in xrange(width)
		])

	return res

def set_video_refresh_cb(callback):
	"""
	Sets the callback that will handle updated video frames.

	Unlike snes.core.set_video_refresh_cb, the callback passed to this function
	should accept only one parameter:
		
		"image" is an instance of PIL.Image containing the frame data.
	"""
	def wrapper(*args):
		callback(_snes_to_image(*args))

	core.set_video_refresh_cb(wrapper)
