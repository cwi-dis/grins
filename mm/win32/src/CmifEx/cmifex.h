#ifndef _CMIFEX_H_
#define _CMIFEX_H_

//Win32 Header Files
#include <process.h>

//MFC Header Files
#include "StdAfx.h"

//Python Header Files
#define Py_USE_NEW_NAMES
#include "Python.h"
#include "modsupport.h"
#include "abstract.h"

//PythonWin Header Files
#include "win32ui.h"
#include "win32assoc.h"
#include "win32cmd.h"
#include "win32win.h"

//CmifEx Header Files
#include "resource.h"
#include "cmifexhelp.h"
#define PyEXPORT  __declspec(dllexport)

#endif