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
#ifndef initMacOS
extern void initMacOS();
#endif
#ifndef initaudioop
extern void initaudioop();
#endif
#ifndef initstruct
extern void initstruct();
#endif
#ifndef initimp
extern void initimp();
#endif
#ifndef initimggif
extern void initimggif();
#endif
#ifndef initimgpng
extern void initimgpng();
#endif
#ifndef initList
extern void initList();
#endif
#ifndef initcStringIO
extern void initcStringIO();
#endif
#ifndef initDlg
extern void initDlg();
#endif
#ifndef initRes
extern void initRes();
#endif
#ifndef initrma
extern void initrma();
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
#ifndef initmacfs
extern void initmacfs();
#endif
#ifndef initimgjpeg
extern void initimgjpeg();
#endif
#ifndef initApp
extern void initApp();
#endif
#ifndef init_sre
extern void init_sre();
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
#ifndef initselect
extern void initselect();
#endif
#ifndef initIcn
extern void initIcn();
#endif
#ifndef initpcre
extern void initpcre();
#endif
#ifndef initerrno
extern void initerrno();
#endif
#ifndef init_socket
extern void init_socket();
#endif
#ifndef initbinascii
extern void initbinascii();
#endif
#ifndef initDrag
extern void initDrag();
#endif
#ifndef initimgop
extern void initimgop();
#endif
#ifndef initgestalt
extern void initgestalt();
#endif
#ifndef initwaste
extern void initwaste();
#endif
#ifndef initimgtiff
extern void initimgtiff();
#endif
#ifndef initEvt
extern void initEvt();
#endif
#ifndef initFm
extern void initFm();
#endif
#ifndef initimgformat
extern void initimgformat();
#endif
#ifndef initMenu
extern void initMenu();
#endif
#ifndef initScrap
extern void initScrap();
#endif
#ifndef initNav
extern void initNav();
#endif
#ifndef initimgpgm
extern void initimgpgm();
#endif
#ifndef initSnd
extern void initSnd();
#endif
#ifndef initstrop
extern void initstrop();
#endif
#ifndef initTE
extern void initTE();
#endif
#ifndef initAE
extern void initAE();
#endif
#ifndef initQt
extern void initQt();
#endif
#ifndef initmac
extern void initmac();
#endif
#ifndef initQd
extern void initQd();
#endif
#ifndef initCtl
extern void initCtl();
#endif
#ifndef initicglue
extern void initicglue();
#endif
#ifndef initWin
extern void initWin();
#endif
#ifndef initimgcolormap
extern void initimgcolormap();
#endif
#ifndef initimgsgi
extern void initimgsgi();
#endif
#ifndef inittime
extern void inittime();
#endif
#ifndef initQdoffs
extern void initQdoffs();
#endif

extern void PyMarshal_Init();
extern void initimp();

struct _inittab _PyImport_Inittab[] = {

/* -- ADDMODULE MARKER 2 -- */
	{"MacOS", initMacOS},
	{"audioop", initaudioop},
	{"struct", initstruct},
	{"imp", initimp},
	{"imggif", initimggif},
	{"imgpng", initimgpng},
	{"List", initList},
	{"cStringIO", initcStringIO},
	{"Dlg", initDlg},
	{"Res", initRes},
	{"rma", initrma},
	{"imageop", initimageop},
	{"imgppm", initimgppm},
	{"math", initmath},
	{"macfs", initmacfs},
	{"imgjpeg", initimgjpeg},
	{"App", initApp},
	{"_sre", init_sre},
	{"imgpbm", initimgpbm},
	{"operator", initoperator},
	{"array", initarray},
	{"select", initselect},
	{"Icn", initIcn},
	{"pcre", initpcre},
	{"errno", initerrno},
	{"_socket", init_socket},
	{"binascii", initbinascii},
	{"Drag", initDrag},
	{"imgop", initimgop},
	{"gestalt", initgestalt},
	{"waste", initwaste},
	{"imgtiff", initimgtiff},
	{"Evt", initEvt},
	{"Fm", initFm},
	{"imgformat", initimgformat},
	{"Menu", initMenu},
	{"Scrap", initScrap},
	{"Nav", initNav},
	{"imgpgm", initimgpgm},
	{"Snd", initSnd},
	{"strop", initstrop},
	{"TE", initTE},
	{"AE", initAE},
	{"Qt", initQt},
	{"mac", initmac},
	{"Qd", initQd},
	{"Ctl", initCtl},
	{"icglue", initicglue},
	{"Win", initWin},
	{"imgcolormap", initimgcolormap},
	{"imgsgi", initimgsgi},
	{"time", inittime},
	{"Qdoffs", initQdoffs},

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
