
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "winuser_globals.h"

PyObject* Winuser_MessageLoop(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	MSG msg;
	Py_BEGIN_ALLOW_THREADS
	while(::GetMessage(&msg, NULL, 0, 0)) 
		{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
		}
	Py_END_ALLOW_THREADS
	return none();
}

PyObject* Winuser_PostQuitMessage(PyObject *self, PyObject *args)
{
	int nExitCode = 0;
	if (!PyArg_ParseTuple(args, "|i"))
		return NULL;
	PostQuitMessage(nExitCode);
	return none();
}
