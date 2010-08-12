"""
Common functions useful with libsnes.
"""

def _decode_pixel(pixel):
	"""
	Decode a SNES pixel into an (r,g,b,x) tuple.
	"""
	r = (pixel & 0x7c00) >> 7
	g = (pixel & 0x03e0) >> 2
	b = (pixel & 0x001f) << 3

	return "%c%c%c%c" % (
			(r | (r >> 5)),
			(g | (g >> 5)),
			(b | (b >> 5)),
			0,
		)

rgb_lookup = [_decode_pixel(p) for p in xrange(32768)]

def snes_framebuffer_to_RGBX8888(data, width, height, pitch):
	"""
	Quick and hacky way to convert libsnes video data to RGBX8888 data.

	Despite the word 'quick', it's actually incredibly slow. Python is not the
	best language to use for bitbanging, it seems.
	"""
	res = ''.join(
			rgb_lookup[data[pitch * y + x]]
			for y in xrange(height)
			for x in xrange(width)
		)

	return res

