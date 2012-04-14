SOURCES = libsnes.pyx

all: setup.py $(SOURCES)
	python2 setup.py build_ext --inplace

html: $(SOURCES)
	cython -a --cplus $(SOURCES) -I/usr/include/SDL -I/usr/lib/python2.7/site-packages/numpy/core/include

