/*
** Configuration file for standalone 68k/ppc Python.
**
** Note: enabling the switches below is not enough to enable the
** specific features, you may also need different sets of sources.
*/

#define USE_GUSI2		/* Stdio implemented with GUSI */
#if defined(USE_GUSI1) || defined(USE_GUSI2)
#define USE_GUSI
#endif
#define USE_MSL			/* Use Mw Standard Library (as opposed to Plaugher C libraries) */
#define USE_TOOLBOX		/* Include toolbox modules in core Python */
#define USE_QT			/* Include quicktime modules in core Python */
#define USE_WASTE		/* Include waste module in core Python */
/* #define USE_MACSPEECH		/* Include macspeech module in core Python */
#define USE_IMG	       		/* Include img modules in core Python */
/* #define USE_MACCTB		/* Include ctb module in core Python */
/* #define USE_STDWIN		/* Include stdwin module in core Python */
/* #define USE_MACTCP		/* Include mactcp (*not* socket) modules in core */
/* #define USE_TK			/* Include _tkinter module in core Python */
/* #define MAC_TCL			/* This *must* be on if USE_TK is on */
/* #define USE_MAC_SHARED_LIBRARY	/* Enable code to add shared-library resources */
#define USE_MAC_APPLET_SUPPORT	/* Enable code to run a PYC resource */
/* #define USE_MAC_DYNAMIC_LOADING		/* Enable dynamically loaded modules */
/* #define USE_MALLOC_DEBUG			/* Enable range checking and other malloc debugging */
/* #define USE_GDBM		/* Include the gdbm module */
/* #define USE_ZLIB		/* Include the zlib module */
#define USE_MSL_MALLOC	/* Disable private malloc. Also disables next two defines */
#ifndef USE_MSL_MALLOC
/* #define USE_MALLOC_DEBUG			/* Enable range checking and other malloc debugging */
#ifdef __powerc
#define USE_CACHE_ALIGNED 8		/* Align on 32-byte boundaries for 604 */
#endif
#endif
#ifdef USE_MSL
#define MSL_USE_PRECOMPILED_HEADERS 0	/* Don't use precomp headers: we include our own */
#include <ansi_prefix.mac.h>
#endif

#if __POWERPC__
#define WITH_RMA_SUPPORT	/* Support for real media types */
#define _MACINTOSH 1
#define _MACPPC 1
#endif
#ifndef WITH_RMA_SUPPORT
#define initrma 0
#endif