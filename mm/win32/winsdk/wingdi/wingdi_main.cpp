
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "utils.h"

#include "wingdi_main.h"

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

