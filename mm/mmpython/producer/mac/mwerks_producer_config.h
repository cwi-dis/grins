/*
** Config file for dynamically-loaded ppc/cfm68k plugin modules.
*/

#define USE_GUSI		/* Stdio implemented with GUSI */
#define USE_MSL			/* Use MSL libraries */
#ifdef USE_MSL
#define MSL_USE_PRECOMPILED_HEADERS 1	/* Use precomp headers */
#include <ansi_prefix.mac.h>
#endif

#ifndef _MACINTOSH
	#define _MACINTOSH   1
	#define OTUNIXERRORS 1

	#ifdef __POWERPC__
		#define _MACPPC	1
	#else
		#define _MAC68K	1
	#endif
#endif
