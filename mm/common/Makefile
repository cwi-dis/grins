PYTHON = /ufs/guido/src/python
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
	-DPYTHONPATH='"/ufs/guido/lib/python"'
CFLAGS = -g -G0 -xansi -D__STDC__ -I$(PYTHON)/src $(DEFS)

BUILD = $(PYTHON)/build.sgi
LIBS =	$(BUILD)/libpython.a \
	-lcl \
	/ufs/guido/src/forms/FORMS/libforms.a \
	/ufs/guido/src/readline.sgi/libreadline.a \
	-lm -lsun -laudio -lsvideo -lXext -limage -lgutil -lm  \
	/ufs/guido/src/dl/libdl.a -lmld -lmpc -lfm_s -lgl_s -lX11 -ltermcap

OBJS =	$(BUILD)/pythonmain.o config.o \
	soundchannelmodule.o \
	moviechannelmodule.o \
	mmmodule.o

all:	python

python: $(OBJS)
	cc $(OBJS) $(LIBS) -o python

clean:
	rm -f *.o *.ld

$(OBJS):	mmmodule.h
