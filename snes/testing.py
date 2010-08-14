"""
Classes and functions for testing SNES software.
"""
from tempfile import mkdtemp
import os.path
from PIL import Image
from snes import core
from snes.video import pil_output

DEVICE_NAME_TO_ID = {
		"none": core.DEVICE_NONE,
		"joypad": core.DEVICE_JOYPAD,
		"multitap": core.DEVICE_MULTITAP,
		"mouse": core.DEVICE_MOUSE,
		"superscope": core.DEVICE_SUPER_SCOPE,
		"justifier": core.DEVICE_JUSTIFIER,
		"justifiers": core.DEVICE_JUSTIFIERS,
	}


class TestSetupError(Exception):
	pass


class FrameTest(object):

	def __init__(self, expected_video_file=None):
		if expected_video_file is not None:
			self.expected_video = Image.open(expected_video_file)
		else:
			self.expected_video = None

	def _test_video(self, video_frame):
		difference = pil_output.image_difference(video_frame,
				self.expected_video)

		if difference is None:
			return ("video frame", True, "")

		if isinstance(difference, Image.Image):
			# Save the comparators and result so that we can examine them at
			# our leisure.
			outputdir = mkdtemp()
			actual_name = os.path.join(outputdir, "actual.bmp")
			expected_name = os.path.join(outputdir, "expected.bmp")
			difference_name = os.path.join(outputdir, "difference.bmp")

			video_frame.save(actual_name)
			self.expected_video.save(expected_name)
			difference.save(difference_name)

			# Replace the difference image with a message that test runners can
			# display.
			difference = (
					"Image differences found. Actual: %s Expected: %s "
					"Difference: %s" % (
						actual_name, expected_name, difference_name,
					)
				)

		return ("video frame", False, difference)

	def test(self, video_frame):
		"""
		Compare our expected state to that of the emulated SNES.

		Yields a sequence of (testname, result, reason) tuples, where
		"testname" is a string describing the kind of test, "result" is True
		for pass or False for fail, and "reason" is an empty string (if the
		test passed) or a description of the failure (if the test failed).
		"""
		if self.expected_video:
			yield self._test_video(video_frame)

	def count_tests(self):
		"""
		How many tests does this FrameTest perform?
		"""
		count = 0

		if self.expected_video:
			count += 1

		return count


class TestScript(object):

	def __init__(self):
		self.cartridge_loading_info = None
		self.port_1_device = None
		self.port_2_device = None
		self.frametests = {}
		self._max_frame_number = 0

	def test(self):
		"""
		Set up the SNES, run our per-frame tests

		Yields a sequence of (frame#, testname, result, reason) tuples, where
		"frame#" is the frame-count at which the test was done, "testname" is
		a string describing the kind of test, "result" is True for pass or
		False for fail, and "reason" is an empty string (if the test passed) or
		a description of the failure (if the test failed).
		"""
		if self.cartridge_loading_info is None:
			raise TestSetupError("Must load a cartridge before testing")

		if self.port_1_device is None or self.port_2_device is None:
			raise TestSetupError("Must set controllers before testing")

		try:
			core.unload()
		except core.NoCartridgeLoaded:
			pass

		core.set_video_refresh_cb(lambda *args: None)
		core.set_audio_sample_cb(lambda *args: None)
		core.set_input_poll_cb(lambda: None)
		core.set_input_state_cb(lambda *args: 0)

		core.set_controller_port_device(core.PORT_1, self.port_1_device)
		core.set_controller_port_device(core.PORT_2, self.port_2_device)

		# Load the cartridge data as we've been instructed.
		load_func, args, kwargs = self.cartridge_loading_info
		load_func(*args, **kwargs)

		# Because we want to capture the image frame handed to the callback,
		# and because Python doesn't (yet) have a way for nested functions to
		# set to variables in their parent functions, we'll make our callback
		# modify a variable in the outer scope instead.
		video_frame = []
		def video_refresh(image):
			video_frame.append(image)

		for frame_num in range(self._max_frame_number+1):
			if frame_num in self.frametests:
				# Set up the SNES to capture the information we need to test
				# this upcoming frame.
				video_frame = []
				pil_output.set_video_refresh_cb(video_refresh)

			core.run()

			if frame_num in self.frametests:
				# Run the tests for this frame.
				frametest = self.frametests[frame_num]
				for testname, result, reason in frametest.test(video_frame[0]):
					yield (frame_num, testname, result, reason)

				# ...then put things back the way they were.
				core.set_video_refresh_cb(lambda *args: None)

	def count_tests(self):
		"""
		Returns the number of tests in this TestScript.
		"""
		return sum(ft.count_tests() for ft in self.frametests.values())

	def load_cartridge_normal(self, *args, **kwargs):
		"""
		Load the given cartridge in the SNES while this test script runs.

		See core.load_cartridge_normal() for details.
		"""
		self.cartridge_loading_info = (
				core.load_cartridge_normal, args, kwargs)

	def set_controllers(self, port_1_device=None, port_2_device=None):
		"""
		Connect the given controllers to the SNES while this test script runs.
		"""
		if port_1_device is None:
			self.port_1_device = core.DEVICE_NONE
		else:
			self.port_1_device = port_1_device

		if port_2_device is None:
			self.port_2_device = core.DEVICE_NONE
		else:
			self.port_2_device = port_2_device

	def add_frametest(self, frame_num, frametest):
		"""
		Adds a FrameTest to this TestScript at the given frame number.
		"""
		if frame_num in self.frametests:
			raise KeyError(frame_num, "Frame %d already has a test"
					% (frame_num,))

		self._max_frame_number = max(self._max_frame_number, frame_num)

		self.frametests[frame_num] = frametest

