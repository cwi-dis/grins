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
extern void inittime();
extern void initimgsgi();
extern void initimgcolormap();
extern void initimageop();
extern void initWin();
extern void initicglue();
extern void initCtl();
extern void initList();
extern void initQd();
extern void initmac();
extern void initQt();
extern void initAE();
extern void initTE();
#ifdef WITH_GIF_SUPPORT
extern void initimggif();
#endif
extern void initstrop();
extern void initSnd();
extern void initimgtiff();
extern void initScrap();
extern void initMenu();
extern void initEvt();
extern void initFm();
extern void initwaste();
extern void initmacfs();
extern void initimgformat();
extern void initimgop();
extern void initDrag();
extern void initbinascii();
extern void initpcre();
extern void initregex();
extern void initarray();
extern void initimgpbm();
extern void initimgjpeg();
extern void initsocket();
extern void initmath();
extern void initimgppm();
#ifdef WITH_RMA_SUPPORT
extern void initrma();
#endif
extern void initRes();
extern void initDlg();
extern void initcStringIO();
extern void initimgpgm();
extern void initstruct();
extern void initaudioop();
extern void initMacOS();

extern void PyMarshal_Init();
extern void initimp();

struct _inittab _PyImport_Inittab[] = {

/* -- ADDMODULE MARKER 2 -- */
	{"time", inittime},
	{"imgsgi", initimgsgi},
	{"imgcolormap", initimgcolormap},
	{"imageop", initimageop},
	{"Win", initWin},
	{"icglue", initicglue},
	{"Ctl", initCtl},
	{"List", initList},
	{"Qd", initQd},
	{"mac", initmac},
	{"Qt", initQt},
	{"AE", initAE},
	{"TE", initTE},
#ifdef WITH_GIF_SUPPORT
	{"imggif", initimggif},
#endif
	{"strop", initstrop},
	{"Snd", initSnd},
	{"imgtiff", initimgtiff},
	{"Scrap", initScrap},
	{"Menu", initMenu},
	{"Evt", initEvt},
	{"Fm", initFm},
	{"waste", initwaste},
	{"macfs", initmacfs},
	{"imgformat", initimgformat},
	{"imgop", initimgop},
	{"Drag", initDrag},
	{"binascii", initbinascii},
	{"pcre", initpcre},
	{"regex", initregex},
	{"array", initarray},
	{"imgpbm", initimgpbm},
	{"imgjpeg", initimgjpeg},
	{"socket", initsocket},
	{"math", initmath},
	{"imgppm", initimgppm},
#ifdef WITH_RMA_SUPPORT
	{"rma", initrma},
#endif
	{"Res", initRes},
	{"Dlg", initDlg},
	{"cStringIO", initcStringIO},
	{"imgpgm", initimgpgm},
	{"struct", initstruct},
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
