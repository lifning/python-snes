"""
Python Imaging Library (PIL) output for SNES Video.
"""

from PIL import Image
from snes import core
from snes.util import snes_framebuffer_to_RGB888

def _snes_to_image(data, width, height, hires, interlace, overscan, pitch):
	return Image.fromstring("RGB", (width, height),
			snes_framebuffer_to_RGB888(data, width, height, pitch))

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
