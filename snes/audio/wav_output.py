"""
WAV output for SNES Audio.
"""

import wave, struct

def set_audio_sample_file(core, filename):
	"""
	Sets the WAV file that will log updated audio levels.

	Unlike core.EmulatedSNES.set_audio_sample_cb, this function takes a
	filename to use, rather than a function.
	"""
	wavfile = wave.open(filename, 'wb')
	wavfile.setnchannels(2)
	wavfile.setsampwidth(2)
	wavfile.setframerate(32000)
	wavstruct = struct.Struct('<HH')
	def wrapper(left, right):
		# buffering?  what's that?
		wavfile.writeframes(wavstruct.pack(left, right))

	core.set_audio_sample_cb(wrapper)
