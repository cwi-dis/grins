GUIDO =	/ufs/guido
GSRC = $(GUIDO)/src
PYTHON = $(GSRC)/python
BUILD = $(PYTHON)/build.sgi

LIBPYTHON = $(BUILD)/libpython.a
LIBFORMS = $(GSRC)/forms/FORMS/libforms.a
LIBREADLINE = $(GSRC)/readline.sgi/libreadline.a
LIBDL = $(GSRC)/dl/libdl.a

DEFS =	\
	-DUSE_SELECT \
	-DUSE_GL \
	-DUSE_MATH \
	-DUSE_FL \
	-DUSE_TIME \
	-DUSE_POSIX \
	-DUSE_REGEX \
	-DUSE_PWD \
	-DUSE_THREAD \
	-DUSE_MARSHAL \
	-DUSE_CL \
	-DUSE_FM \
	-DUSE_IMGFILE \
	-DUSE_STROP \
	-DUSE_IMAGEOP \
	-DMM_DEBUG \
	-DPYTHONPATH='"$(GUIDO)/lib/python"'

CFLAGS = -g -G0 -xansi -D__STDC__ -I$(PYTHON)/src $(DEFS)

LIBS =	$(LIBPYTHON) \
	-lcl \
	$(LIBFORMS) \
	$(LIBREADLINE) \
	-lm -lsun -laudio -lsvideo -lXext -limage -lgutil -lm  \
	$(LIBDL) -lmld -lmpc -lfm_s -lgl_s -lX11 -ltermcap

LIBDEPS = $(LIBPYTHON) \
	$(LIBFORMS) \
	$(LIBREADLINE) \
	$(LIBDL)

OBJS =	$(BUILD)/pythonmain.o config.o \
	soundchannelmodule.o \
	moviechannelmodule.o \
	mmmodule.o

all:	python

python: $(OBJS) $(LIBDEPS)
	cc $(OBJS) $(LIBS) -o python

ldfiles:
	$(GUIDO)/bin/sgi/python -c \
		'import mmmodule, nullchannel, moviechannel, soundchannel'

clean:
	rm -f *.o core

clobber: clean
	rm -f *.ld python

$(OBJS): mmmodule.h
