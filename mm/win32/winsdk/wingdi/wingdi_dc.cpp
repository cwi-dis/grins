
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "wingdi_dc.h"

#include "utils.h"

#include "wingdi_rgn.h"
#include "wingdi_bmp.h"

struct PyDC
	{
	PyObject_HEAD
	HDC m_hDC;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyDC *createInstance(HDC hDC=NULL)
		{
		PyDC *instance = PyObject_NEW(PyDC, &type);
		if (instance == NULL) return NULL;
		instance->m_hDC = hDC;
		return instance;
		}

	static void dealloc(PyDC *instance) 
		{ 
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyDC *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Wingdi_CreateDCFromHandle(PyObject *self, PyObject *args)
	{
	HDC hDC;
	if(!PyArg_ParseTuple(args, "i", &hDC))
		return NULL;
	return (PyObject*)PyDC::createInstance(hDC);
	}

PyObject* Wingdi_GetDesktopDC(PyObject *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return (PyObject*)PyDC::createInstance(GetDC(NULL));
	}

///////////////////////////////
// module

#ifndef _WIN32_WCE
static PyObject* PyDC_SetWorldTransform(PyDC *self, PyObject *args)
{
	float tf[6];
	if (!PyArg_ParseTuple(args, "(ffffff)",&tf[0], &tf[1], &tf[2],&tf[3], &tf[4], &tf[5]))
		return NULL;
	BOOL res = SetWorldTransform(self->m_hDC, (XFORM*)tf);
	if(!res){
		seterror("SetWorldTransform", GetLastError());
		return NULL;
		}
	return none();
}
#endif

#ifndef _WIN32_WCE
static PyObject* PyDC_GetWorldTransform(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	float tf[6];
	BOOL res = GetWorldTransform(self->m_hDC, (XFORM*)tf);
	if(!res){
		seterror("GetWorldTransform", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ffffff", tf[0], tf[1], tf[2], tf[3], tf[4], tf[5]);
}
#endif


static PyObject* PyDC_SaveDC(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	int idSavedDC  = SaveDC(self->m_hDC);
	if(idSavedDC==0){
		seterror("SaveDC", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", idSavedDC);
}


static PyObject* PyDC_RestoreDC(PyDC *self, PyObject *args)
{
	int idSavedDC;
	if (!PyArg_ParseTuple(args, "i", &idSavedDC))
		return NULL;
	BOOL res = RestoreDC(self->m_hDC, idSavedDC);
	if(!res){
		seterror("RestoreDC", GetLastError());
		return NULL;
		}
	return none();
}

#ifndef _WIN32_WCE
static PyObject* PyDC_SetGraphicsMode(PyDC *self, PyObject *args)
{
	int imode;
	if (!PyArg_ParseTuple(args, "i", &imode))
		return NULL;
	int oldmode = SetGraphicsMode(self->m_hDC, imode);
	if(oldmode==0){
		seterror("SetGraphicsMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", oldmode);
}
#endif

#ifndef _WIN32_WCE
static PyObject* PyDC_SetMapMode(PyDC *self, PyObject *args)
{
	int fnMapMode;
	if (!PyArg_ParseTuple(args, "i", &fnMapMode))
		return NULL;
	int fnOldMapMode = SetMapMode(self->m_hDC, fnMapMode);
	if(fnOldMapMode==0){
		seterror("SetMapMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fnOldMapMode);
}
#endif

#ifndef _WIN32_WCE
static PyObject* PyDC_SetWindowExtEx(PyDC *self, PyObject *args)
{
	SIZE s;
	if (!PyArg_ParseTuple(args, "(ii)", &s.cx, &s.cy))
		return NULL;
	SIZE sold;
	BOOL res = SetWindowExtEx(self->m_hDC, s.cx, s.cy, &sold);
	if(!res){
		seterror("SetWindowExtEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", sold.cx, sold.cy);
}

static PyObject* PyDC_GetWindowExtEx(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	SIZE s;
	BOOL res = GetWindowExtEx(self->m_hDC, &s);
	if(!res){
		seterror("GetWindowExtEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", s.cx, s.cy);
}


static PyObject*
PyDC_SetViewportExtEx(PyDC *self, PyObject *args)
{
	SIZE s;
	if (!PyArg_ParseTuple(args, "(ii)", &s.cx, &s.cy))
		return NULL;
	SIZE sold;
	BOOL res = SetViewportExtEx(self->m_hDC, s.cx, s.cy, &sold);
	if(!res){
		seterror("SetViewportExtEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", sold.cx, sold.cy);
}

static PyObject*
PyDC_GetViewportExtEx(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	SIZE s;
	BOOL res = GetViewportExtEx(self->m_hDC, &s);
	if(!res){
		seterror("GetViewportExtEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", s.cx, s.cy);
}
#endif //_WIN32_WCE


static PyObject*
PyDC_SetViewportOrgEx(PyDC *self, PyObject *args)
{
	POINT pt;
	if (!PyArg_ParseTuple(args, "(ii)", &pt.x, &pt.y))
		return NULL;
	POINT ptold;
	BOOL res = SetViewportOrgEx(self->m_hDC, pt.x, pt.y, &ptold);
	if(!res){
		seterror("SetViewportOrgEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", ptold.x, ptold.y);
}

#ifndef _WIN32_WCE
static PyObject *
PyDC_SetWindowOrg(PyDC *self, PyObject *args)
{
	int x, y;
 	if(!PyArg_ParseTuple(args, "(ii)", &x, &y))
		return NULL;
	POINT pt;
	BOOL res = SetWindowOrgEx(self->m_hDC, x, y, &pt);
	if(!res){
		seterror("SetWindowExtEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue ("ii", pt.x, pt.y);
}

static PyObject *
PyDC_GetWindowOrg(PyDC *self, PyObject *args)
{ 	
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	POINT pt;
	BOOL res = GetWindowOrgEx(self->m_hDC, &pt);
	if(!res){
		seterror("GetWindowOrgEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", pt.x, pt.y);
}
#endif //_WIN32_WCE

static PyObject*
PyDC_SetROP2(PyDC *self, PyObject *args)
{
	int fnDrawMode;
	if (!PyArg_ParseTuple(args, "i", &fnDrawMode))
		return NULL;
	int fnOldDrawMode = SetROP2(self->m_hDC, fnDrawMode);
	if(fnOldDrawMode==0){
		seterror("SetROP2", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fnOldDrawMode);
}

#ifndef _WIN32_WCE
static PyObject*
PyDC_GetROP2(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	int fnDrawMode = GetROP2(self->m_hDC);
	if(fnDrawMode==0){
		seterror("GetROP2", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fnDrawMode);
}
#endif

static PyObject*
PyDC_SetBkMode(PyDC *self, PyObject *args)
{
	int iBkMode;
	if (!PyArg_ParseTuple(args, "i", &iBkMode))
		return NULL;
	int iOldBkMode = SetBkMode(self->m_hDC, iBkMode);
	if(iOldBkMode==0){
		seterror("SetBkMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", iOldBkMode);
}

static PyObject*
PyDC_GetBkMode(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	int iBkMode = GetBkMode(self->m_hDC);
	if(iBkMode==0){
		seterror("GetBkMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", iBkMode);
}

#ifndef _WIN32_WCE
static PyObject*
PyDC_SetTextAlign(PyDC *self, PyObject *args)
{
	UINT fMode;
	if (!PyArg_ParseTuple(args, "i", &fMode))
		return NULL;
	int fOldMode = SetTextAlign(self->m_hDC, fMode);
	if(fOldMode==GDI_ERROR){
		seterror("SetTextAlign", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fOldMode);
}
#endif

static PyObject*
PyDC_SetTextColor(PyDC *self, PyObject *args)
{
	int r, g, b;
	if (!PyArg_ParseTuple(args, "(iii)", &r, &g, &b))
		return NULL;
	COLORREF crColor = RGB(r,g,b);
	COLORREF crOldColor = SetTextColor(self->m_hDC, crColor);
	if(crOldColor==CLR_INVALID){
		seterror("SetTextColor", GetLastError());
		return NULL;
		}
	return Py_BuildValue("iii", GetRValue(crOldColor),GetGValue(crOldColor),GetBValue(crOldColor));
}

#ifndef _WIN32_WCE
static PyObject*
PyDC_SetPolyFillMode(PyDC *self, PyObject *args)
{
	UINT fMode;
	if (!PyArg_ParseTuple(args, "i", &fMode))
		return NULL;
	int fOldMode = SetPolyFillMode(self->m_hDC, fMode);
	if(!fOldMode){
		seterror("SetPolyFillMode", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", fOldMode);
}
#endif

#ifndef _WIN32_WCE
static PyObject*
PyDC_SetArcDirection(PyDC *self, PyObject *args)
{
	int direction;
	if (!PyArg_ParseTuple(args, "i", &direction))
		return NULL;
	int oldDirection = SetArcDirection(self->m_hDC, direction);
	if(!oldDirection){
		seterror("SetArcDirection", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", oldDirection);
}
#endif

static PyObject*
PyDC_GetDeviceCaps(PyDC *self, PyObject *args)
{
	int nIndex;
	if (!PyArg_ParseTuple(args, "i", &nIndex))
		return NULL;
	int caps = GetDeviceCaps(self->m_hDC, nIndex);
	return Py_BuildValue("i", caps);
}

#ifndef _WIN32_WCE
static PyObject*
PyDC_SetMiterLimit(PyDC *self, PyObject *args)
{
	float eNewLimit;
	if (!PyArg_ParseTuple(args, "f", &eNewLimit))
		return NULL;
	float eOldLimit;
	BOOL res = SetMiterLimit(self->m_hDC, eNewLimit, &eOldLimit);
	if(!res){
		seterror("SetMiterLimit", GetLastError());
		return NULL;
		}
	return Py_BuildValue("f", eOldLimit);
}
#endif

static PyObject* PyDC_GetTextMetrics(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	TEXTMETRIC tm;
	BOOL res = GetTextMetrics(self->m_hDC, &tm);
	if(!res)
		{
		seterror("GetTextMetrics", GetLastError());
		return NULL;
		}
	PyObject *d = PyDict_New();

	#define DICTADD(D,ST,M,TYPE) PyDict_SetItemString (D, #M, Py_BuildValue (TYPE, ST.M))
	DICTADD (d, tm, tmHeight, "i"); 
	DICTADD (d, tm, tmAscent, "i");
	DICTADD (d, tm, tmDescent, "i");
	DICTADD (d, tm, tmInternalLeading, "i");
	DICTADD (d, tm, tmExternalLeading, "i");
	DICTADD (d, tm, tmAveCharWidth, "i");
	DICTADD (d, tm, tmMaxCharWidth, "i");
	DICTADD (d, tm, tmWeight, "i");
	DICTADD (d, tm, tmItalic, "i");
	DICTADD (d, tm, tmUnderlined, "i");
	DICTADD (d, tm, tmStruckOut, "i");
	DICTADD (d, tm, tmFirstChar, "i");
	DICTADD (d, tm, tmLastChar, "i");
	DICTADD (d, tm, tmDefaultChar, "i");
	DICTADD (d, tm, tmBreakChar, "i");
	DICTADD (d, tm, tmPitchAndFamily, "i");
	DICTADD (d, tm, tmCharSet, "i");
	DICTADD (d, tm, tmOverhang, "i");
	DICTADD (d, tm, tmDigitizedAspectX, "i");
	DICTADD (d, tm, tmDigitizedAspectY, "i");
	#undef DICTADD

	return d;
}

static PyObject* PyDC_GetTextExtent(PyDC *self, PyObject *args)
{
	char *pString;
	int cbString;
	if (!PyArg_ParseTuple (args, "s#", &pString, &cbString))
	  return NULL;
	SIZE sz;
	BOOL res = GetTextExtentPoint32(self->m_hDC, TextPtr(pString), cbString, &sz);
	if(!res)
		{
		seterror("GetTextExtentPoint32", GetLastError());
		return NULL;
		}
	return Py_BuildValue ("(ii)", sz.cx, sz.cy);
}

////////////////////////////////////////
// Path

#ifndef _WIN32_WCE

static PyObject*
PyDC_BeginPath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = BeginPath(self->m_hDC);
	if(!res){
		seterror("BeginPath", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_EndPath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = EndPath(self->m_hDC);
	if(!res){
		seterror("EndPath", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_StrokePath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = StrokePath(self->m_hDC);
	if(!res){
		seterror("StrokePath", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_FillPath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = FillPath(self->m_hDC);
	if(!res){
		seterror("FillPath", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_StrokeAndFillPath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = StrokeAndFillPath(self->m_hDC);
	if(!res){
		seterror("StrokeAndFillPath", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_CloseFigure(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = CloseFigure(self->m_hDC);
	if(!res){
		seterror("CloseFigure", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_FlattenPath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = FlattenPath(self->m_hDC);
	if(!res){
		seterror("FlattenPath", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_WidenPath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = WidenPath(self->m_hDC);
	if(!res){
		seterror("WidenPath", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_GetPath(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	// how many points are in the path?
	int npoints = GetPath(self->m_hDC, NULL, NULL, 0);

	// get points ...
	//POINT *pPoints = NULL;  // path vertices
	//BYTE *pTypes = NULL;    // array of path vertex types
	//npoints = GetPath(self->m_hDC, NULL, NULL, 0);

	if(npoints<0){
		seterror("GetPath", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", npoints);
}

#endif // _WIN32_WCE

////////////////////////////////////////
// Draw

#ifndef _WIN32_WCE
static PyObject*
PyDC_MoveToEx(PyDC *self, PyObject *args)
{
	int x, y;
	if (!PyArg_ParseTuple(args, "(ii)", &x, &y))
		return NULL;
	POINT pt;
	BOOL res = MoveToEx(self->m_hDC, x, y, &pt);
	if(!res){
		seterror("MoveToEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("ii", pt.x, pt.y);
}
#endif

static PyObject*
PyDC_Rectangle(PyDC *self, PyObject *args)
{
	int l, t, r, b;
	if (!PyArg_ParseTuple(args, "(iiii)", &l, &t, &r,&b))
		return NULL;
	BOOL res = Rectangle(self->m_hDC, l, t, r, b);
	if(!res){
		seterror("Rectangle", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_RoundRect(PyDC *self, PyObject *args)
{
	int l, t, r, b, w, h;
	if (!PyArg_ParseTuple(args, "(iiii)(ii)", &l, &t, &r,&b, &w, &h))
		return NULL;
	BOOL res = RoundRect(self->m_hDC, l, t, r, b, w, h);
	if(!res){
		seterror("RoundRect", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_Ellipse(PyDC *self, PyObject *args)
{
	int l, t, r, b;
	if (!PyArg_ParseTuple(args, "(iiii)", &l, &t, &r,&b))
		return NULL;
	BOOL res = Ellipse(self->m_hDC, l, t, r, b);
	if(!res){
		seterror("Ellipse", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_FillSolidRect(PyDC *self, PyObject *args)
{
	RECT rect;
	COLORREF color;
	if(!PyArg_ParseTuple(args, "(iiii)i", 
			&rect.left, &rect.top, &rect.right, &rect.bottom, &color)) 
		return NULL;
	SetBkColor(self->m_hDC, color);
	ExtTextOut(self->m_hDC, 0, 0, ETO_OPAQUE, &rect, NULL, 0, NULL);
	return none();
}

#ifdef _WIN32_WCE
int wce_FrameRect(HDC hdc, const RECT* lprc, HBRUSH hbr)
{
  // Fill a "line-size" rectangle for each edge of the frame, using hbr
  // Note that right/bottom borders not painted by FillRect (or FrameRect)
  RECT rectEdge;	
  if (SetRect(&rectEdge, lprc->left, lprc->top, lprc->right, 
    lprc->top + 1) == FALSE) // Top edge of frame
    return FALSE;
  if (FillRect(hdc, &rectEdge, hbr) == FALSE)
    return FALSE;
  
  if (SetRect(&rectEdge, lprc->right - 1, lprc->top, lprc->right, 
    lprc->bottom) == FALSE) // Right edge of frame
    return FALSE;
  if (FillRect(hdc, &rectEdge, hbr) == FALSE)
    return FALSE;
  if (SetRect(&rectEdge, lprc->left, lprc->bottom - 1, lprc->right, 
    lprc->bottom) == FALSE) // Bottom edge of frame
    return FALSE;
  if (FillRect(hdc, &rectEdge, hbr) == FALSE)
    return FALSE;
  if (SetRect(&rectEdge, lprc->left, lprc->top, lprc->left + 1, 
    lprc->bottom) == FALSE) // Left edge of frame
    return FALSE;
  return FillRect(hdc, &rectEdge, hbr);
}
#endif

static PyObject*
PyDC_FrameRect(PyDC *self, PyObject *args)
{
	RECT rect;
	HBRUSH hbr;
	if(!PyArg_ParseTuple(args, "(iiii)i", 
			&rect.left, &rect.top, &rect.right, &rect.bottom, &hbr)) 
		return NULL;
#ifdef _WIN32_WCE
	wce_FrameRect(self->m_hDC, &rect, hbr);
#else
	FrameRect(self->m_hDC, &rect, hbr);
#endif
	return none();
}

#ifndef _WIN32_WCE
static PyObject*
PyDC_ArcTo(PyDC *self, PyObject *args)
{
	RECT rc;
	POINT pt1, pt2;
	if (!PyArg_ParseTuple(args, "(iiii)(ii)(ii)", &rc.left, &rc.top, &rc.right, &rc.bottom,
			&pt1.x, &pt1.y, &pt2.x, &pt2.y))
		return NULL;
	BOOL res = ArcTo(self->m_hDC, rc.left, rc.top, rc.right, rc.bottom, pt1.x, pt1.y, pt2.x, pt2.y);
	if(!res){
		seterror("ArcTo", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_Arc(PyDC *self, PyObject *args)
{
	RECT rc;
	POINT pt1, pt2;
	if (!PyArg_ParseTuple(args, "(iiii)(ii)(ii)", &rc.left, &rc.top, &rc.right, &rc.bottom,
			&pt1.x, &pt1.y, &pt2.x, &pt2.y))
		return NULL;
	BOOL res = Arc(self->m_hDC, rc.left, rc.top, rc.right, rc.bottom, pt1.x, pt1.y, pt2.x, pt2.y);
	if(!res){
		seterror("Arc", GetLastError());
		return NULL;
		}
	return none();
}
#endif

#ifndef _WIN32_WCE
static PyObject*
PyDC_LineTo(PyDC *self, PyObject *args)
{
	int x, y;
	if (!PyArg_ParseTuple(args, "(ii)", &x, &y))
		return NULL;
	BOOL res = LineTo(self->m_hDC, x, y);
	if(!res){
		seterror("LineTo", GetLastError());
		return NULL;
		}
	return none();
}
#endif

static PyObject*
PyDC_Polyline(PyDC *self, PyObject *args)
{
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "O", &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist))
		{
		seterror("Polyline", "Invalid point list");
		return NULL;
		}
	BOOL res = Polyline(self->m_hDC, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("Polyline", GetLastError());
		return NULL;
		}
	return none();
}

#ifndef _WIN32_WCE
static PyObject*
PyDC_PolylineTo(PyDC *self, PyObject *args)
{
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "O", &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist))
		{
		seterror("PolylineTo", "Invalid point list");
		return NULL;
		}
	BOOL res = PolylineTo(self->m_hDC, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("Polyline", GetLastError());
		return NULL;
		}
	return none();
}
#endif


static PyObject*
PyDC_Polygon(PyDC *self, PyObject *args)
{
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "O", &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist)){
		seterror("Polygon", "Invalid point list");
		return NULL;
		}
	BOOL res = Polygon(self->m_hDC, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("Polygon", GetLastError());
		return NULL;
		}
	return none();
}


#ifndef _WIN32_WCE
static PyObject*
PyDC_PolyBezier(PyDC *self, PyObject *args)
{
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "O", &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist)){
		seterror("PolyBezier", "Invalid point list");
		return NULL;
		}
	BOOL res = PolyBezier(self->m_hDC, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("PolyBezier", GetLastError());
		return NULL;
		}
	return none();
}
#endif

#ifndef _WIN32_WCE
static PyObject*
PyDC_PolyBezierTo(PyDC *self, PyObject *args)
{
	PyObject *pyptlist;
	if (!PyArg_ParseTuple(args, "O", &pyptlist))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist)){
		char sz[80];
		sprintf(sz,"Invalid point list (n=%d) %s", conv.getSize(), conv.getErrorStr());
		seterror("PolyBezierTo", sz);
		return NULL;
		}
	BOOL res = PolyBezierTo(self->m_hDC, conv.getPoints(), conv.getSize());
	if(!res){
		seterror("PolyBezierTo", GetLastError());
		return NULL;
		}
	return none();
}
#endif

#ifndef _WIN32_WCE
static PyObject*
PyDC_PolyDraw(PyDC *self, PyObject *args)
{
	PyObject *pyptlist;
	PyObject *pyintlist;
	if (!PyArg_ParseTuple(args, "OO", &pyptlist, &pyintlist))
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

	BOOL res = PolyDraw(self->m_hDC, ptconv.getPoints(), intconv.packInts(), ptconv.getSize());
	if(!res){
		seterror("PolyDraw", GetLastError());
		return NULL;
		}
	return none();
}
#endif

static PyObject*
PyDC_TextOut(PyDC *self, PyObject *args)
{
	int x, y;
	PyObject *pystr;
	if (!PyArg_ParseTuple(args, "(ii)O", &x, &y, &pystr))
		return NULL;
	int cbstr = PyString_GET_SIZE(pystr);
	char *pstr = PyString_AS_STRING(pystr);
#ifndef _WIN32_WCE
	BOOL res = TextOut(self->m_hDC, x, y, TextPtr(pstr), cbstr);
#else
	UINT fuOptions = ETO_OPAQUE;
	RECT *prc = NULL;
	int *pDx = NULL;
	BOOL res = ExtTextOut(self->m_hDC, x, y, fuOptions, prc, TextPtr(pstr), cbstr, pDx);
#endif
	if(!res){
		seterror("TextOut", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject*
PyDC_ExtTextOut(PyDC *self, PyObject *args)
{
	int x, y;
	PyObject *pystr;
	UINT fuOptions = ETO_OPAQUE;
	PyObject *rcobj = NULL;
	int *pDx = NULL;
	if (!PyArg_ParseTuple(args, "(ii)O|iO", &x, &y, &pystr, &fuOptions, &rcobj))
		return NULL;
	int cbstr = PyString_GET_SIZE(pystr);
	char *pstr = PyString_AS_STRING(pystr);
	RECT rc;
	RECT *prc = NULL;
	if(rcobj != NULL)
		{
		if(!PyArg_ParseTuple(rcobj, "iiii", &rc.left,  &rc.top,  &rc.right,&rc.bottom)) 
			{
			PyErr_Clear();
			seterror("ExtTextOut", "Argument not a rectangle");
			return NULL;
			}
		prc = &rc;
		}
	BOOL res = ExtTextOut(self->m_hDC, x, y, fuOptions, prc, TextPtr(pstr), cbstr, pDx);
	if(!res){
		seterror("TextOut", GetLastError());
		return NULL;
		}
	return none();
}


static PyObject*
PyDC_DrawText(PyDC *self, PyObject *args)
{
	char *str;
	RECT rc;
	UINT uFormat = DT_SINGLELINE | DT_CENTER | DT_VCENTER;
	if (!PyArg_ParseTuple(args, "s(iiii)|i", &str,
		&rc.left, &rc.top, &rc.right, &rc.bottom, &uFormat))
		return NULL;
	BOOL res = DrawText(self->m_hDC, TextPtr(str), -1, &rc, uFormat);
	if(!res){
		seterror("DrawText", GetLastError());
		return NULL;
		}
	return none();
}

//////////////////
static PyObject*
PyDC_SelectObject(PyDC *self, PyObject *args)
{
	PyObject *obj;;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	HGDIOBJ hgdiobj = (HGDIOBJ)GetGdiObjHandle(obj);
	HGDIOBJ holdgdiobj = SelectObject(self->m_hDC, hgdiobj);
	return Py_BuildValue("i", holdgdiobj);
}

static PyObject*
PyDC_SelectClipRgn(PyDC *self, PyObject *args)
{
	PyObject *rgn;
	if (!PyArg_ParseTuple(args, "O", &rgn))
		return NULL;
	int res = SelectClipRgn(self->m_hDC, (HRGN)GetGdiObjHandle(rgn));
	return Py_BuildValue("i", res);
}

#ifndef _WIN32_WCE
static PyObject*
PyDC_PaintRgn(PyDC *self, PyObject *args)
{
	PyObject *rgn;
	if (!PyArg_ParseTuple(args, "O", &rgn))
		return NULL;
	BOOL res = PaintRgn(self->m_hDC, (HRGN)GetGdiObjHandle(rgn));
	if(!res){
		seterror("PaintRgn", GetLastError());
		return NULL;
		}
	return none();
}
#endif

#ifndef _WIN32_WCE
static PyObject* 
PyDC_PathToRegion(PyDC *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRGN hRgn = PathToRegion(self->m_hDC);
	if(hRgn==0){
		seterror("PathToRegion", GetLastError());
		return NULL;
		}
	return CreatePyRgnFromHandle(hRgn);
}
#endif

static PyObject* PyDC_Detach(PyDC *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	HDC hDC = self->m_hDC;
	self->m_hDC = NULL;
	return Py_BuildValue("i", hDC);
}

static PyObject* PyDC_GetSafeHdc(PyDC *self, PyObject *args)
{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i", self->m_hDC);
}

static PyObject* PyDC_CreateCompatibleDC(PyDC *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	HDC hDC = CreateCompatibleDC(self->m_hDC);
	if(hDC==0){
		seterror("CreateCompatibleDC", GetLastError());
		return NULL;
		}
	return (PyObject*)PyDC::createInstance(hDC);
}

PyObject* PyDC_CreateCompatibleBitmap(PyDC *self, PyObject *args)
	{
	int nWidth, nHeight;
	if (!PyArg_ParseTuple(args, "ii", &nWidth, &nHeight))
		return NULL;
	HBITMAP hBmp = CreateCompatibleBitmap(self->m_hDC, nWidth, nHeight);
	if(hBmp==NULL)
		{
		seterror("CreateCompatibleBitmap", GetLastError());
		return NULL;
		}
	return CreateBitmapFromHandle(hBmp, nWidth, nHeight);
	}

static PyObject* PyDC_BitBlt(PyDC *self, PyObject *args)
{
	int nXDest, nYDest;
	int nWidth, nHeight;
	PyObject *obj;
	int nXSrc = 0, nYSrc = 0;
	DWORD dwRop = SRCCOPY;
	if(!PyArg_ParseTuple(args, "(ii)(ii)O|(ii)l", 
		&nXDest,&nYDest,&nWidth,&nHeight,&obj,&nXSrc,&nYSrc,&dwRop))
		return NULL;
	HDC hdcSrc = (HDC)GetGdiObjHandle(obj);
	BOOL res = BitBlt(self->m_hDC,nXDest,nYDest,nWidth,nHeight,hdcSrc,nXSrc,nYSrc,dwRop);
	if(!res){
		seterror("BitBlt", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyDC_StretchBlt(PyDC *self, PyObject *args)
{
	int nXDest, nYDest;
	int nWidthDest, nHeightDest;
	PyObject *obj;
	int nXSrc = 0, nYSrc = 0;
	int nWidthSrc, nHeightSrc;
	DWORD dwRop = SRCCOPY;
	if(!PyArg_ParseTuple(args, "(iiii)O(iiii)|l",
		&nXDest,&nYDest,&nWidthDest,&nHeightDest,&obj,
		&nXSrc,&nYSrc,&nWidthSrc,&nHeightSrc,&dwRop))
		return NULL;
	HDC hdcSrc = (HDC)GetGdiObjHandle(obj);
	BOOL res = StretchBlt(self->m_hDC,nXDest,nYDest,nWidthDest,nHeightDest,hdcSrc,nXSrc,nYSrc,nWidthSrc,nHeightSrc,dwRop);
	if(!res){
		seterror("StretchBlt", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyDC_DeleteDC(PyDC *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res = DeleteDC(self->m_hDC);
	if(!res){
		seterror("DeleteDC", GetLastError());
		return NULL;
		}
	self->m_hDC = NULL;
	return none();
}

static PyObject* PyDC_SetBrushOrgEx(PyDC *self, PyObject *args)
{
	int nXOrg, nYOrg;
	if(!PyArg_ParseTuple (args, "(ii)", &nXOrg, &nYOrg))
		return NULL;
	POINT pt;
	BOOL res = SetBrushOrgEx(self->m_hDC, nXOrg, nYOrg, &pt);
	if(!res){
		seterror("SetBrushOrgEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue ("(ii)", pt.x, pt.y);
}

static PyObject* PyDC_GetClipBox(PyDC *self, PyObject *args)
{
	if(!PyArg_ParseTuple (args, ""))
		return NULL;
	RECT rc;
	int res = GetClipBox(self->m_hDC, &rc);
	if(res == ERROR){
		seterror("GetClipBox", GetLastError());
		return NULL;
		}
	return Py_BuildValue ("(iiii)", rc.left, rc.top, rc.right, rc.bottom);
}


PyMethodDef PyDC::methods[] = {
#ifndef _WIN32_WCE
	{"SetWorldTransform", (PyCFunction)PyDC_SetWorldTransform, METH_VARARGS, ""},
	{"GetWorldTransform", (PyCFunction)PyDC_GetWorldTransform, METH_VARARGS, ""},
	{"SetGraphicsMode", (PyCFunction)PyDC_SetGraphicsMode, METH_VARARGS, ""},
	{"SetMapMode", (PyCFunction)PyDC_SetMapMode, METH_VARARGS, ""},
	{"SetWindowExtEx", (PyCFunction)PyDC_SetWindowExtEx, METH_VARARGS, ""},
	{"GetWindowExtEx", (PyCFunction)PyDC_GetWindowExtEx, METH_VARARGS, ""},
	{"SetViewportExtEx", (PyCFunction)PyDC_SetViewportExtEx, METH_VARARGS, ""},
	{"GetViewportExtEx", (PyCFunction)PyDC_GetViewportExtEx, METH_VARARGS, ""},
	{"SetWindowOrg", (PyCFunction)PyDC_SetWindowOrg, METH_VARARGS, ""},
	{"GetWindowOrg", (PyCFunction)PyDC_GetWindowOrg, METH_VARARGS, ""},
	{"GetROP2", (PyCFunction)PyDC_GetROP2, METH_VARARGS, ""},
	{"SetTextAlign", (PyCFunction)PyDC_SetTextAlign, METH_VARARGS, ""},
	{"SetPolyFillMode", (PyCFunction)PyDC_SetPolyFillMode, METH_VARARGS, ""},
	{"SetArcDirection", (PyCFunction)PyDC_SetArcDirection, METH_VARARGS, ""},
	{"SetMiterLimit", (PyCFunction)PyDC_SetMiterLimit, METH_VARARGS, ""},

	{"BeginPath", (PyCFunction)PyDC_BeginPath, METH_VARARGS, ""},
	{"EndPath", (PyCFunction)PyDC_EndPath, METH_VARARGS, ""},
	{"StrokePath", (PyCFunction)PyDC_StrokePath, METH_VARARGS, ""},
	{"FillPath", (PyCFunction)PyDC_FillPath, METH_VARARGS, ""},
	{"StrokeAndFillPath", (PyCFunction)PyDC_StrokeAndFillPath, METH_VARARGS, ""},
	{"CloseFigure", (PyCFunction)PyDC_CloseFigure, METH_VARARGS, ""},
	{"FlattenPath", (PyCFunction)PyDC_FlattenPath, METH_VARARGS, ""},
	{"WidenPath", (PyCFunction)PyDC_WidenPath, METH_VARARGS, ""},
	{"GetPath", (PyCFunction)PyDC_GetPath, METH_VARARGS, ""},

	{"MoveToEx", (PyCFunction)PyDC_MoveToEx, METH_VARARGS, ""},
	{"ArcTo", (PyCFunction)PyDC_ArcTo, METH_VARARGS, ""},
	{"Arc", (PyCFunction)PyDC_Arc, METH_VARARGS, ""},
	{"LineTo", (PyCFunction)PyDC_LineTo, METH_VARARGS, ""},
	{"PolylineTo", (PyCFunction)PyDC_PolylineTo, METH_VARARGS, ""},
	{"PolyBezier", (PyCFunction)PyDC_PolyBezier, METH_VARARGS, ""},
	{"PolyBezierTo", (PyCFunction)PyDC_PolyBezierTo, METH_VARARGS, ""},
	{"PolyDraw", (PyCFunction)PyDC_PolyDraw, METH_VARARGS, ""},

	{"PaintRgn", (PyCFunction)PyDC_PaintRgn, METH_VARARGS, ""},
	{"PathToRegion", (PyCFunction)PyDC_PathToRegion, METH_VARARGS, ""},
#endif
	{"TextOut", (PyCFunction)PyDC_TextOut, METH_VARARGS, ""},
	{"ExtTextOut", (PyCFunction)PyDC_ExtTextOut, METH_VARARGS, ""},

	{"SaveDC", (PyCFunction)PyDC_SaveDC, METH_VARARGS, ""},
	{"RestoreDC", (PyCFunction)PyDC_RestoreDC, METH_VARARGS, ""},
	{"SetROP2", (PyCFunction)PyDC_SetROP2, METH_VARARGS, ""},
	{"SetBkMode", (PyCFunction)PyDC_SetBkMode, METH_VARARGS, ""},
	{"GetBkMode", (PyCFunction)PyDC_GetBkMode, METH_VARARGS, ""},
	{"SetTextColor", (PyCFunction)PyDC_SetTextColor, METH_VARARGS, ""},
	{"GetDeviceCaps", (PyCFunction)PyDC_GetDeviceCaps, METH_VARARGS, ""},
	{"GetTextMetrics", (PyCFunction)PyDC_GetTextMetrics, METH_VARARGS, ""},
	{"GetTextExtent", (PyCFunction)PyDC_GetTextExtent, METH_VARARGS, ""},

	{"SetViewportOrgEx", (PyCFunction)PyDC_SetViewportOrgEx, METH_VARARGS, ""},
	{"SetViewportOrg", (PyCFunction)PyDC_SetViewportOrgEx, METH_VARARGS, ""},

	{"Rectangle", (PyCFunction)PyDC_Rectangle, METH_VARARGS, ""},
	{"RoundRect", (PyCFunction)PyDC_RoundRect, METH_VARARGS, ""},
	{"Ellipse", (PyCFunction)PyDC_Ellipse, METH_VARARGS, ""},
	{"Polyline", (PyCFunction)PyDC_Polyline, METH_VARARGS, ""},
	{"Polygon", (PyCFunction)PyDC_Polygon, METH_VARARGS, ""},
	{"DrawText", (PyCFunction)PyDC_DrawText, METH_VARARGS, ""},
	{"FillSolidRect", (PyCFunction)PyDC_FillSolidRect, METH_VARARGS, ""},
	{"FrameRect", (PyCFunction)PyDC_FrameRect, METH_VARARGS, ""},

	{"SelectObject", (PyCFunction)PyDC_SelectObject, METH_VARARGS, ""},
	
	{"SelectClipRgn", (PyCFunction)PyDC_SelectClipRgn, METH_VARARGS, ""},

	{"Detach", (PyCFunction)PyDC_Detach, METH_VARARGS, ""},
	{"GetSafeHdc", (PyCFunction)PyDC_GetSafeHdc, METH_VARARGS, ""},

	{"CreateCompatibleDC", (PyCFunction)PyDC_CreateCompatibleDC, METH_VARARGS, ""},
	{"CreateCompatibleBitmap", (PyCFunction)PyDC_CreateCompatibleBitmap, METH_VARARGS, ""},
	{"BitBlt", (PyCFunction)PyDC_BitBlt, METH_VARARGS, ""},
	{"StretchBlt", (PyCFunction)PyDC_StretchBlt, METH_VARARGS, ""},
	{"DeleteDC", (PyCFunction)PyDC_DeleteDC, METH_VARARGS, ""},
	{"SetBrushOrgEx", (PyCFunction)PyDC_SetBrushOrgEx, METH_VARARGS, ""},
	{"SetBrushOrg", (PyCFunction)PyDC_SetBrushOrgEx, METH_VARARGS, ""},
	{"GetClipBox", (PyCFunction)PyDC_GetClipBox, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyDC::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyDC",			// tp_name
	sizeof(PyDC),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyDC::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyDC::getattr,// tp_getattr
	(setattrfunc)0,	// tp_setattr
	(cmpfunc)0,		// tp_compare
	(reprfunc)0,	// tp_repr
	0,				// tp_as_number
	0,				// tp_as_sequence
	0,				// tp_as_mapping
	(hashfunc)0,	// tp_hash
	(ternaryfunc)0,	// tp_call
	(reprfunc)0,	// tp_str

	// Space for future expansion
	0L,0L,0L,0L,

	"PyDC Type" // Documentation string
	};

