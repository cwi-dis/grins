#define MSL_USE_PRECOMPILED_HEADERS 1
#include <ansi_prefix.mac.h>

#define _DEBUG 1

#ifndef _MACINTOSH
	#define _MACINTOSH   1
	#define OTUNIXERRORS 1

	#ifdef __POWERPC__
		#define _MACPPC	1
	#else
		#define _MAC68K	1
	#endif
#endif
