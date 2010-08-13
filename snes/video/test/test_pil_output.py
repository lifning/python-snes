#!/usr/bin/python
import unittest
import os.path
from PIL import Image
from snes import core
from snes.test import util
from snes.video import pil_output

TEST_PATH = os.path.abspath(os.path.dirname(__file__))


class TestPILOutput(util.SNESTestCase):

	def test_snes_to_image(self):
		"""
		_snes_to_image correctly converts a SNES frame to a PIL.Image
		"""
		snes_frame = [
				0x7C00, 0x03E0, # Red  Green
				0x001F, 0x0000, # Blue Black
			]

		image = pil_output._snes_to_image(snes_frame, 2, 2, False, False,
				False, 2)

		self.assertEqual(image.mode, "RGB")
		self.assertEqual(image.size, (2,2))
		self.assertEqual(list(image.getdata()), [
				(255, 0, 0), (0, 255, 0),
				(0, 0, 255), (0, 0, 0),
			])

	def test_video_refresh_callback(self):
		"""
		set_video_refresh_cb delivers SNES frames via PIL
		"""
		# Load a test cart and run it for a second so we can look at something
		# other than a black screen.
		self._loadTestCart()
		for _ in xrange(core.get_refresh_rate()):
			core.run()

		result = []
		def video_refresh(image):
			# Because we can't raise exceptions from inside this callback, our
			# test assertions are useless here. Let's stash the result
			# somewhere so we can examine it after the callbacks return.
			result.append(image)

		pil_output.set_video_refresh_cb(video_refresh)

		# Crank the handle one more time so we get our video frame.
		core.run()

		self.assertEqual(len(result), 1)
		actual = result[0]
		self.assertEqual(actual.mode, "RGB")
		self.assertEqual(actual.size, (256,224))

		expected = Image.open(os.path.join(TEST_PATH, "col15.bmp"))

		self.assertImagesEqual(actual, expected)


class TestImageComparison(unittest.TestCase):

	def _make_test_image(self, width=2, height=2):
		# Create a new image
		res = Image.new("RGB", (width, height))

		# Put our pretty-coloured test pattern in there.
		pixels = res.load()
		pixels[0,0] = (255, 0, 0)
		pixels[1,0] = (0, 255, 0)
		pixels[0,1] = (0, 0, 255)

		return res

	def test_identical_images(self):
		"""
		Identical images compare equal.
		"""
		imageA = self._make_test_image()
		imageB = self._make_test_image()

		self.assertEqual(
				pil_output.image_difference(imageA, imageB),
				None,
			)

	def test_different_modes(self):
		"""
		Images with different modes are detected as different.
		"""
		imageA = self._make_test_image()
		imageB = self._make_test_image().convert("RGBX")

		self.assertEqual(
				pil_output.image_difference(imageA, imageB),
				"Images have different modes ('RGB' vs. 'RGBX')",
			)

	def test_different_sizes(self):
		"""
		Images with different sizes are detected as different.
		"""
		imageA = self._make_test_image()
		imageB = self._make_test_image(width=3)

		self.assertEqual(
				pil_output.image_difference(imageA, imageB),
				"Images have different sizes (2x2 vs. 3x2)",
			)

	def test_different_image_content(self):
		"""
		Images with different content are detected as different.
		"""
		imageA = self._make_test_image()
		imageB = self._make_test_image()

		# Change the green pixel to a yellow one.
		imageB.putpixel((1,0), (255, 255, 0))

		result = pil_output.image_difference(imageA, imageB)

		# We should get back an image mapping the differences.
		self.assertTrue(isinstance(result, Image.Image))
		self.assertEqual(result.mode, "1")
		self.assertEqual(result.size, imageA.size)
		self.assertEqual(list(result.getdata()), [
				# The difference map should use a white pixel to mark each
				# difference, and black everywhere else.
				0, 1,
				0, 0,
			])


if __name__ == "__main__":
	unittest.main()
