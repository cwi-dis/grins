#ifndef _REGISTRYEX_H_
#define _REGISTRYEX_H_

//Win32 Header Files
#include <process.h>

//MFC Header Files
#include "StdAfx.h"

//Python Header Files
#define Py_USE_NEW_NAMES
#include "allobjects.h"
#include "modsupport.h"
#include "abstract.h"
#include "Python.h"

//PythonWin Header Files
#include "win32ui.h"
#include "win32assoc.h"
#include "win32cmd.h"
#include "win32win.h"

//RegEx Header Files
#define PyIMPORT  __declspec(dllimport)
#define PyEXPORT  __declspec(dllexport)

