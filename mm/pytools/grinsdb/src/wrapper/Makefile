prefix=   	/ufs/jack/src/mm/pytools/grinsdb/src
exec_prefix=	${prefix}
srcdir= 	.
bindir= 	${exec_prefix}/bin

CC=		cc
INSTALL=	/ufs/jack/bin/sgi/install -c
PYTHON=  	/ufs/jack/bin/sgi/python

DEFS=   	 -DHAVE_STRERROR=1 -DHAVE_SETREGID=1 -DSTDC_HEADERS=1 -DHAVE_SYSLOG_H=1 -DGETGROUPS_T=gid_t -DHAVE_VPRINTF=1 

# UIDs and GIDs
MAIL_GID=      	60001
CGI_GID=	60001

# Customizable but not set by configure
COMMON_FLAGS=	-DPREFIX="\"$(prefix)\"" \
		-DPYTHON="\"$(PYTHON)\""
OPT=		-O
CFLAGS=		$(OPT) $(DEFS) -DMAIL_GID=$(MAIL_GID) -DCGI_GID=$(CGI_GID) \
		$(COMMON_FLAGS)

ALL=mail-wrapper
INSTALLDIR=../../bin

all: $(ALL)

install: $(ALL)
	cp mail-wrapper $(INSTALLDIR)
	chmod 2755 $(INSTALLDIR)/mail-wrapper

mail-wrapper: mail-wrapper.o common.o
	$(CC) -o mail-wrapper mail-wrapper.o common.o