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
#include <events.h>

#ifdef __MWERKS__
    #include <console.h>
    #include <sioux.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif


// Typedefs
typedef void* HINSTANCE;
typedef HINSTANCE HMODULE;

// Functions to load & release shared libraries
HINSTANCE LoadLibrary    (const char* dllname);
void      FreeLibrary    (HINSTANCE lib);
void*     GetProcAddress (HMODULE lib, char* function);

// String functions
int stricmp  (const char *first, const char *last);
int strnicmp (const char *first, const char *last, size_t count);


#ifdef __cplusplus
}
#endif

#define kPeriodKey 0x2E    /* the period character */

#ifndef _MAX_PATH
#define _MAX_PATH 1024
#endif

#endif

