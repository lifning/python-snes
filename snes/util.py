"""
Common functions useful with libsnes.
"""
import array

def _decode_pixel(pixel):
	"""
	Decode a SNES pixel into an XRGB8888 integer.
	"""
	r = (pixel & 0x7c00) >> 7
	g = (pixel & 0x03e0) >> 2
	b = (pixel & 0x001f) << 3

	# FIXME: For speed we're using ints to hold XBGR8888 data, assuming that
	# they're 32-bit and little-endian. This is... less than portable.
	return (
			(r | (r >> 5))       |
			(g | (g >> 5)) << 8  |
			(b | (b >> 5)) << 16
		)

rgb_lookup = [_decode_pixel(p) for p in xrange(32768)]

def snes_framebuffer_to_XRGB8888(data, width, height, pitch):
	"""
	Quick and hacky way to convert libsnes video data to XRGB8888 data.

	Despite the word 'quick', it's actually incredibly slow. Python is not the
	best language to use for bitbanging, it seems.

	Returns an array.array() of 32-bit integers, each representing a pixel in
	XRGB8888 format.
	"""
	return array.array('i', [
				rgb_lookup[data[pitch * y + x]]
				for y in xrange(height)
				for x in xrange(width)
			])
