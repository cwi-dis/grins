topdir = ../python
blddir = ../python/build.sgi

MODS = mm nullchannel soundchannel moviechannel
OBJS = config.o \
	mmmodule.o \
	moviechannelmodule.o \
	mpegchannelmodule.o \
	nullchannelmodule.o \
	soundchannelmodule.o

INCLS = -I$(blddir) -I$(topdir)/Include
DEFS = -DHAVE_CONFIG_H -DUSE_GL -DUSE_CL -DMM_DEBUG
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
MODLIBS = $(STDWIN)/Build/$(ARCH)/x11/lib/lib.a -lX11_s $(GMP)/libgmp.a -laudio -lcdaudio -lds -lcl -lfm_s -lgl_s -lgl_s -limage -lgutil -lm -lsvideo -lXext -lX11_s $(FORMS)/libforms.a
LIBS = -L/ufs/guido/src/python/readline -lreadline -ltermcap -lmpc -lsun
LIBM = -lm
LIBC = 
SYSLIBS = $(LIBM) $(LIBC)

all: python

python: $(OBJS)
	$(CC) $(OBJS) $(MYLIBS) $(MODLIBS) $(LIBS) $(SYSLIBS) -o python

clean:
	-rm -f *.o
