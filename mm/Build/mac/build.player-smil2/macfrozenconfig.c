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
#ifndef initQdoffs
extern void initQdoffs();
#endif
#ifndef inittime
extern void inittime();
#endif
#ifndef initimgsgi
extern void initimgsgi();
#endif
#ifndef initimgjpeg
extern void initimgjpeg();
#endif
#ifndef initWin
extern void initWin();
#endif
#ifndef initicglue
extern void initicglue();
#endif
#ifndef initCtl
extern void initCtl();
#endif
#ifndef initQd
extern void initQd();
#endif
#ifndef initmac
extern void initmac();
#endif
#ifndef initList
extern void initList();
#endif
#ifndef initQt
extern void initQt();
#endif
#ifndef initAE
extern void initAE();
#endif
#ifndef initTE
extern void initTE();
#endif
#ifndef initimggif
extern void initimggif();
#endif
#ifndef initstrop
extern void initstrop();
#endif
#ifndef initSnd
extern void initSnd();
#endif
#ifndef initNav
extern void initNav();
#endif
#ifndef initScrap
extern void initScrap();
#endif
#ifndef initMenu
extern void initMenu();
#endif
#ifndef initEvt
extern void initEvt();
#endif
#ifndef initFm
extern void initFm();
#endif
#ifndef initwaste
extern void initwaste();
#endif
#ifndef initgestalt
extern void initgestalt();
#endif
#ifndef initimgformat
extern void initimgformat();
#endif
#ifndef initimgop
extern void initimgop();
#endif
#ifndef initDrag
extern void initDrag();
#endif
#ifndef initbinascii
extern void initbinascii();
#endif
#ifndef init_socket
extern void init_socket();
#endif
#ifndef initerrno
extern void initerrno();
#endif
#ifndef initpcre
extern void initpcre();
#endif
#ifndef initarray
extern void initarray();
#endif
#ifndef initimgpbm
extern void initimgpbm();
#endif
#ifndef init_sre
extern void init_sre();
#endif
#ifndef initApp
extern void initApp();
#endif
#ifndef initmacfs
extern void initmacfs();
#endif
#ifndef initmath
extern void initmath();
#endif
#ifndef initimgppm
extern void initimgppm();
#endif
#ifndef initrma
extern void initrma();
#endif
#ifndef initRes
extern void initRes();
#endif
#ifndef initDlg
extern void initDlg();
#endif
#ifndef initcStringIO
extern void initcStringIO();
#endif
#ifndef initimageop
extern void initimageop();
#endif
#ifndef initimgcolormap
extern void initimgcolormap();
#endif
#ifndef initimgtiff
extern void initimgtiff();
#endif
#ifndef initimgpgm
extern void initimgpgm();
#endif
#ifndef initimgpng
extern void initimgpng();
#endif
#ifndef initimp
extern void initimp();
#endif
#ifndef initstruct
extern void initstruct();
#endif
#ifndef initIcn
extern void initIcn();
#endif
#ifndef initaudioop
extern void initaudioop();
#endif
#ifndef initMacOS
extern void initMacOS();
#endif

extern void PyMarshal_Init();
extern void initimp();

struct _inittab _PyImport_Inittab[] = {

/* -- ADDMODULE MARKER 2 -- */
	{"Qdoffs", initQdoffs},
	{"time", inittime},
	{"imgsgi", initimgsgi},
	{"imgjpeg", initimgjpeg},
	{"Win", initWin},
	{"icglue", initicglue},
	{"Ctl", initCtl},
	{"Qd", initQd},
	{"mac", initmac},
	{"List", initList},
	{"Qt", initQt},
	{"AE", initAE},
	{"TE", initTE},
	{"imggif", initimggif},
	{"strop", initstrop},
	{"Snd", initSnd},
	{"Nav", initNav},
	{"Scrap", initScrap},
	{"Menu", initMenu},
	{"Evt", initEvt},
	{"Fm", initFm},
	{"waste", initwaste},
	{"gestalt", initgestalt},
	{"imgformat", initimgformat},
	{"imgop", initimgop},
	{"Drag", initDrag},
	{"binascii", initbinascii},
	{"_socket", init_socket},
	{"errno", initerrno},
	{"pcre", initpcre},
	{"array", initarray},
	{"imgpbm", initimgpbm},
	{"_sre", init_sre},
	{"App", initApp},
	{"macfs", initmacfs},
	{"math", initmath},
	{"imgppm", initimgppm},
	{"rma", initrma},
	{"Res", initRes},
	{"Dlg", initDlg},
	{"cStringIO", initcStringIO},
	{"imageop", initimageop},
	{"imgcolormap", initimgcolormap},
	{"imgtiff", initimgtiff},
	{"imgpgm", initimgpgm},
	{"imgpng", initimgpng},
	{"imp", initimp},
	{"struct", initstruct},
	{"Icn", initIcn},
	{"audioop", initaudioop},
	{"MacOS", initMacOS},

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
