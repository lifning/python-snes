"""
BSV file reading for SNES Input.
"""

from struct import unpack, Struct

# only supports reading at the moment.
class BSVFile:
	def __init__(self, path, verbose=False):
		buf = open(path, 'rb').read()

		magic = buf[3::-1]  # curse you endianness!
		if magic != 'BSV1': raise Exception('invalid BSV magic number: ' + magic)

		(serializerVersion, cartCRC, stateSize) = unpack('<III', buf[4:16])

		buf = buf[16:]
		self.save = buf[:stateSize]
		self.ctrlbuf = buf[stateSize:]

		self.ctrlstruct = Struct('<H')
		self.ctrlindex = 0

		if verbose:
			print magic, 'file loaded:'
			print '  serializerVersion =', serializerVersion
			print '  cartCRC           =', cartCRC
			print '  stateSize         =', stateSize

	def next_input(self):
		ret = 0
		if self.ctrlindex < len(self.ctrlbuf):
			s = self.ctrlstruct
			ret = s.unpack_from(self.ctrlbuf, self.ctrlindex)[0]
			self.ctrlindex += 2
		return ret

def set_input_state_file(core, filename, restore=True):
	"""
	Sets the BSV file containing the log of input states.
	!!! Also restores the savestate contained in the file !!!
	!!! unless the argument 'restore' is set to False.    !!!

	Unlike core.EmulatedSNES.set_input_state_cb, this function takes a
	filename to use, rather than a function.
	"""

	bsv = BSVFile(filename)
	def wrapper(port, device, index, id):
		return bsv.next_input()

	if restore:
		core.unserialize(bsv.save)

	core.set_input_state_cb(wrapper)
