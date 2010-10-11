#!/usr/bin/python
import unittest
from snes.video import scaling

class TestScaleMax(unittest.TestCase):

	def test_scale_up(self):
		imageW, imageH = scaling.scale_max(
				1000, 800, 256, 224)
		self.assertEqual(imageW, 1000)
		self.assertEqual(imageH, 800)

		imageW, imageH = scaling.scale_max(
				800, 1000, 256, 224)
		self.assertEqual(imageW, 800)
		self.assertEqual(imageH, 1000)

	def test_scale_down(self):
		imageW, imageH = scaling.scale_max(
				10, 10, 256, 224)
		self.assertEqual(imageW, 10)
		self.assertEqual(imageH, 10)

	def test_integer_scale_up(self):
		imageW, imageH = scaling.scale_max(
				800, 800, 256, 224, True)
		self.assertEqual(imageW, 768) # 256 * 3
		self.assertEqual(imageH, 672) # 224 * 3

		imageW, imageH = scaling.scale_max(
				800, 600, 256, 224, True)
		self.assertEqual(imageW, 768) # 256 * 3
		self.assertEqual(imageH, 448) # 224 * 2

	def test_integer_scale_down(self):
		"""
		If a window dimension is smaller than the image, ignore "integerOnly".
		"""
		imageW, imageH = scaling.scale_max(
				800, 150, 256, 224, True)
		self.assertEqual(imageW, 768)
		self.assertEqual(imageH, 150)

		imageW, imageH = scaling.scale_max(
				150, 800, 256, 224, True)
		self.assertEqual(imageW, 150)
		self.assertEqual(imageH, 672)

		imageW, imageH = scaling.scale_max(
				150, 150, 256, 224, True)
		self.assertEqual(imageW, 150)
		self.assertEqual(imageW, 150)

class TestScaleRaw(unittest.TestCase):

	def test_scale_up(self):
		imageW, imageH = scaling.scale_raw(
				800, 1000, 256, 224)
		self.assertEqual(imageW, 800)
		self.assertEqual(imageH, 700)

		imageW, imageH = scaling.scale_raw(
				1000, 800, 256, 224)
		self.assertEqual(imageW, 853)
		self.assertEqual(imageH, 746)

	def test_scale_down(self):
		imageW, imageH = scaling.scale_raw(
				200, 300, 256, 224)
		self.assertEqual(imageW, 200)
		self.assertEqual(imageH, 175)

		imageW, imageH = scaling.scale_raw(
				300, 200, 256, 224)
		self.assertEqual(imageW, 213)
		self.assertEqual(imageH, 186)

	def test_integer_scale_up(self):
		imageW, imageH = scaling.scale_raw(
				700, 1000, 256, 224, True)
		self.assertEqual(imageW, 512)
		self.assertEqual(imageH, 448)

		# 700px vertically is enough to display 3x224 = 672, but not enough to
		# display 3x240 = 720. Therefore we pick the smaller multiplier, so
		# that no matter what video mode the SNES is in, we won't have to
		# suddenly jump to a smaller multiplier.
		imageW, imageH = scaling.scale_raw(
				1000, 700, 256, 224, True)
		self.assertEqual(imageW, 512)
		self.assertEqual(imageH, 448)

	def test_integer_scale_down(self):
		"""
		If a window dimension is smaller than the image, ignore "integerOnly".
		"""
		imageW, imageH = scaling.scale_raw(
				200, 300, 256, 224, True)
		self.assertEqual(imageW, 200)
		self.assertEqual(imageH, 175)

		imageW, imageH = scaling.scale_raw(
				300, 200, 256, 224, True)
		self.assertEqual(imageW, 213)
		self.assertEqual(imageH, 186)




if __name__ == "__main__":
	unittest.main()
