"""
PyOpenGL output for SNES video.
"""
from OpenGL.GL import *
from OpenGL.raw.GL import glTexImage2D
import ctypes

def set_video_refresh_cb(core, callback):
	"""
	Sets the callback that will handle updated video frames.

	Unlike core.EmulatedSNES.set_video_refresh_cb, the callback passed to this
	function should accept the following parameters:

		"textureID" is an integer, the OpenGL texture ID of the texture
		containing this frame's video data.

		"frameW" is an integer, the width of this frame's video data in pixels.

		"frameH" is an integer, the height of this frame's video data in
		pixels.

		"textureW" is an integer, the width of the allocated texture in pixels.

		"textureH" is an integer, the height of the allocated texture in
		pixels.
	"""
	# Allocate and configure our texture.
	texture = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, texture)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)

	def wrapper(data, width, height, hires, interlace, overscan, pitch):
		# Load our texture
		glBindTexture(GL_TEXTURE_2D, texture)

		# Copy the frame data from libsnes into a Python string.
		frame_size = (pitch * 2) * height
		frame_buf = ctypes.create_string_buffer(frame_size)
		ctypes.memmove(frame_buf, data, frame_size)

		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, pitch, height, 0, GL_BGRA,
				GL_UNSIGNED_SHORT_1_5_5_5_REV, frame_buf)

		callback(texture, width, height, pitch, height)

	core.set_video_refresh_cb(wrapper)
