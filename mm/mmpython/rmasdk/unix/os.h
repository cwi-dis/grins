/****************************************************************************
 * 
 *  $Id$
 *
 *  Copyright (C) 1995,1996,1997 RealNetworks, Inc.
 *  All rights reserved.
 *
 *  http://www.real.com/devzone
 *
 *  This program contains proprietary information of RealNetworks, Inc.,
 *  and is licensed subject to restrictions on use and distribution.
 *
 *  Operating System Dependant defines, functions, and includes
 *
 */

#ifndef _OS_
#define _OS_

#include <stdio.h>
#if defined (_SCO_UW)
#include <strings.h>		/* for strcasecmp() */
#endif
#include <string.h>
#include <sys/time.h>
#include <sys/types.h>

#define stricmp strcasecmp

#ifndef _MAX_PATH
#define _MAX_PATH  1024
#endif

#include <X11/Intrinsic.h>
#include <X11/StringDefs.h>
#include <X11/Shell.h>

#if defined( _WIN32 ) || defined( _WINDOWS )
#include <windows.h>
#endif

#if defined(_UNIX)
#include <dlfcn.h>
#endif

#ifdef _FREEBSD
#include <stdlib.h>
#endif

#if (!defined( _WIN32 )) && (!defined( _WINDOWS ))
    typedef void* HINSTANCE;
#endif

#if defined(_UNIX)
inline HINSTANCE
LoadLibrary(char* pFileName)
{
    char  pNewFileName[2048];
    char* pTemp = pNewFileName;

    for (; *pFileName; pFileName++)
    {
	if (*pFileName == '.')
	{
	    const char SUFFIX[] = ".so.6.0";
	    memcpy (pTemp, SUFFIX, sizeof(SUFFIX));


#if defined _SCO_SV
		/* On SCO OpenServer5, we get unresolved symbols from rmacore and
		 * crashes if we do not use RLTL_GLOBAL here.  This problem usually
		 * occured later when we called dlclose().  The symbols this
		 * has occured with include CRaErrorMsg and CPNString.
		 * We can open the codecs without RTLD_GLOBAL, but appear to
		 * need it for rmacore.  (See similar change below, too.)
		 * We do not appear to need this on SCO Unixware.
		 */
	    return dlopen(pNewFileName, RTLD_LAZY|RTLD_GLOBAL);
#elif defined _FREEBSD
	    void* pDll=NULL;
	    if (pDll = dlopen(pNewFileName, 1)) 
		return pDll;
	    else
		break;
#else
	    return dlopen(pNewFileName, 1);
#endif
	}
	else
	{
	    *pTemp++ = *pFileName;
	}
    }

#if defined(_FREEBSD)
    {
	char* ld_library_path = getenv("LD_LIBRARY_PATH");
	char  next_path[2048];
	char* colon;
	char* ptr;
	void* handle = NULL;

	handle = dlopen(pFileName, 1);
	colon = ld_library_path;
	while(!handle && colon && *colon)
	{
	    while(*colon == ':')
		colon++;

	    for(ptr = next_path; *colon != 0 && *colon != ':' ; colon++)
		*ptr++ = *colon;

	    if(*ptr != '/')
		*ptr++ = '/';
	    *ptr = 0;
	    strcat(next_path, pNewFileName);
	    handle = dlopen(next_path, 1);

	}
	return handle;
    }
#elif defined(_LINUX)
    return dlopen(pFileName, RTLD_LAZY);
#elif defined(_SCO_SV)
    return dlopen(pNewFileName, RTLD_LAZY|RTLD_GLOBAL);
#else
    return dlopen(pNewFileName, 1);
#endif
}
#endif

#if defined(_UNIX)
inline void*
GetProcAddress(HINSTANCE pDLL, char* pSymbol)
{
#if defined(_FREEBSD)
    char pNewSymbol[2048];
    sprintf(pNewSymbol, "_%s", pSymbol);
    return dlsym(pDLL, pNewSymbol);
#else
    return dlsym(pDLL, pSymbol);
#endif
}
#endif

#if defined(_UNIX)
inline void
FreeLibrary(HINSTANCE pDLL)
{
    dlclose(pDLL);
}
#endif

#endif
