
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}

static void
seterror(const char *funcname, DWORD err)
{
	char* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 err,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(ErrorObject, "%s failed, error = %x, %s", funcname, err, pszmsg);
	LocalFree(pszmsg);
}


static char GetDesktopWindow__doc__[] =
"returns a handle to the desktop window"
;
static PyObject*
GetDesktopWindow(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HWND hwnd = GetDesktopWindow();
	return Py_BuildValue("i", hwnd);
}

static char GetDC__doc__[] =
"retrieves a handle to a display device context (DC) for the client area of a specified window"
;
static PyObject*
GetDC(PyObject *self, PyObject *args)
{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;
	HDC hdc = GetDC(hwnd);
	return Py_BuildValue("i", hdc);
}

static char InvalidateRect__doc__[] =
"adds a rectangle to the specified window's update region"
;
static PyObject*
InvalidateRect(PyObject *self, PyObject *args)
{
	HWND hwnd;
	PyObject *pyrc; 
	BOOL bErase;
	if (!PyArg_ParseTuple(args, "iOi", &hwnd, &pyrc, &bErase))
		return NULL;
	RECT rc, *prc = NULL;
	if(pyrc != Py_None)
		{
		if(!PyArg_ParseTuple(pyrc, "iiii", &rc.left, &rc.top, &rc.right, &rc.bottom)) 
			{
			seterror("second argument should be a rect tuple or None");
			return NULL;
			}
		prc = &rc;
		}
	BOOL res = InvalidateRect(hwnd, prc, bErase);
	if(!res){
		seterror("InvalidateRect", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GetClientRect__doc__[] =
"retrieves the coordinates of a window's client area"
;
static PyObject*
GetClientRect(PyObject *self, PyObject *args)
{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i", &hwnd))
		return NULL;
	RECT rc;
	BOOL res = GetClientRect(hwnd, &rc);
	if(!res){
		seterror("GetClientRect", GetLastError());
		return NULL;
		}
	return Py_BuildValue("iiii", rc.left, rc.top, rc.right, rc.bottom);
}

static char RedrawWindow__doc__[] =
"updates the specified rectangle or region in a window's client area"
;
static PyObject*
RedrawWindow(PyObject *self, PyObject *args)
{
	HWND hWnd;            // handle to window
	PyObject *pyrc;	      // update rectangle
	HRGN hrgn;            // handle to update region
	UINT flags;           // array of redraw flags
	if (!PyArg_ParseTuple(args, "iOii", &hWnd, &pyrc, &hrgn, &flags))
		return NULL;
	RECT rc, *prc = NULL;
	if(pyrc != Py_None)
		{
		if(!PyArg_ParseTuple(pyrc, "iiii", &rc.left, &rc.top, &rc.right, &rc.bottom)) 
			{
			seterror("second argument should be a rect tuple or None");
			return NULL;
			}
		prc = &rc;
		}
	BOOL res = RedrawWindow(hWnd, prc, hrgn, flags);
	if(!res){
		seterror("RedrawWindow", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}
	
static struct PyMethodDef winuser_methods[] = {
	{"GetDesktopWindow", (PyCFunction)GetDesktopWindow, METH_VARARGS, GetDesktopWindow__doc__},
	{"GetDC", (PyCFunction)GetDC, METH_VARARGS, GetDC__doc__},
	{"GetClientRect", (PyCFunction)GetClientRect, METH_VARARGS, GetClientRect__doc__},
	{"InvalidateRect", (PyCFunction)InvalidateRect, METH_VARARGS, InvalidateRect__doc__},
	{"RedrawWindow", (PyCFunction)RedrawWindow, METH_VARARGS, RedrawWindow__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

/////////////////////////////////////

static char winuser_module_documentation[] =
"Windows user module"
;

extern "C" __declspec(dllexport)
void initwinuser()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("winuser", winuser_methods,
		winuser_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("winuser.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module winuser");
}
