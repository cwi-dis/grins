PYTHON = ../python
BUILD = $(PYTHON)/build.sgi
GSRC = /ufs/guido/src

LIBPYTHON = $(BUILD)/libpython.a
LIBFORMS = $(GSRC)/forms/FORMS/libforms.a
LIBREADLINE = $(GSRC)/readline.sgi/libreadline.a
LIBDL = $(GSRC)/dl/libdl.a

DEFS =	\
	-DPYTHONPATH='"$(PYTHON)/lib"' \
	-DUSE_SELECT \
	-DUSE_MATH \
	-DUSE_TIME \
	-DUSE_POSIX \
	-DUSE_REGEX \
	-DUSE_PWD \
	-DUSE_THREAD \
	-DUSE_MARSHAL \
	-DUSE_RGBIMG \
	-DUSE_STROP \
	-DUSE_IMAGEOP \
	-DUSE_FCNTL \
	-DMM_DEBUG \
	-DUSE_CL \
	-DUSE_XLIB -DUSE_XT -DUSE_XM \
	-DUSE_GL -DUSE_FL -DUSE_FM \
	-DUSE_MALLOC -Dmalloc=xmalloc -Drealloc=xrealloc -Dfree=xfree # -DCOUNT_ALLOCS

CFLAGS = -g -G0 -xansi -D__STDC__ -I$(PYTHON)/src $(DEFS)

LIBS =	$(LIBPYTHON) \
	-lcl \
	$(LIBFORMS) \
	$(LIBREADLINE) \
	-lm -lsun -laudio -lsvideo -lXext -limage -lgutil -lm  \
	$(LIBDL) -lmld -lmpc -lfm_s -lgl_s \
	-lXm_s -lPW -lXmu -lXt_s -lX11_s -ltermcap

LIBDEPS = $(LIBPYTHON) \
	$(LIBFORMS) \
	$(LIBREADLINE) \
	$(LIBDL)

OBJS =	$(BUILD)/pythonmain.o config.o \
	soundchannelmodule.o \
	moviechannelmodule.o \
	mpegchannelmodule.o \
	mmmodule.o

all:	python

python: $(OBJS) $(LIBDEPS)
	cc $(OBJS) $(LIBS) -o python

ldfiles:
	$(GUIDO)/bin/sgi/python -c \
		'import mmmodule, nullchannel, moviechannel, soundchannel, mpegchannel'

clean:
	rm -f *.o core

clobber: clean
	rm -f *.ld python

$(OBJS): mmmodule.h
config.o: Makefile
