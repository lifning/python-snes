import unittest
import os.path
from snes import core

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
