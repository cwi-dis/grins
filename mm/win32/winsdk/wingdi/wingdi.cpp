
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "wingdi_main.h"
#include "wingdi_dc.h"
#include "wingdi_rgn.h"

PyObject *ErrorObject;

static struct PyMethodDef wingdi_methods[] = {
	{"CreateDCFromHandle", (PyCFunction)Wingdi_CreateDCFromHandle, METH_VARARGS, ""},
	
	{"DeleteObject", (PyCFunction)Wingdi_DeleteObject, METH_VARARGS, ""},
	{"GetStockObject", (PyCFunction)Wingdi_GetStockObject, METH_VARARGS, ""},
	{"CreateSolidBrush", (PyCFunction)Wingdi_CreateSolidBrush, METH_VARARGS, ""},
	{"CreateFontIndirect", (PyCFunction)Wingdi_CreateFontIndirect, METH_VARARGS, ""},

	{"IntersectRect", (PyCFunction)Wingdi_IntersectRect, METH_VARARGS, ""},
	{"UnionRect", (PyCFunction)Wingdi_UnionRect, METH_VARARGS, ""},

	{"GetRGBValues", (PyCFunction)Wingdi_GetRGBValues, METH_VARARGS, ""},

	{"CreateRectRgn", (PyCFunction)Wingdi_CreateRectRgn, METH_VARARGS, ""},

	{"CombineRgn", (PyCFunction)Wingdi_CombineRgn, METH_VARARGS, ""},

#ifndef _WIN32_WCE
	{"CreatePolygonRgn", (PyCFunction)Wingdi_CreatePolygonRgn, METH_VARARGS, ""},
	{"CreateBrushIndirect", (PyCFunction)Wingdi_CreateBrushIndirect, METH_VARARGS, ""},
	{"ExtCreatePen", (PyCFunction)Wingdi_ExtCreatePen, METH_VARARGS, ""},
#endif
	
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};


extern "C" __declspec(dllexport)
void initwingdi()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("wingdi", wingdi_methods,
		"Windows GDI module",
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("wingdi.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module wingdi");
}
