
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "utils.h"

#include "wingdi_main.h"

PyObject* Wingdi_DeleteObject(PyObject *self, PyObject *args)
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
