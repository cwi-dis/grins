#include "pywintoolbox.h"

static PyObject *PyMac_OSErrException;

PyObject *
PyMac_GetOSErrException(void){
	/* Call it Qt.Error on windows */
	if ( PyMac_OSErrException == NULL )
		PyMac_OSErrException = PyString_FromString("Qt.Error");
	return PyMac_OSErrException;
}

PyObject *PyErr_Mac(PyObject *, int){return 0;}		/* Exception with a mac error */
PyObject *PyMac_Error(OSErr){return 0;}				/* Uses PyMac_GetOSErrException */


/*
** These conversion routines are defined in mactoolboxglue.c itself.
*/
int PyMac_GetOSType(PyObject *, OSType *) {return 0;}	/* argument parser for OSType */
PyObject *PyMac_BuildOSType(OSType) {return 0;}		/* Convert OSType to PyObject */

//PyObject *PyMac_BuildNumVersion(NumVersion) {return 0;}/* Convert NumVersion to PyObject */

int PyMac_GetStr255(PyObject *, Str255) {return 0;}	/* argument parser for Str255 */
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
//
int PyMac_GetEventRecord(PyObject *obj, EventRecord  *pe)
	{
	MSG msg;
	if (!PyArg_ParseTuple(obj, "iiiii(ii)", &msg.hwnd, &msg.message, &msg.wParam, &msg.lParam, &msg.time, &msg.pt.x, &msg.pt.y))
		return 0;
	WinEventToMacEvent(&msg, pe);
	return 1;
}
PyObject *PyMac_BuildEventRecord(EventRecord *) {return 0;} /* Convert EventRecord to PyObject */

int PyMac_GetFixed(PyObject *, Fixed *) {return 0;}	/* argument parser for Fixed */
PyObject *PyMac_BuildFixed(Fixed) {return 0;}			/* Convert Fixed to PyObject */
int PyMac_Getwide(PyObject *, wide *) {return 0;}		/* argument parser for wide */
PyObject *PyMac_Buildwide(wide *) {return 0;}			/* Convert wide to PyObject */

int PyMac_GetFSSpec(PyObject *, FSSpec *) {return 0;}

/* AE exports */
//extern PyObject *AEDesc_New(AppleEvent *) {return 0;} /* XXXX Why passed by address?? */
//extern int AEDesc_Convert(PyObject *, AppleEvent *) {return 0;}

/* Cm exports */
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
extern int MenuObj_Convert(PyObject *, MenuHandle *) {return 0;}

/* Qd exports */
extern PyObject *GrafObj_New(GrafPtr) {return 0;}
extern int GrafObj_Convert(PyObject *, GrafPtr *) {return 0;}
//extern PyObject *BMObj_New(BitMapPtr) {return 0;}
//extern int BMObj_Convert(PyObject *, BitMapPtr *) {return 0;}
extern PyObject *QdRGB_New(RGBColor *) {return 0;}
extern int QdRGB_Convert(PyObject *, RGBColor *) {return 0;}

/* Qdoffs exports */
//extern PyObject *GWorldObj_New(GWorldPtr) {return 0;}
extern int GWorldObj_Convert(PyObject *, GWorldPtr *) {return 0;}


/* Res exports */
extern PyObject *ResObj_New(Handle) {return 0;}
extern int ResObj_Convert(PyObject *, Handle *) {return 0;}
extern PyObject *OptResObj_New(Handle) {return 0;}
extern int OptResObj_Convert(PyObject *, Handle *) {return 0;}

/* TE exports */
//extern PyObject *TEObj_New(TEHandle) {return 0;}
//extern int TEObj_Convert(PyObject *, TEHandle *) {return 0;}

/* Win exports */
//extern PyObject *WinObj_New(WindowPtr) {return 0;}
extern int WinObj_Convert(PyObject *, WindowPtr *) {return 0;}
//extern PyObject *WinObj_WhichWindow(WindowPtr) {return 0;}
