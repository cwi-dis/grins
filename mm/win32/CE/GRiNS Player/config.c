/* -*- C -*- ***********************************************
Copyright 1991-1995 by Stichting Mathematisch Centrum, Amsterdam,
The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI or Corporation for National Research Initiatives or
CNRI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

While CWI is the initial source for this software, a modified version
is made available by the Corporation for National Research Initiatives
(CNRI) at the Internet address ftp://ftp.python.org.

STICHTING MATHEMATISCH CENTRUM AND CNRI DISCLAIM ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH
CENTRUM OR CNRI BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

******************************************************************/

#include "Python.h"

extern void initarray(void);
extern void initbinascii(void);
extern void initce(void);
extern void initcmath(void);
extern void initcStringIO(void);
extern void initimp(void);
extern void initmath(void);
extern void initmd5(void);
extern void initnew(void);
extern void PyMarshal_Init(void);
extern void initpcre(void);
extern void initregex(void);
extern void init_socket(void);
extern void initselect(void);
extern void initstrop(void);
extern void initstruct(void);
#ifdef WITH_THREAD
extern void initthread(void);
#endif
extern void inittime(void);
extern void init_codecs(void);
extern void initwingdi(void);
extern void initwinkernel(void);
extern void initwinmm(void);
extern void initwinuser(void);




struct _inittab _PyImport_Inittab[]=
{
	{"array",		initarray},
	{"binascii",		initbinascii},
	{"ce",			initce},
	{"cmath", 		initcmath},
	{"cStringIO",		initcStringIO},
	{"imp",			initimp},
	{"math",		initmath},
	{"md5",			initmd5},
	{"marshal",		PyMarshal_Init},
	{"new",			initnew},
	{"regex",		initregex},
	{"strop",		initstrop},
	{"struct",		initstruct},
#ifdef WITH_THREAD
	{"thread",		initthread},
#endif
	{"time",        	inittime},
	{"pcre", 		initpcre},
	{"_socket", 		init_socket},
	{"select",		initselect},
	{"_codecs",		init_codecs},
	{"__main__",		NULL},
	{"__builtin__",		NULL},
	{"sys",			NULL},
	{"wingdi",		initwingdi},
	{"winkernel",		initwinkernel},
	{"winmm",		initwinmm},
	{"winuser",		initwinuser},
	{0, 			0}
};
