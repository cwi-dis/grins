topdir = ../python
blddir = ../python/build.sgi

# comment or uncomment the following always in pairs
# uncomment at least one of USE_GL/LIB_GL and USE_XM/LIB_XM (both is allowed)
# USE_CL/LIB_CL is independent of the other two
USE_GL = -DUSE_GL
LIB_GL = -lfm_s -lgl_s

# USE_XM = -DUSE_XM
# LIB_XM = -lXm_s -lPW

USE_CL = -DUSE_CL
LIB_CL = -lcl

MODS = mm nullchannel soundchannel moviechannel
OBJS = config.o \
	mmmodule.o \
	moviechannelmodule.o \
	mpegchannelmodule.o \
	nullchannelmodule.o \
	soundchannelmodule.o

INCLS = -I$(blddir) -I$(topdir)/Include
DEFS = -DHAVE_CONFIG_H $(USE_CL) $(USE_GL) $(USE_XM) -DMM_DEBUG
CFLAGS = $(INCLS) $(USES) $(DEFS)

MYLIBS = \
	$(blddir)/Modules/libModules.a \
	$(blddir)/Python/libPython.a \
	$(blddir)/Objects/libObjects.a \
	$(blddir)/Parser/libParser.a
STDWIN = /ufs/guido/src/stdwin
ARCH = sgi
GMP = /ufs/guido/src/gmp
FORMS = /ufs/guido/src/forms/FORMS
MODLIBS = $(STDWIN)/Build/$(ARCH)/x11/lib/lib.a -lX11_s $(GMP)/libgmp.a -laudio -lcdaudio -lds $(LIB_CL) -lmpc $(LIB_GL) $(LIB_XM) -limage -lgutil -lm -lsvideo -lXext -lX11_s $(FORMS)/libforms.a
LIBS = -L/ufs/guido/src/python/readline -lreadline -ltermcap -lsun
LIBM = -lm
LIBC = 
SYSLIBS = $(LIBM) $(LIBC)

all: python

python: $(OBJS)
	$(CC) $(OBJS) $(MYLIBS) $(MODLIBS) $(LIBS) $(SYSLIBS) -o python

clean:
	-rm -f *.o
