
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "utils.h"

static PyObject *ErrorObject;

static void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}
static void seterror(const char *funcname, const char *msg)
	{
	PyErr_Format(ErrorObject, "%s failed, %s", funcname, msg);
	PyErr_SetString(ErrorObject, msg);
	}
static void seterror(const char *funcname, DWORD err)
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

////////////////////////////////////////
static char SetWorldTransform__doc__[] =
"sets a two-dimensional linear transformation between world space and page space "
;
static PyObject*
SetWorldTransform(PyObject *self, PyObject *args)
{
	HDC hdc;
	float tf[6];
	if (!PyArg_ParseTuple(args, "i(ffffff)", &hdc, &tf[0], &tf[1], &tf[2],&tf[3], &tf[4], &tf[5]))
		return NULL;
	BOOL res = SetWorldTransform(hdc, (XFORM*)tf);
	if(!res){
		seterror("SetWorldTransform", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GetWorldTransform__doc__[] =
"retrieves the current world-space to page-space transformation"
;
static PyObject*
GetWorldTransform(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	float tf[6];
	BOOL res = GetWorldTransform(hdc, (XFORM*)tf);
	if(!res){
		seterror("GetWorldTransform", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ffffff", tf[0], tf[1], tf[2], tf[3], tf[4], tf[5]);
}


static char SaveDC__doc__[] =
"saves the current state of the specified device context "
;
static PyObject*
SaveDC(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	int idSavedDC  = SaveDC(hdc);
	if(idSavedDC==0){
		seterror("SaveDC", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", idSavedDC);
}


static char RestoreDC__doc__[] =
"restores a device context (DC) to the specified state"
;
static PyObject*
RestoreDC(PyObject *self, PyObject *args)
{
	HDC hdc;
	int idSavedDC;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &idSavedDC))
		return NULL;
	BOOL res = RestoreDC(hdc, idSavedDC);
	if(!res){
		seterror("RestoreDC", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char SetGraphicsMode__doc__[] =
"sets the graphics mode for the specified device context"
;
static PyObject*
SetGraphicsMode(PyObject *self, PyObject *args)
{
	HDC hdc;
	int imode;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &imode))
		return NULL;
	int oldmode = SetGraphicsMode(hdc, imode);
	if(oldmode==0){
		seterror("SetGraphicsMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", oldmode);
}

static char SetMapMode__doc__[] =
"sets the mapping mode of the specified device context"
;
static PyObject*
SetMapMode(PyObject *self, PyObject *args)
{
	HDC hdc;
	int fnMapMode;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &fnMapMode))
		return NULL;
	int fnOldMapMode = SetMapMode(hdc, fnMapMode);
	if(fnOldMapMode==0){
		seterror("SetMapMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fnOldMapMode);
}

static char SetViewportExtEx__doc__[] =
"sets the horizontal and vertical extents of the viewport"
;
static PyObject*
SetViewportExtEx(PyObject *self, PyObject *args)
{
	HDC hdc;
	SIZE s;
	if (!PyArg_ParseTuple(args, "i(ii)", &hdc, &s.cx, &s.cy))
		return NULL;
	SIZE sold;
	BOOL res = SetViewportExtEx(hdc, s.cx, s.cy, &sold);
	if(!res){
		seterror("SetViewportExtEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", sold.cx, sold.cy);
}

static char GetViewportExtEx__doc__[] =
"retrieves the x-extent and y-extent of the current viewport"
;
static PyObject*
GetViewportExtEx(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	SIZE s;
	BOOL res = GetViewportExtEx(hdc, &s);
	if(!res){
		seterror("GetViewportExtEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", s.cx, s.cy);
}


static char SetViewportOrgEx__doc__[] =
"specifies which device point maps to the window origin (0,0)"
;
static PyObject*
SetViewportOrgEx(PyObject *self, PyObject *args)
{
	HDC hdc;
	POINT pt;
	if (!PyArg_ParseTuple(args, "i(ii)", &hdc, &pt.x, &pt.y))
		return NULL;
	POINT ptold;
	BOOL res = SetViewportOrgEx(hdc, pt.x, pt.y, &ptold);
	if(!res){
		seterror("SetViewportOrgEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", ptold.x, ptold.y);
}


static char SetROP2__doc__[] =
"sets the current foreground mix mode"
;
static PyObject*
SetROP2(PyObject *self, PyObject *args)
{
	HDC hdc;
	int fnDrawMode;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &fnDrawMode))
		return NULL;
	int fnOldDrawMode = SetROP2(hdc, fnDrawMode);
	if(fnOldDrawMode==0){
		seterror("SetROP2", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fnOldDrawMode);
}

static char GetROP2__doc__[] =
"gets the current foreground mix mode"
;
static PyObject*
GetROP2(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	int fnDrawMode = GetROP2(hdc);
	if(fnDrawMode==0){
		seterror("GetROP2", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fnDrawMode);
}

static char SetBkMode__doc__[] =
"sets the background mix mode of the specified device context"
;
static PyObject*
SetBkMode(PyObject *self, PyObject *args)
{
	HDC hdc;
	int iBkMode;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &iBkMode))
		return NULL;
	int iOldBkMode = SetBkMode(hdc, iBkMode);
	if(iOldBkMode==0){
		seterror("SetBkMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", iOldBkMode);
}

static char GetBkMode__doc__[] =
"returns the current background mix mode"
;
static PyObject*
GetBkMode(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	int iBkMode = GetBkMode(hdc);
	if(iBkMode==0){
		seterror("GetBkMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", iBkMode);
}

static char SetTextAlign__doc__[] =
"sets the text-alignment flags for the specified device context"
;
static PyObject*
SetTextAlign(PyObject *self, PyObject *args)
{
	HDC hdc;
	UINT fMode;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &fMode))
		return NULL;
	int fOldMode = SetTextAlign(hdc, fMode);
	if(fOldMode==GDI_ERROR){
		seterror("SetTextAlign", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fOldMode);
}

static char SetTextColor__doc__[] =
"sets the text color for the specified device context to the specified color"
;
static PyObject*
SetTextColor(PyObject *self, PyObject *args)
{
	HDC hdc;
	int r, g, b;
	if (!PyArg_ParseTuple(args, "i(iii)", &hdc, &r, &g, &b))
		return NULL;
	COLORREF crColor = RGB(r,g,b);
	COLORREF crOldColor = SetTextColor(hdc, crColor);
	if(crOldColor==CLR_INVALID){
		seterror("SetTextColor", GetLastError());
		return NULL;
		}
	return Py_BuildValue("iii", GetRValue(crOldColor),GetGValue(crOldColor),GetBValue(crOldColor));
}

static char SetPolyFillMode__doc__[] =
"sets the polygon fill mode for functions that fill polygons"
;
static PyObject*
SetPolyFillMode(PyObject *self, PyObject *args)
{
	HDC hdc;
	UINT fMode;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &fMode))
		return NULL;
	int fOldMode = SetPolyFillMode(hdc, fMode);
	if(!fOldMode){
		seterror("SetPolyFillMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fOldMode);
}

static char SetArcDirection__doc__[] =
"sets the drawing direction to be used for arc and rectangle functions"
;
static PyObject*
SetArcDirection(PyObject *self, PyObject *args)
{
	HDC hdc;
	int direction;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &direction))
		return NULL;
	int oldDirection = SetArcDirection(hdc, direction);
	if(!oldDirection){
		seterror("SetArcDirection", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", oldDirection);
}

static char GetDeviceCaps__doc__[] =
"retrieves device-specific information for the specified device"
;
static PyObject*
GetDeviceCaps(PyObject *self, PyObject *args)
{
	HDC hdc;
	int nIndex;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &nIndex))
		return NULL;
	int caps = GetDeviceCaps(hdc, nIndex);
	return Py_BuildValue("i", caps);
}

////////////////////////////////////////
// Path

static char BeginPath__doc__[] =
"opens a path bracket in the specified device context"
;
static PyObject*
BeginPath(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	BOOL res = BeginPath(hdc);
	if(!res){
		seterror("BeginPath", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char EndPath__doc__[] =
"closes a path bracket and selects the path defined by the bracket into the specified device context"
;
static PyObject*
EndPath(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	BOOL res = EndPath(hdc);
	if(!res){
		seterror("EndPath", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char StrokePath__doc__[] =
"renders the specified path by using the current pen"
;
static PyObject*
StrokePath(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	BOOL res = StrokePath(hdc);
	if(!res){
		seterror("StrokePath", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char FillPath__doc__[] =
"Closes any open figures in the current path and fills the path's interior by using the current brush and polygon-filling mode."
;
static PyObject*
FillPath(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	BOOL res = FillPath(hdc);
	if(!res){
		seterror("FillPath", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char StrokeAndFillPath__doc__[] =
"closes any open figures in a path, strokes the outline of the path by using the current pen, and fills its interior by using the current brush."
;
static PyObject*
StrokeAndFillPath(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	BOOL res = StrokeAndFillPath(hdc);
	if(!res){
		seterror("StrokeAndFillPath", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char CloseFigure__doc__[] =
"closes an open figure in a path"
;
static PyObject*
CloseFigure(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	BOOL res = CloseFigure(hdc);
	if(!res){
		seterror("CloseFigure", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char FlattenPath__doc__[] =
"transforms any curves into a sequence of lines."
;
static PyObject*
FlattenPath(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	BOOL res = FlattenPath(hdc);
	if(!res){
		seterror("FlattenPath", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GetPath__doc__[] =
"retrieves the coordinates defining the endpoints of lines and the control points of curves"
;
static PyObject*
GetPath(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;

	// how many points are in the path?
	int npoints = GetPath(hdc, NULL, NULL, 0);

	// get points ...
	//POINT *pPoints = NULL;  // path vertices
	//BYTE *pTypes = NULL;    // array of path vertex types
	//npoints = GetPath(hdc, NULL, NULL, 0);

	if(npoints<0){
		seterror("GetPath", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", npoints);
}

////////////////////////////////////////
// Draw

static char MoveToEx__doc__[] =
"updates the current position to the specified point and returns the previous position"
;
static PyObject*
MoveToEx(PyObject *self, PyObject *args)
{
	HDC hdc;
	int x, y;
	if (!PyArg_ParseTuple(args, "i(ii)", &hdc, &x, &y))
		return NULL;
	POINT pt;
	BOOL res = MoveToEx(hdc, x, y, &pt);
	if(!res){
		seterror("MoveToEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", pt.x, pt.y);
}



static char Rectangle__doc__[] =
"Draws a rectangle. The rectangle is outlined by using the current pen and filled by using the current brush"
;
static PyObject*
Rectangle(PyObject *self, PyObject *args)
{
	HDC hdc;
	int l, t, r, b;
	if (!PyArg_ParseTuple(args, "i(iiii)", &hdc, &l, &t, &r,&b))
		return NULL;
	BOOL res = Rectangle(hdc, l, t, r, b);
	if(!res){
		seterror("Rectangle", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char RoundRect__doc__[] =
"Draws a rectangle with rounded corners. The rectangle is outlined by using the current pen and filled by using the current brush."
;
static PyObject*
RoundRect(PyObject *self, PyObject *args)
{
	HDC hdc;
	int l, t, r, b, w, h;
	if (!PyArg_ParseTuple(args, "i(iiii)(ii)", &hdc, &l, &t, &r,&b, &w, &h))
		return NULL;
	BOOL res = RoundRect(hdc, l, t, r, b, w, h);
	if(!res){
		seterror("RoundRect", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char Ellipse__doc__[] =
"Draws an ellipse. The center of the ellipse is the center of the specified bounding rectangle"
;
static PyObject*
Ellipse(PyObject *self, PyObject *args)
{
	HDC hdc;
	int l, t, r, b;
	if (!PyArg_ParseTuple(args, "i(iiii)", &hdc, &l, &t, &r,&b))
		return NULL;
	BOOL res = Ellipse(hdc, l, t, r, b);
	if(!res){
		seterror("Ellipse", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char ArcTo__doc__[] =
"draws an elliptical arc"
;
static PyObject*
ArcTo(PyObject *self, PyObject *args)
{
	HDC hdc;
	RECT rc;
	POINT pt1, pt2;
	if (!PyArg_ParseTuple(args, "i(iiii)(ii)(ii)", &hdc, &rc.left, &rc.top, &rc.right, &rc.bottom,
			&pt1.x, &pt1.y, &pt2.x, &pt2.y))
		return NULL;
	BOOL res = ArcTo(hdc, rc.left, rc.top, rc.right, rc.bottom, pt1.x, pt1.y, pt2.x, pt2.y);
	if(!res){
		seterror("ArcTo", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char Arc__doc__[] =
"draws an elliptical arc"
;
static PyObject*
Arc(PyObject *self, PyObject *args)
{
	HDC hdc;
	RECT rc;
	POINT pt1, pt2;
	if (!PyArg_ParseTuple(args, "i(iiii)(ii)(ii)", &hdc, &rc.left, &rc.top, &rc.right, &rc.bottom,
			&pt1.x, &pt1.y, &pt2.x, &pt2.y))
		return NULL;
	BOOL res = Arc(hdc, rc.left, rc.top, rc.right, rc.bottom, pt1.x, pt1.y, pt2.x, pt2.y);
	if(!res){
		seterror("Arc", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char LineTo__doc__[] =
"draws a line from the current position up to, but not including, the specified point"
;
static PyObject*
LineTo(PyObject *self, PyObject *args)
{
	HDC hdc;
	int x, y;
	if (!PyArg_ParseTuple(args, "i(ii)", &hdc, &x, &y))
		return NULL;
	BOOL res = LineTo(hdc, x, y);
	if(!res){
		seterror("LineTo", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char Polyline__doc__[] =
"draws a series of line segments by connecting the points in the specified array"
;
static PyObject*
Polyline(PyObject *self, PyObject *args)
{
	HDC hdc;
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "iO", &hdc, &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist))
		{
		seterror("Polyline", "Invalid point list");
		return NULL;
		}
	BOOL res = Polyline(hdc, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("Polyline", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char PolylineTo__doc__[] =
"draws one or more straight lines"
;
static PyObject*
PolylineTo(PyObject *self, PyObject *args)
{
	HDC hdc;
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "iO", &hdc, &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist))
		{
		seterror("PolylineTo", "Invalid point list");
		return NULL;
		}
	BOOL res = PolylineTo(hdc, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("Polyline", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}


static char Polygon__doc__[] =
"draws a polygon consisting of two or more vertices connected by straight lines"
;
static PyObject*
Polygon(PyObject *self, PyObject *args)
{
	HDC hdc;
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "iO", &hdc, &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist)){
		seterror("Polygon", "Invalid point list");
		return NULL;
		}
	BOOL res = Polygon(hdc, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("Polygon", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}


static char PolyBezier__doc__[] =
"draws one or more Bezier curves"
;
static PyObject*
PolyBezier(PyObject *self, PyObject *args)
{
	HDC hdc;
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "iO", &hdc, &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist)){
		seterror("PolyBezier", "Invalid point list");
		return NULL;
		}
	BOOL res = PolyBezier(hdc, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("PolyBezier", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char PolyBezierTo__doc__[] =
"draws one or more Bezier curves"
;
static PyObject*
PolyBezierTo(PyObject *self, PyObject *args)
{
	HDC hdc;
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "iO", &hdc, &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist)){
		char sz[80];
		sprintf(sz,"Invalid point list (n=%d) %s", conv.getSize(), conv.getErrorStr());
		seterror("PolyBezierTo", sz);
		return NULL;
		}
	BOOL res = PolyBezierTo(hdc, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("PolyBezierTo", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char PolyDraw__doc__[] =
"draws a set of line segments and Bezier curves"
;
static PyObject*
PolyDraw(PyObject *self, PyObject *args)
{
	HDC hdc;
	PyObject *pyptlist;
	PyObject *pyintlist;
	if (!PyArg_ParseTuple(args, "iOO", &hdc, &pyptlist, &pyintlist))
		return NULL;
	PyPtListConverter ptconv;
	if(!ptconv.convert(pyptlist)){
		seterror("PolyDraw", "Invalid point list");
		return NULL;
		}
	PyIntListConverter intconv;
	if(!intconv.convert(pyintlist) || intconv.getSize()!=ptconv.getSize()){
		seterror("PolyDraw", "Invalid points type list");
		return NULL;
		}

	BOOL res = PolyDraw(hdc, ptconv.getPoints(), intconv.packInts(), ptconv.getSize());
	if(!res){
		seterror("PolyDraw", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char TextOut__doc__[] =
"writes a character string at the specified location"
;
static PyObject*
TextOut(PyObject *self, PyObject *args)
{
	HDC hdc;
	int x, y;
	PyObject *pystr;
	if (!PyArg_ParseTuple(args, "i(ii)O", &hdc, &x, &y, &pystr))
		return NULL;
	int cbstr = PyString_GET_SIZE(pystr);
	const char *pstr = PyString_AS_STRING(pystr);
	BOOL res = TextOut(hdc, x, y, pstr, cbstr);
	if(!res){
		seterror("TextOut", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

//////////////////
static char SelectObject__doc__[] =
"selects an object into the specified device context"
;
static PyObject*
SelectObject(PyObject *self, PyObject *args)
{
	HDC hdc;
	HGDIOBJ hgdiobj;
	if (!PyArg_ParseTuple(args, "ii", &hdc, &hgdiobj))
		return NULL;
	HGDIOBJ holdgdiobj = SelectObject(hdc, hgdiobj);
	return Py_BuildValue("i", holdgdiobj);
}

static char DeleteObject__doc__[] =
"deletes a GDI object"
;
static PyObject*
DeleteObject(PyObject *self, PyObject *args)
{
	HGDIOBJ hgdiobj;
	if (!PyArg_ParseTuple(args, "i", &hgdiobj))
		return NULL;
	BOOL res = DeleteObject(hgdiobj);
	if(!res){
		seterror("DeleteObject", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

static char GetStockObject__doc__[] =
"retrieves a handle to one of the stock pens, brushes, fonts, or palettes"
;
static PyObject*
GetStockObject(PyObject *self, PyObject *args)
{
	int gdiobjtype;
	if (!PyArg_ParseTuple(args, "i", &gdiobjtype))
		return NULL;
	HGDIOBJ hgdiobj = GetStockObject(gdiobjtype);
	if(!hgdiobj){
		seterror("GetStockObject", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hgdiobj);
}

static char ExtCreatePen__doc__[] =
"creates a logical cosmetic or geometric pen that has the specified style, width, and brush attributes"
;
static PyObject*
ExtCreatePen(PyObject *self, PyObject *args)
{
	DWORD dwPenStyle = PS_GEOMETRIC | PS_SOLID | PS_ENDCAP_FLAT;
	DWORD dwWidth;
	LOGBRUSH lb = {BS_SOLID, 0, 0};
	DWORD dwStyleCount = 0;    // length of custom style array
	DWORD *lpStyle =NULL;  // custom style array

	int r, g, b;
	if (!PyArg_ParseTuple(args, "i(iii)", &dwWidth, &r,&g,&b))
		return NULL;
	lb.lbColor = RGB(r, g, b);
	HPEN hpen = ExtCreatePen(dwPenStyle, dwWidth, &lb, dwStyleCount, lpStyle);
	if(hpen==0){
		seterror("ExtCreatePen", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hpen);
}

static char CreateSolidBrush__doc__[] =
"creates a logical brush that has the specified solid color"
;
static PyObject*
CreateSolidBrush(PyObject *self, PyObject *args)
{
	int r, g, b;
	if (!PyArg_ParseTuple(args, "(iii)", &r,&g,&b))
		return NULL;
	COLORREF crColor = RGB(r, g, b);
	HBRUSH hbrush = CreateSolidBrush(crColor);
	if(!hbrush){
		seterror("CreateSolidBrush", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hbrush);
}

static char CreateBrushIndirect__doc__[] =
"creates a logical brush that has the specified style, color, and pattern"
;
static PyObject*
CreateBrushIndirect(PyObject *self, PyObject *args)
{
	LOGBRUSH lb = {BS_SOLID, 0, 0};
	int r, g, b;
	if (!PyArg_ParseTuple(args, "(iii)", &r,&g,&b))
		return NULL;
	lb.lbColor = RGB(r, g, b);
	HBRUSH hbrush = CreateBrushIndirect(&lb);
	if(hbrush==0){
		seterror("CreateBrushIndirect", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hbrush);
}

static char CreateFontIndirect__doc__[] =
"creates a logical font that has the characteristics specified in the dictionary"
;
static PyObject*
CreateFontIndirect(PyObject *self, PyObject *args)
{
	PyObject *pydict;
	if (!PyArg_ParseTuple(args, "O", &pydict))
		return NULL;
	PyDictParser p(pydict);
	LOGFONT s;
	memset(&s, 0, sizeof(LOGFONT));
	s.lfHeight = -p.getIntAttr("height"); 
	s.lfWidth = p.getIntAttr("width");
	s.lfEscapement = p.getIntAttr("escapement");
	s.lfOrientation = p.getIntAttr("orientation"); 
	s.lfWeight = p.getIntAttr("weight");
	s.lfItalic = (BYTE)p.getIntAttr("italic"); 
	s.lfUnderline = (BYTE)p.getIntAttr("underline");
	s.lfStrikeOut = (BYTE)p.getIntAttr("strikeout"); 
	s.lfCharSet = (BYTE)p.getIntAttr("charset", DEFAULT_CHARSET);
	s.lfOutPrecision = (BYTE)p.getIntAttr("outprecision", OUT_DEFAULT_PRECIS); 
	s.lfClipPrecision =(BYTE) p.getIntAttr("clipprecision", CLIP_DEFAULT_PRECIS);
	s.lfQuality = (BYTE)p.getIntAttr("quality", PROOF_QUALITY);
	s.lfPitchAndFamily = (BYTE)p.getIntAttr("pitch and family", DEFAULT_PITCH | FF_DONTCARE); // naming compatibility
	p.getStrAttr("name", s.lfFaceName, LF_FACESIZE, "Arial");  //  naming compatibility
	HFONT hfont = CreateFontIndirect(&s);
	if(hfont==0){
		seterror("CreateFontIndirect", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hfont);
}

static struct PyMethodDef wingdi_methods[] = {
	{"SetWorldTransform", (PyCFunction)SetWorldTransform, METH_VARARGS, SetWorldTransform__doc__},
	{"GetWorldTransform", (PyCFunction)GetWorldTransform, METH_VARARGS, GetWorldTransform__doc__},
	{"SaveDC", (PyCFunction)SaveDC, METH_VARARGS, SaveDC__doc__},
	{"RestoreDC", (PyCFunction)RestoreDC, METH_VARARGS, RestoreDC__doc__},
	{"SetGraphicsMode", (PyCFunction)SetGraphicsMode, METH_VARARGS, SetGraphicsMode__doc__},
	{"SetMapMode", (PyCFunction)SetMapMode, METH_VARARGS, SetMapMode__doc__},
	{"SetViewportExtEx", (PyCFunction)SetViewportExtEx, METH_VARARGS, SetViewportExtEx__doc__},
	{"GetViewportExtEx", (PyCFunction)GetViewportExtEx, METH_VARARGS, GetViewportExtEx__doc__},
	{"SetViewportOrgEx", (PyCFunction)SetViewportOrgEx, METH_VARARGS, SetViewportOrgEx__doc__},
	{"SetROP2", (PyCFunction)SetROP2, METH_VARARGS, SetROP2__doc__},
	{"GetROP2", (PyCFunction)GetROP2, METH_VARARGS, GetROP2__doc__},
	{"SetBkMode", (PyCFunction)SetBkMode, METH_VARARGS, SetBkMode__doc__},
	{"GetBkMode", (PyCFunction)GetBkMode, METH_VARARGS, GetBkMode__doc__},
	{"SetTextAlign", (PyCFunction)SetTextAlign, METH_VARARGS, SetTextAlign__doc__},
	{"SetTextColor", (PyCFunction)SetTextColor, METH_VARARGS, SetTextColor__doc__},
	{"SetPolyFillMode", (PyCFunction)SetPolyFillMode, METH_VARARGS, SetPolyFillMode__doc__},
	{"SetArcDirection", (PyCFunction)SetArcDirection, METH_VARARGS, SetArcDirection__doc__},
	{"GetDeviceCaps", (PyCFunction)GetDeviceCaps, METH_VARARGS, GetDeviceCaps__doc__},

	{"BeginPath", (PyCFunction)BeginPath, METH_VARARGS, BeginPath__doc__},
	{"EndPath", (PyCFunction)EndPath, METH_VARARGS, EndPath__doc__},
	{"StrokePath", (PyCFunction)StrokePath, METH_VARARGS, StrokePath__doc__},
	{"FillPath", (PyCFunction)FillPath, METH_VARARGS, FillPath__doc__},
	{"StrokeAndFillPath", (PyCFunction)StrokeAndFillPath, METH_VARARGS, StrokeAndFillPath__doc__},
	{"CloseFigure", (PyCFunction)CloseFigure, METH_VARARGS, CloseFigure__doc__},
	{"FlattenPath", (PyCFunction)FlattenPath, METH_VARARGS, FlattenPath__doc__},
	{"GetPath", (PyCFunction)GetPath, METH_VARARGS, GetPath__doc__},

	{"MoveToEx", (PyCFunction)MoveToEx, METH_VARARGS, MoveToEx__doc__},
	{"Rectangle", (PyCFunction)Rectangle, METH_VARARGS, Rectangle__doc__},
	{"RoundRect", (PyCFunction)RoundRect, METH_VARARGS, RoundRect__doc__},
	{"Ellipse", (PyCFunction)Ellipse, METH_VARARGS, Ellipse__doc__},
	{"ArcTo", (PyCFunction)ArcTo, METH_VARARGS, ArcTo__doc__},
	{"Arc", (PyCFunction)Arc, METH_VARARGS, Arc__doc__},
	{"LineTo", (PyCFunction)LineTo, METH_VARARGS, LineTo__doc__},
	{"Polyline", (PyCFunction)Polyline, METH_VARARGS, Polyline__doc__},
	{"PolylineTo", (PyCFunction)PolylineTo, METH_VARARGS, PolylineTo__doc__},
	{"Polygon", (PyCFunction)Polygon, METH_VARARGS, Polygon__doc__},
	{"PolyBezier", (PyCFunction)PolyBezier, METH_VARARGS, PolyBezier__doc__},
	{"PolyBezierTo", (PyCFunction)PolyBezierTo, METH_VARARGS, PolyBezierTo__doc__},
	{"PolyDraw", (PyCFunction)PolyDraw, METH_VARARGS, PolyDraw__doc__},
	{"TextOut", (PyCFunction)TextOut, METH_VARARGS, TextOut__doc__},

	{"SelectObject", (PyCFunction)SelectObject, METH_VARARGS, SelectObject__doc__},
	{"DeleteObject", (PyCFunction)DeleteObject, METH_VARARGS, DeleteObject__doc__},

	{"GetStockObject", (PyCFunction)GetStockObject, METH_VARARGS, GetStockObject__doc__},
	{"ExtCreatePen", (PyCFunction)ExtCreatePen, METH_VARARGS, ExtCreatePen__doc__},
	{"CreateSolidBrush", (PyCFunction)CreateSolidBrush, METH_VARARGS, CreateSolidBrush__doc__},
	{"CreateBrushIndirect", (PyCFunction)CreateBrushIndirect, METH_VARARGS, CreateBrushIndirect__doc__},
	{"CreateFontIndirect", (PyCFunction)CreateFontIndirect, METH_VARARGS, CreateFontIndirect__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


/////////////////////////////////////
static char wingdi_module_documentation[] =
"Windows GDI module"
;

extern "C" __declspec(dllexport)
void initwingdi()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("wingdi", wingdi_methods,
		wingdi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("wingdi.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module wingdi");
}
