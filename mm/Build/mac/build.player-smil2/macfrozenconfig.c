/* Generated automatically from /ufs/jack/src/python/build.irix6/tmp/lib/python1.5/config/config.c.in by makesetup. */
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

/* Module configuration */

/* !!! !!! !!! This file is edited by the makesetup script !!! !!! !!! */

/* This file contains the table of built-in modules.
   See init_builtin() in import.c. */

#include "Python.h"


/* -- ADDMODULE MARKER 1 -- */
#ifndef init_Snd
extern void init_Snd();
#endif
#ifndef initimgpng
extern void initimgpng();
#endif
#ifndef init_Fm
extern void init_Fm();
#endif
#ifndef initrma
extern void initrma();
#endif
#ifndef initmacfs
extern void initmacfs();
#endif
#ifndef init_Menu
extern void init_Menu();
#endif
#ifndef init_List
extern void init_List();
#endif
#ifndef initimgjpeg
extern void initimgjpeg();
#endif
#ifndef init_sre
extern void init_sre();
#endif
#ifndef init_Ctl
extern void init_Ctl();
#endif
#ifndef init_Icn
extern void init_Icn();
#endif
#ifndef initselect
extern void initselect();
#endif
#ifndef initimp
extern void initimp();
#endif
#ifndef init_Qd
extern void init_Qd();
#endif
#ifndef initbinascii
extern void initbinascii();
#endif
#ifndef initimgop
extern void initimgop();
#endif
#ifndef initwaste
extern void initwaste();
#endif
#ifndef init_Dlg
extern void init_Dlg();
#endif
#ifndef init_Evt
extern void init_Evt();
#endif
#ifndef init_Res
extern void init_Res();
#endif
#ifndef initimgformat
extern void initimgformat();
#endif
#ifndef initimgtiff
extern void initimgtiff();
#endif
#ifndef initNav
extern void initNav();
#endif
#ifndef init_Qt
extern void init_Qt();
#endif
#ifndef initimgpgm
extern void initimgpgm();
#endif
#ifndef initstrop
extern void initstrop();
#endif
#ifndef init_TE
extern void init_TE();
#endif
#ifndef initimgcolormap
extern void initimgcolormap();
#endif
#ifndef initimgsgi
extern void initimgsgi();
#endif
#ifndef initMacOS
extern void initMacOS();
#endif
#ifndef initaudioop
extern void initaudioop();
#endif
#ifndef initstruct
extern void initstruct();
#endif
#ifndef init_AE
extern void init_AE();
#endif
#ifndef initcStringIO
extern void initcStringIO();
#endif
#ifndef initimageop
extern void initimageop();
#endif
#ifndef initimgppm
extern void initimgppm();
#endif
#ifndef initmath
extern void initmath();
#endif
#ifndef initmac
extern void initmac();
#endif
#ifndef initerrno
extern void initerrno();
#endif
#ifndef init_App
extern void init_App();
#endif
#ifndef initimgpbm
extern void initimgpbm();
#endif
#ifndef initoperator
extern void initoperator();
#endif
#ifndef initarray
extern void initarray();
#endif
#ifndef initpcre
extern void initpcre();
#endif
#ifndef init_Qdoffs
extern void init_Qdoffs();
#endif
#ifndef init_socket
extern void init_socket();
#endif
#ifndef initicglue
extern void initicglue();
#endif
#ifndef init_codecs
extern void init_codecs();
#endif
#ifndef initgestalt
extern void initgestalt();
#endif
#ifndef init_Scrap
extern void init_Scrap();
#endif
#ifndef initimggif
extern void initimggif();
#endif
#ifndef inittime
extern void inittime();
#endif
#ifndef init_Drag
extern void init_Drag();
#endif
#ifndef init_Win
extern void init_Win();
#endif

extern void PyMarshal_Init();
extern void initimp();

struct _inittab _PyImport_Inittab[] = {

/* -- ADDMODULE MARKER 2 -- */
	{"_Snd", init_Snd},
	{"imgpng", initimgpng},
	{"_Fm", init_Fm},
	{"rma", initrma},
	{"macfs", initmacfs},
	{"_Menu", init_Menu},
	{"_List", init_List},
	{"imgjpeg", initimgjpeg},
	{"_sre", init_sre},
	{"_Ctl", init_Ctl},
	{"_Icn", init_Icn},
	{"select", initselect},
	{"imp", initimp},
	{"_Qd", init_Qd},
	{"binascii", initbinascii},
	{"imgop", initimgop},
	{"waste", initwaste},
	{"_Dlg", init_Dlg},
	{"_Evt", init_Evt},
	{"_Res", init_Res},
	{"imgformat", initimgformat},
	{"imgtiff", initimgtiff},
	{"Nav", initNav},
	{"_Qt", init_Qt},
	{"imgpgm", initimgpgm},
	{"strop", initstrop},
	{"_TE", init_TE},
	{"imgcolormap", initimgcolormap},
	{"imgsgi", initimgsgi},
	{"MacOS", initMacOS},
	{"audioop", initaudioop},
	{"struct", initstruct},
	{"_AE", init_AE},
	{"cStringIO", initcStringIO},
	{"imageop", initimageop},
	{"imgppm", initimgppm},
	{"math", initmath},
	{"mac", initmac},
	{"errno", initerrno},
	{"_App", init_App},
	{"imgpbm", initimgpbm},
	{"operator", initoperator},
	{"array", initarray},
	{"pcre", initpcre},
	{"_Qdoffs", init_Qdoffs},
	{"_socket", init_socket},
	{"icglue", initicglue},
	{"_codecs", init_codecs},
	{"gestalt", initgestalt},
	{"_Scrap", init_Scrap},
	{"imggif", initimggif},
	{"time", inittime},
	{"_Drag", init_Drag},
	{"_Win", init_Win},

	/* This module "lives in" with marshal.c */
	{"marshal", PyMarshal_Init},

	/* This lives it with import.c */
	{"imp", initimp},

	/* These entries are here for sys.builtin_module_names */
	{"__main__", NULL},
	{"__builtin__", NULL},
	{"sys", NULL},

	/* Sentinel */
	{0, 0}
};
