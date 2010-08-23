import unittest
import os.path
from tempfile import mkdtemp
from PIL import Image
from snes import core, exceptions as EX
from snes.video.pil_output import image_difference

TEST_PATH = os.path.abspath(os.path.dirname(__file__))
TEST_ROM_PATH = os.path.join(TEST_PATH, "col15", "col15.sfc")

TEST_GOOD_FRAME_PATH = os.path.join(TEST_PATH, "col15", "col15.bmp")
TEST_BAD_FRAME_PATH  = os.path.join(TEST_PATH, "bad.bmp")


class SNESTestCase(unittest.TestCase):

	def setUp(self):
		self.core = self._makeEmulatedSNES()

		if self.core is None:
			raise RuntimeError("Can't find a libsnes implementation!")

	def _makeEmulatedSNES(self, tag=None):
		res = None
		for name in core.guess_library_name(tag):
			try:
				res = core.EmulatedSNES(name)
				break
			except OSError, e:
				# Library not found
				pass

		return res

	def _loadTestCart(self, core=None):
		if core is None:
			core = self.core
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

	def tearDown(self):
		self.core.close()
