#include "Python.h"

#include "macglue.h"
#include "pymactoolbox.h"

PyObject *PyMac_GetOSErrException(void){return 0;}	/* Initialize & return it */
PyObject *PyErr_Mac(PyObject *, int){return 0;}		/* Exception with a mac error */
PyObject *PyMac_Error(OSErr){return 0;}				/* Uses PyMac_GetOSErrException */


/*
** These conversion routines are defined in mactoolboxglue.c itself.
*/
int PyMac_GetOSType(PyObject *, OSType *) {return 0;}	/* argument parser for OSType */
PyObject *PyMac_BuildOSType(OSType) {return 0;}		/* Convert OSType to PyObject */

PyObject *PyMac_BuildNumVersion(NumVersion) {return 0;}/* Convert NumVersion to PyObject */

int PyMac_GetStr255(PyObject *, Str255) {return 0;}	/* argument parser for Str255 */
PyObject *PyMac_BuildStr255(Str255) {return 0;}		/* Convert Str255 to PyObject */
PyObject *PyMac_BuildOptStr255(Str255) {return 0;}		/* Convert Str255 to PyObject, NULL to None */

int PyMac_GetRect(PyObject *, Rect *) {return 0;}		/* argument parser for Rect */
PyObject *PyMac_BuildRect(Rect *) {return 0;}			/* Convert Rect to PyObject */

int PyMac_GetPoint(PyObject *, Point *) {return 0;}	/* argument parser for Point */
PyObject *PyMac_BuildPoint(Point) {return 0;}			/* Convert Point to PyObject */

int PyMac_GetEventRecord(PyObject *, EventRecord *) {return 0;} /* argument parser for EventRecord */
PyObject *PyMac_BuildEventRecord(EventRecord *) {return 0;} /* Convert EventRecord to PyObject */

int PyMac_GetFixed(PyObject *, Fixed *) {return 0;}	/* argument parser for Fixed */
PyObject *PyMac_BuildFixed(Fixed) {return 0;}			/* Convert Fixed to PyObject */
int PyMac_Getwide(PyObject *, wide *) {return 0;}		/* argument parser for wide */
PyObject *PyMac_Buildwide(wide *) {return 0;}			/* Convert wide to PyObject */

/*
** The rest of the routines are implemented by extension modules. If they are
** dynamically loaded mactoolboxglue will contain a stub implementation of the
** routine, which imports the module, whereupon the module's init routine will
** communicate the routine pointer back to the stub.
** If USE_TOOLBOX_OBJECT_GLUE is not defined there is no glue code, and the
** extension modules simply declare the routine. This is the case for static
** builds (and could be the case for MacPython CFM builds, because CFM extension
** modules can reference each other without problems).
*/

#ifdef USE_TOOLBOX_OBJECT_GLUE
/*
** These macros are used in the module init code. If we use toolbox object glue
** it sets the function pointer to point to the real function.
*/
#define PyMac_INIT_TOOLBOX_OBJECT_NEW(object, rtn) { \
	extern PyObject *(*PyMacGluePtr_##rtn)(object); \
	PyMacGluePtr_##rtn = _##rtn; \
}
#define PyMac_INIT_TOOLBOX_OBJECT_CONVERT(object, rtn) { \
	extern int (*PyMacGluePtr_##rtn)(PyObject *, object *); \
	PyMacGluePtr_##rtn = _##rtn; \
}
#else
/*
** If we don't use toolbox object glue the init macros are empty. Moreover, we define
** _xxx_New to be the same as xxx_New, and the code in mactoolboxglue isn't included.
*/
#define PyMac_INIT_TOOLBOX_OBJECT_NEW(object, rtn)
#define PyMac_INIT_TOOLBOX_OBJECT_CONVERT(object, rtn)
#endif /* USE_TOOLBOX_OBJECT_GLUE */

/* macfs exports */
extern int PyMac_GetFSSpec(PyObject *, FSSpec *) {return 0;}

/* AE exports */
extern PyObject *AEDesc_New(AppleEvent *) {return 0;} /* XXXX Why passed by address?? */
extern int AEDesc_Convert(PyObject *, AppleEvent *) {return 0;}

/* Cm exports */
extern PyObject *CmpObj_New(Component) {return 0;}
extern int CmpObj_Convert(PyObject *, Component *) {return 0;}
extern PyObject *CmpInstObj_New(ComponentInstance) {return 0;}
extern int CmpInstObj_Convert(PyObject *, ComponentInstance *) {return 0;}

/* Ctl exports */
extern PyObject *CtlObj_New(ControlHandle) {return 0;}
extern int CtlObj_Convert(PyObject *, ControlHandle *) {return 0;}

/* Dlg exports */
extern PyObject *DlgObj_New(DialogPtr) {return 0;}
extern int DlgObj_Convert(PyObject *, DialogPtr *) {return 0;}
extern PyObject *DlgObj_WhichDialog(DialogPtr) {return 0;}

/* Drag exports */
extern PyObject *DragObj_New(DragReference) {return 0;}
extern int DragObj_Convert(PyObject *, DragReference *) {return 0;}

/* List exports */
extern PyObject *ListObj_New(ListHandle) {return 0;}
extern int ListObj_Convert(PyObject *, ListHandle *) {return 0;}

/* Menu exports */
extern PyObject *MenuObj_New(MenuHandle) {return 0;}
extern int MenuObj_Convert(PyObject *, MenuHandle *) {return 0;}

/* Qd exports */
extern PyObject *GrafObj_New(GrafPtr) {return 0;}
extern int GrafObj_Convert(PyObject *, GrafPtr *) {return 0;}
extern PyObject *BMObj_New(BitMapPtr) {return 0;}
extern int BMObj_Convert(PyObject *, BitMapPtr *) {return 0;}
extern PyObject *QdRGB_New(RGBColor *) {return 0;}
extern int QdRGB_Convert(PyObject *, RGBColor *) {return 0;}

/* Qdoffs exports */
extern PyObject *GWorldObj_New(GWorldPtr) {return 0;}
extern int GWorldObj_Convert(PyObject *, GWorldPtr *) {return 0;}


/* Res exports */
extern PyObject *ResObj_New(Handle) {return 0;}
extern int ResObj_Convert(PyObject *, Handle *) {return 0;}
extern PyObject *OptResObj_New(Handle) {return 0;}
extern int OptResObj_Convert(PyObject *, Handle *) {return 0;}

/* TE exports */
extern PyObject *TEObj_New(TEHandle) {return 0;}
extern int TEObj_Convert(PyObject *, TEHandle *) {return 0;}

/* Win exports */
extern PyObject *WinObj_New(WindowPtr) {return 0;}
extern int WinObj_Convert(PyObject *, WindowPtr *) {return 0;}
extern PyObject *WinObj_WhichWindow(WindowPtr) {return 0;}
