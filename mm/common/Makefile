PYTHON = /ufs/sjoerd/src/python
CFLAGS = -DMM_DEBUG -g -G0 -xansi -D__STDC__ -I$(PYTHON)/src

OBJS =	\
	soundchannelmodule.o \
	moviechannelmodule.o \
	nullchannelmodule.o \
	mmmodule.o

all:	$(OBJS)

$(OBJS):	mmmodule.h
