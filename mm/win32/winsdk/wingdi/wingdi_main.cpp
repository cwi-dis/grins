
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "wingdi_main.h"

#include "utils.h"


PyObject* Wingdi_DeleteObject(PyObject *self, PyObject *args)
{
	PyObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	HGDIOBJ hgdiobj = (HGDIOBJ)GetGdiObjHandle(obj);
	BOOL res = DeleteObject(hgdiobj);
	if(!res){
		seterror("DeleteObject", GetLastError());
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;
}

PyObject* Wingdi_GetStockObject(PyObject *self, PyObject *args)
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


#ifndef _WIN32_WCE
PyObject* Wingdi_ExtCreatePen(PyObject *self, PyObject *args)
{
	DWORD dwPenStyle = PS_GEOMETRIC | PS_SOLID | PS_ENDCAP_FLAT | PS_JOIN_MITER;
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
#endif

PyObject* Wingdi_CreateSolidBrush(PyObject *self, PyObject *args)
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

#ifndef _WIN32_WCE
PyObject* Wingdi_CreateBrushIndirect(PyObject *self, PyObject *args)
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
#endif

PyObject* Wingdi_CreateFontIndirect(PyObject *self, PyObject *args)
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
	s.lfQuality = (BYTE)p.getIntAttr("quality", DEFAULT_QUALITY);
	s.lfPitchAndFamily = (BYTE)p.getIntAttr("pitch and family", DEFAULT_PITCH | FF_DONTCARE); // naming compatibility
	p.getStrAttr("name", toMB(s.lfFaceName), LF_FACESIZE, "Arial");  //  naming compatibility
	HFONT hfont = CreateFontIndirect(&s);
	if(hfont==0){
		seterror("CreateFontIndirect", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hfont);
}

PyObject* Wingdi_IntersectRect(PyObject *self, PyObject *args)
	{
	RECT rcSrc1,rcSrc2;
	if (!PyArg_ParseTuple(args,"(iiii)(iiii):IntersectRect",
		        &rcSrc1.left, &rcSrc1.top, &rcSrc1.right,&rcSrc1.bottom,
				&rcSrc2.left, &rcSrc2.top, &rcSrc2.right,&rcSrc2.bottom
				))
		return NULL;
	RECT rcDst;
	BOOL inrersect=::IntersectRect(&rcDst,&rcSrc1,&rcSrc2);
	return Py_BuildValue("(iiii)i",rcDst.left,rcDst.top,rcDst.right,rcDst.bottom,inrersect);
	}

PyObject* Wingdi_UnionRect(PyObject *self, PyObject *args)
	{
	RECT rcSrc1,rcSrc2;
	if (!PyArg_ParseTuple(args,"(iiii)(iiii):IntersectRect",
		        &rcSrc1.left, &rcSrc1.top, &rcSrc1.right,&rcSrc1.bottom,
				&rcSrc2.left, &rcSrc2.top, &rcSrc2.right,&rcSrc2.bottom
				))
		return NULL;
	RECT rcDst;
	BOOL notempty = ::UnionRect(&rcDst,&rcSrc1,&rcSrc2);
	return Py_BuildValue("(iiii)i",rcDst.left,rcDst.top,rcDst.right,rcDst.bottom, notempty);
	}

PyObject* Wingdi_GetRGBValues(PyObject *self, PyObject *args)
	{
	long clr;   
	if (!PyArg_ParseTuple (args, "l",&clr))
		return NULL;
	return Py_BuildValue("iii",(int)GetRValue(clr),(int)GetGValue(clr),(int)GetBValue(clr));
	}
