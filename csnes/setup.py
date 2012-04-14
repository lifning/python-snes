#!/usr/bin/env python

"""
setup.py  to build code with cython
"""
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy # to get includes

mods = [
	Extension("libsnes", ["libsnes.pyx", "libsnes.pxd"],
		libraries=["dl", "SDL_mixer", "SDL"],
		language='C++',
		#extra_compile_args=['-fopenmp'],
		#extra_link_args=['-fopenmp'],
    )
]

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = mods,
    include_dirs = ['/usr/include/SDL', numpy.get_include()],
)

