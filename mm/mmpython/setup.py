#!/usr/bin/env python

from distutils.core import setup, Extension
import os

cwd = os.getcwd()

setup(name="mmpython",
      version="1.0",
      description="GRiNS Extensions for Python",
      author="Sjoerd Mullender",
      author_email="sjoerd.mullender@oratrix.com",
      maintainer="Sjoerd Mullender",
      maintainer_email="sjoerd.mullender@oratrix.com",
      license="\"Oratrix license\"",
      long_description="""\
The GRiNS Extensions for Python are a set of extensions for running
the GRiNS system.""",
      platforms=["Unix","Linux"],
      ext_modules=[Extension("mm",
                             ["mmmodule.c", "pysema.c"],
                             define_macros=[('MM_DEBUG', None)],
                             ),
                   Extension("moviechannel",
                             ["moviechannelmodule.c"],
                             define_macros=[('MM_DEBUG',None),
                                            ('USE_XM',None),],
                             include_dirs=[os.path.join(cwd,'../../python/Extensions/x-python')]
                             ),
                   Extension("mpegchannel",
                             ["mpegchannelmodule.c"],
                             define_macros=[('MM_DEBUG',None),
                                            ('USE_XM',None),],
                             include_dirs=[os.path.join(cwd,'../../python/Extensions/x-python'),
                                           os.path.join(cwd, '../../lib-src/libmpeg')],
                             libraries=["mpeg","Xm","Xt","X11"],
                             library_dirs=[os.path.join(cwd, '../../lib-src/libmpeg'),
                                           "/usr/X11R6/lib"]
                             ),
                   ])
