#ifndef _HTMLEX_H_
#define _HTMLEX_H_

//Win32 Header Files
#include <process.h>

//MFC Header Files
#include "StdAfx.h"

//Python Header Files
#include "Python.h"

//PythonWin Header Files
#include "win32ui.h"
#include "win32assoc.h"
#include "win32cmd.h"
#include "win32win.h"

#ifdef __cplusplus
extern "C" {
#endif

void CallbackExErrorFunc(char *str);
void initcallbackex();

#ifdef __cplusplus
}
#endif



#endif