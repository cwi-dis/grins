
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

PyObject* Winuser_MessageBox(PyObject *self, PyObject *args)
{
	char *text;
	char *caption;
	UINT type = MB_OK;
	if (!PyArg_ParseTuple(args, "ss|i", &text, &caption, &type))
		return NULL;
	int res;
	Py_BEGIN_ALLOW_THREADS
	res = MessageBox(NULL, text, caption, type);
	Py_END_ALLOW_THREADS
	return Py_BuildValue("i", res);
}
