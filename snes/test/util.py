import unittest
import os.path
from tempfile import mkdtemp
from PIL import Image
from snes import core
from snes.video.pil_output import image_difference

TEST_ROM_PATH = os.path.join(
		os.path.abspath(os.path.dirname(__file__)),
		"col15", "col15.sfc",
	)


class SNESTestCase(unittest.TestCase):

	def setUp(self):
		# Because libsnes is a singleton, we can't completely destroy and
		# recreate it for each test, but we can certainly reset it.
		try:
			core.unload()
		except core.NoCartridgeLoaded:
			pass

		core.set_video_refresh_cb(lambda *args: None)
		core.set_audio_sample_cb(lambda *args: None)
		core.set_input_poll_cb(lambda: None)
		core.set_input_state_cb(lambda *args: 0)

		# Experimentation shows that libsnes defaults to a joypad in each port,
		# if not configured otherwise.
		core.set_controller_port_device(core.PORT_1, core.DEVICE_JOYPAD)
		core.set_controller_port_device(core.PORT_2, core.DEVICE_JOYPAD)

	def _loadTestCart(self):
		with open(TEST_ROM_PATH, "rb") as handle:
			core.load_cartridge_normal(handle.read())

	def assertImagesEqual(self, actual, expected, message=None):
		"""
		Compare the given images, raise failureException if they differ.
		"""
		difference = image_difference(actual, expected)

		if difference is None:
			# No differences.
			return

		if isinstance(difference, Image.Image):
			# Save the comparators and result so that we can examine them at
			# our leisure.
			outputdir = mkdtemp()
			actual_name = os.path.join(outputdir, "actual.bmp")
			expected_name = os.path.join(outputdir, "expected.bmp")
			difference_name = os.path.join(outputdir, "difference.bmp")

			actual.save(actual_name)
			expected.save(expected_name)
			difference.save(difference_name)

			# Replace the difference image with a message that test runners can
			# display.
			difference = (
					"Image differences found. Actual: %s Expected: %s "
					"Difference: %s" % (
						actual_name, expected_name, difference_name,
					)
				)

		if message:
			raise self.failureException("%s\n%s" % (message, difference))
		else:
			raise self.failureException("%s" % (difference,))
