
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "mtpycall.h"

#include "winuser_main.h"
#include "winuser_wnd.h"
#include "winuser_menu.h"
#include "winuser_ofn.h"

PyObject *ErrorObject;

PyInterpreterState*
PyCallbackBlock::s_interpreterState = NULL;

static struct PyMethodDef winuser_methods[] = {
	{"MessageLoop", (PyCFunction)Winuser_MessageLoop, METH_VARARGS, ""},
	{"PostQuitMessage", (PyCFunction)Winuser_PostQuitMessage, METH_VARARGS, ""},
	{"MessageBox", (PyCFunction)Winuser_MessageBox, METH_VARARGS, ""},
	{"GetSystemMetrics", (PyCFunction)Winuser_GetSystemMetrics, METH_VARARGS, ""},
	{"GetSysColor", (PyCFunction)Winuser_GetSysColor, METH_VARARGS, ""},
	{"GetDC", (PyCFunction)Winuser_GetDC, METH_VARARGS, ""},
	{"LoadStandardCursor", (PyCFunction)Winuser_LoadStandardCursor, METH_VARARGS, ""},
	{"LoadCursor", (PyCFunction)Winuser_LoadCursor, METH_VARARGS, ""},

	{"RegisterClassEx", (PyCFunction)Winuser_RegisterClassEx, METH_VARARGS, ""},

	{"CreateWindowEx", (PyCFunction)Winuser_CreateWindowEx, METH_VARARGS, ""},
	{"CreateWindowFromHandle", (PyCFunction)Winuser_CreateWindowFromHandle, METH_VARARGS, ""},
	{"GetDesktopWindow", (PyCFunction)Winuser_GetDesktopWindow, METH_VARARGS, ""},
	
	{"CreateMenu", (PyCFunction)Winuser_CreateMenu, METH_VARARGS, ""},
	{"CreatePopupMenu", (PyCFunction)Winuser_CreatePopupMenu, METH_VARARGS, ""},
	{"CreateMenuFromHandle", (PyCFunction)Winuser_CreateMenuFromHandle, METH_VARARGS, ""},

	{"CreateFileDialog", (PyCFunction)Winuser_CreateFileDialog, METH_VARARGS, ""},

	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
	};

extern "C" __declspec(dllexport) 
void initwinuser()
	{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	PyCallbackBlock::init();	

	// Create the module and add the functions
	m = Py_InitModule4("winuser", winuser_methods,
		"winuser module",
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("winuser.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module winuser");
	}
