#include "pywintoolbox.h"

static PyObject *PyMac_OSErrException;

/* Initialize and return PyMac_OSErrException */
PyObject *
PyMac_GetOSErrException(void)
{
	if (PyMac_OSErrException == NULL)
		PyMac_OSErrException = PyString_FromString("MacOS.Error");
	return PyMac_OSErrException;
}

/* Set a MAC-specific error from errno, and return NULL; return None if no error */
PyObject * 
PyErr_Mac(PyObject *eobj, int err)
{
	PyObject *v;
	
	if (err == 0 && !PyErr_Occurred()) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	if (err == -1 && PyErr_Occurred())
		return NULL;
	v = Py_BuildValue("(is)", err, "Quicktime Error");
	PyErr_SetObject(eobj, v);
	Py_DECREF(v);
	return NULL;
}

/* Call PyErr_Mac with PyMac_OSErrException */
PyObject *
PyMac_Error(OSErr err)
{
	return PyErr_Mac(PyMac_GetOSErrException(), err);
}


/*
** These conversion routines are defined in mactoolboxglue.c itself.
*/
/* Convert a 4-char string object argument to an OSType value */
int
PyMac_GetOSType(PyObject *v, OSType *pr)
{
	if (!PyString_Check(v) || PyString_Size(v) != 4) {
		PyErr_SetString(PyExc_TypeError,
			"OSType arg must be string of 4 chars");
		return 0;
	}
	memcpy((char *)pr, PyString_AsString(v), 4);
	return 1;
}

/* Convert an OSType value to a 4-char string object */
PyObject *
PyMac_BuildOSType(OSType t)
{
	return PyString_FromStringAndSize((char *)&t, 4);
}


//PyObject *PyMac_BuildNumVersion(NumVersion) {return 0;}/* Convert NumVersion to PyObject */

/* Convert a Python string object to a Str255 */
/* QTWINPORT XXXX - This one is suspect. I can't image Str255's being used on Windows */
int
PyMac_GetStr255(PyObject *v, Str255 pbuf)
{
	int len;
	if (!PyString_Check(v) || (len = PyString_Size(v)) > 255) {
		PyErr_SetString(PyExc_TypeError,
			"Str255 arg must be string of at most 255 chars");
		return 0;
	}
	pbuf[0] = len;
	memcpy((char *)(pbuf+1), PyString_AsString(v), len);
	return 1;
}
//PyObject *PyMac_BuildStr255(Str255) {return 0;}		/* Convert Str255 to PyObject */
//PyObject *PyMac_BuildOptStr255(Str255) {return 0;}		/* Convert Str255 to PyObject, NULL to None */

int PyMac_GetRect(PyObject *_args, Rect *pr) 
	{
	RECT rc;
	if(!PyArg_ParseTuple(_args, "iiii", &rc.left, &rc.top, &rc.right, &rc.bottom))
		return 0;
	pr->left = short(rc.left);
	pr->top = short(rc.top);
	pr->right = short(rc.right);
	pr->bottom = short(rc.bottom);
	return 1;
	}

PyObject *PyMac_BuildRect(Rect *pr) 
	{return Py_BuildValue("iiii", pr->left, pr->top, pr->right, pr->bottom);}			

int PyMac_GetPoint(PyObject *, Point *) {return 0;}	/* argument parser for Point */
PyObject *PyMac_BuildPoint(Point) {return 0;}			/* Convert Point to PyObject */

int PyMac_GetEventRecord(PyObject *obj, EventRecord  *pe)
	{
	MSG msg;
	if (!PyArg_ParseTuple(obj, "iiiii(ii)", &msg.hwnd, &msg.message, &msg.wParam, &msg.lParam, &msg.time, &msg.pt.x, &msg.pt.y))
		return 0;
	WinEventToMacEvent(&msg, pe);
	return 1;
}
PyObject *PyMac_BuildEventRecord(EventRecord *) {return 0;} /* Convert EventRecord to PyObject */

/* Convert Python object to Fixed */
int
PyMac_GetFixed(PyObject *v, Fixed *f)
{
	double d;
	
	if( !PyArg_Parse(v, "d", &d))
		return 0;
	*f = (Fixed)(d * 0x10000);
	return 1;
}

/* Convert a Fixed to a Python object */
PyObject *
PyMac_BuildFixed(Fixed f)
{
	double d;
	
	d = f;
	d = d / 0x10000;
	return Py_BuildValue("d", d);
}

/* Convert wide to/from Python int or (hi, lo) tuple. XXXX Should use Python longs */
int
PyMac_Getwide(PyObject *v, wide *rv)
{
	if (PyInt_Check(v)) {
		rv->hi = 0;
		rv->lo = PyInt_AsLong(v);
		if( rv->lo & 0x80000000 )
			rv->hi = -1;
		return 1;
	}
	return PyArg_Parse(v, "(ll)", &rv->hi, &rv->lo);
}


PyObject *
PyMac_Buildwide(wide *w)
{
	if ( (w->hi == 0 && (w->lo & 0x80000000) == 0) ||
	     (w->hi == -1 && (w->lo & 0x80000000) ) )
		return PyInt_FromLong(w->lo);
	return Py_BuildValue("(ll)", w->hi, w->lo);
}

/* QTWINPORT XXXX - Suspect. Unless FSSpec's on windows somehow encapsulate
** just a filename */
int PyMac_GetFSSpec(PyObject *, FSSpec *) {return 0;}

/* AE exports */
//extern PyObject *AEDesc_New(AppleEvent *) {return 0;} /* XXXX Why passed by address?? */
//extern int AEDesc_Convert(PyObject *, AppleEvent *) {return 0;}

/* Cm exports */
/* QTWINPORT XXXX - Check whether we actually need the routines that use these objects */
PyObject *CmpObj_New(Component) {return 0;}
int CmpObj_Convert(PyObject *, Component *) {return 0;}
PyObject *CmpInstObj_New(ComponentInstance) {return 0;}
int CmpInstObj_Convert(PyObject *, ComponentInstance *) {return 0;}

/* Ctl exports */
//extern PyObject *CtlObj_New(ControlHandle) {return 0;}
//extern int CtlObj_Convert(PyObject *, ControlHandle *) {return 0;}

/* Dlg exports */
//extern PyObject *DlgObj_New(DialogPtr) {return 0;}
//extern int DlgObj_Convert(PyObject *, DialogPtr *) {return 0;}
//extern PyObject *DlgObj_WhichDialog(DialogPtr) {return 0;}

/* Drag exports */
//extern PyObject *DragObj_New(DragReference) {return 0;}
//extern int DragObj_Convert(PyObject *, DragReference *) {return 0;}

/* List exports */
//extern PyObject *ListObj_New(ListHandle) {return 0;}
//extern int ListObj_Convert(PyObject *, ListHandle *) {return 0;}

/* Menu exports */
//extern PyObject *MenuObj_New(MenuHandle) {return 0;}
/* QTWINPORT XXXX - Check whether we actually need the routines that use these objects */
extern int MenuObj_Convert(PyObject *, MenuHandle *) {return 0;}

/* Qd exports */
/* QTWINPORT XXXX - These we probably need. They'll need to convert from/to some
** sort of a drawing surface (can be onscreen and offscreen on the mac) */

extern PyObject *GrafObj_New(GrafPtr) {return 0;}
extern int GrafObj_Convert(PyObject *, GrafPtr *) {return 0;}
//extern PyObject *BMObj_New(BitMapPtr) {return 0;}
//extern int BMObj_Convert(PyObject *, BitMapPtr *) {return 0;}
/* QTWINPORT XXXX -These are simple RGB values. Treat like point/rect, I guess, just use Windows
** standard RGB values */
extern PyObject *QdRGB_New(RGBColor *) {return 0;}
extern int QdRGB_Convert(PyObject *, RGBColor *) {return 0;}

/* Qdoffs exports */
//extern PyObject *GWorldObj_New(GWorldPtr) {return 0;}
/* QTWINPORT XXXX - This could be a tricky one. A GWorld is an offscreen drawing context */
extern int GWorldObj_Convert(PyObject *, GWorldPtr *) {return 0;}


/* Res exports */
/* QTWINPORT XXXX - These have to be checked. MacPython code is a bit sloppy, and it uses
** ResObj_xxxxx() for any type of handle. So some will be region Handles, some will be
** completely different types. */
extern PyObject *ResObj_New(Handle) {return 0;}
extern int ResObj_Convert(PyObject *, Handle *) {return 0;}
extern PyObject *OptResObj_New(Handle) {return 0;}
extern int OptResObj_Convert(PyObject *, Handle *) {return 0;}

/* TE exports */
//extern PyObject *TEObj_New(TEHandle) {return 0;}
//extern int TEObj_Convert(PyObject *, TEHandle *) {return 0;}

/* Win exports */
//extern PyObject *WinObj_New(WindowPtr) {return 0;}
/* QTWINPORT XXXX - Probably simply accept a windows WinObj or whatever, run through the
** Qt win->mac conversion routine and pass back. */
extern int WinObj_Convert(PyObject *, WindowPtr *) {return 0;}
//extern PyObject *WinObj_WhichWindow(WindowPtr) {return 0;}
