/*****************************************************************************/
/*                                                                           */
/* MODULE: AccuOSD.h - OS Declarators.                                       */
/*                                                                           */
/*                                                                           */
/* CREATION DATE:  2/10/96                                                   */
/*                                                                           */
/*   $Date$                                         */
/*   $Revision$                                         */
/*                                                                           */
/*     Copyright (c) 1996, AccuSoft Corporation.  All rights reserved.       */
/*                                                                           */
/*****************************************************************************/


#ifndef __ACCUOSD_H__
#define __ACCUOSD_H__


#if defined(WIN32)

/****************************************************************************/
/* 32 Bit Windows (Windows NT and Windows 95)                               */
/****************************************************************************/

#ifdef FAR
#undef FAR
#endif

#ifdef NEAR
#undef NEAR
#endif

#define FAR
#define HUGE
#define NEAR
#define ACCUAPI   __stdcall
#define LACCUAPI  __stdcall

#ifdef _DEBUG
#define INLINE
#else
#define INLINE
#endif

#elif defined(__unix)

/****************************************************************************/
/* Unix (SunOS, Solaris, HP-UX, AIX, SCO)                                   */
/****************************************************************************/

#define FAR
#define HUGE
#define NEAR
#define ACCUAPI
#define LACCUAPI
#define INLINE

#elif defined(__mac)

/****************************************************************************/
/* Macintosh                                                                */
/****************************************************************************/

#define FAR
#define HUGE
#define NEAR
#define ACCUAPI
#define LACCUAPI
#define INLINE

#elif defined(__WINDOWS_386__)

/****************************************************************************/
/* 32 Bit Watcom Windows (Windows 3.1 and Windows for Workgroups)           */
/****************************************************************************/

/***************************************************************************/
/* Platform specific includes                                              */
/***************************************************************************/

#define INCLUDE_COMMDLG_H
#define INCLUDE_SHELLAPI_H
#include <windows.h>    /* Special include for 32-bit Windows 3.x          */

#ifdef FAR
#undef FAR
#endif

#define FAR

#ifndef NEAR
#define NEAR
#endif

#define HUGE

#define ACCUAPI   __pascal
#define LACCUAPI  __pascal
#define INLINE

#else

/****************************************************************************/
/* 16 Bit Windows (Windows 3.1 and Windows for Workgroups)                  */
/****************************************************************************/

#ifndef FAR
#define FAR       __far
#endif

#define HUGE      __huge

#ifndef NEAR
#define NEAR      __near
#endif

#define ACCUAPI   __far __pascal

#ifdef _M_I86LM
#define LACCUAPI  __loadds __far __pascal
#else
#define LACCUAPI  __pascal
#endif

#ifdef _DEBUG
#define INLINE
#else
#define INLINE
#endif

/* #if defined(WIN32) */
#endif

/* #ifndef __ACCUOSD_H__ */
#endif
