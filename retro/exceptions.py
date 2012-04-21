class RetroException(Exception):
	"""
	Something went wrong with libretro.
	"""

class NoGameLoaded(RetroException):
	"""
	Can't do this without a loaded cartridge.
	"""

class GameAlreadyLoaded(RetroException):
	"""
	Can't do this with a loaded cartridge.
	"""

class LibraryInUse(RetroException):
	"""
	The requested library is already being used by something else.
	"""

class LibraryVersionMismatch(RetroException):
	"""
	The library version is one we don't recognise.
	"""
