
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

#include "utils.h"

#include "wingdi_rgn.h"

struct PyRgn
	{
	PyObject_HEAD
	HRGN m_hRgn;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyRgn *createInstance()
		{
		PyRgn *instance = PyObject_NEW(PyRgn, &type);
		if (instance == NULL) return NULL;
		instance->m_hRgn = NULL;
		return instance;
		}

	static PyRgn *createInstance(HRGN hrgn)
		{
		PyRgn * p = createInstance();
		if (p == NULL) return NULL;
		p->m_hRgn = hrgn;
		return p;
		}

	static void dealloc(PyRgn *instance) 
		{ 
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyRgn *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	static HRGN newHRGN() {return CreateRectRgn(0,0,0,0);}
	};

PyObject* Wingdi_CreateRectRgn(PyObject *self, PyObject *args)
	{
	RECT rc;
	if (!PyArg_ParseTuple(args, "(iiii)", &rc.left, &rc.top, &rc.right, &rc.bottom))
		return NULL;
	HRGN hrgn = CreateRectRgn(rc.left, rc.top, rc.right, rc.bottom);
	if(hrgn==0)
		{
		seterror("CreateRectRgn", GetLastError());
		return NULL;
		}
	return (PyObject*)PyRgn::createInstance(hrgn);
	}

PyObject* Wingdi_CreatePolygonRgn(PyObject *self, PyObject *args)
	{
	PyObject *pyptlist;
	int nMode = ALTERNATE;
	if (!PyArg_ParseTuple(args, "O|i", &pyptlist, &nMode))
		return NULL;
	PyPtListConverter conv;
	if(!conv.convert(pyptlist))
		{
		seterror("CreatePolygonRgn", "Invalid point list");
		return NULL;
		}
	HRGN hrgn = CreatePolygonRgn(conv.getPoints(), conv.getSize(), nMode);
	if(hrgn==0)
		{
		seterror("CreatePolygonRgn", GetLastError());
		return NULL;
		}
	return (PyObject*)PyRgn::createInstance(hrgn);
	}

PyObject* Wingdi_PathToRegion(PyObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i", &hdc))
		return NULL;
	HRGN hrgn = PathToRegion(hdc);
	if(hrgn==0){
		seterror("PathToRegion", GetLastError());
		return NULL;
		}
	return (PyObject*)PyRgn::createInstance(hrgn);
}

PyObject* Wingdi_CombineRgn(PyObject *self, PyObject *args)
	{
	PyRgn *rgn1;
	PyRgn *rgn2;
	int fnCombineMode;
	if (!PyArg_ParseTuple(args,"O!O!i", &PyRgn::type, &rgn1, 
		&PyRgn::type, &rgn2, &fnCombineMode))
		return NULL;
	HRGN hrgnDest = PyRgn::newHRGN();
	int res = CombineRgn(hrgnDest, rgn1->m_hRgn, rgn2->m_hRgn, fnCombineMode);
	if(res == ERROR)
		{
		seterror("CombineRgn", GetLastError());
		return NULL;
		}
	return (PyObject*)PyRgn::createInstance(hrgnDest);
	}

///////////////////////////////
// module

static PyObject* PyRgn_PtInRegion(PyRgn *self, PyObject *args)
{
	int x, y;
	if (!PyArg_ParseTuple(args, "(ii)", &x, &y))
		return NULL;
	BOOL res = PtInRegion(self->m_hRgn, x, y);
	return Py_BuildValue("i", res);
}

static PyObject* PyRgn_RectInRegion(PyRgn *self, PyObject *args)
{
	RECT rect;
	if (!PyArg_ParseTuple(args, "(iiii)", &rect.left, &rect.top, &rect.right, &rect.bottom))
		return NULL;
	BOOL res = RectInRegion(self->m_hRgn, &rect);
	return Py_BuildValue("i", res);
}

static PyObject* PyRgn_EqualRgn(PyRgn *self, PyObject *args)
	{
	PyRgn *rgn;
	if (!PyArg_ParseTuple(args,"O!", &PyRgn::type, &rgn)) 
		return NULL;
	BOOL res = EqualRgn(self->m_hRgn, rgn->m_hRgn);
	return Py_BuildValue("i", res);
	}

static PyObject* PyRgn_SetRectRgn(PyRgn *self, PyObject *args)
{
	RECT rect;
	if (!PyArg_ParseTuple(args, "(iiii)", &rect.left, &rect.top, &rect.right, &rect.bottom))
		return NULL;
	BOOL res = SetRectRgn(self->m_hRgn, rect.left, rect.top, rect.right, rect.bottom);
	if(!res)
		{
		seterror("SetRectRgn", GetLastError());
		return NULL;
		}
	return none();
}

static PyObject* PyRgn_CombineRgn(PyRgn *self, PyObject *args)
	{
	PyRgn *rgn1;
	PyRgn *rgn2;
	int fnCombineMode;
	if (!PyArg_ParseTuple(args,"O!O!i", &PyRgn::type, &rgn1, 
		&PyRgn::type, &rgn2, &fnCombineMode))
		return NULL;
	int res = CombineRgn(self->m_hRgn, rgn1->m_hRgn, rgn2->m_hRgn, fnCombineMode);
	if(res == ERROR)
		{
		seterror("CombineRgn", GetLastError());
		return NULL;
		}
	return none();
	}

static PyObject* PyRgn_CopyRgn(PyRgn *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	HRGN hrgnDest = PyRgn::newHRGN();
	int res = CombineRgn(hrgnDest, self->m_hRgn, NULL, RGN_COPY);
	if(res == ERROR)
		{
		seterror("CopyRgn", GetLastError());
		return NULL;
		}
	return (PyObject*)PyRgn::createInstance(hrgnDest);
	}

static PyObject* PyRgn_GetRgnBox(PyRgn *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	RECT rc;
	int res = GetRgnBox(self->m_hRgn, &rc);
	if(res == 0)
		{
		seterror("GetRgnBox", GetLastError());
		return NULL;
		}
	return Py_BuildValue("iiii", rc.left, rc.top, rc.right, rc.bottom);
	}

static PyObject* PyRgn_DeleteObject(PyRgn *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	DeleteObject((HGDIOBJ)self->m_hRgn);
	self->m_hRgn = NULL;
	return none();
	}

static PyObject* PyRgn_Detach(PyRgn *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	HRGN hRgn = self->m_hRgn;
	self->m_hRgn = NULL;
	return Py_BuildValue("i", hRgn);
	}

static PyObject* PyRgn_GetSafeHandle(PyRgn *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i", self->m_hRgn);
	}

PyMethodDef PyRgn::methods[] = {
	{"PtInRegion", (PyCFunction)PyRgn_PtInRegion, METH_VARARGS, ""},
	{"RectInRegion", (PyCFunction)PyRgn_RectInRegion, METH_VARARGS, ""},
	{"EqualRgn", (PyCFunction)PyRgn_EqualRgn, METH_VARARGS, ""},
	{"SetRectRgn", (PyCFunction)PyRgn_SetRectRgn, METH_VARARGS, ""},
	{"CombineRgn", (PyCFunction)PyRgn_CombineRgn, METH_VARARGS, ""},
	{"CopyRgn", (PyCFunction)PyRgn_CopyRgn, METH_VARARGS, ""},
	{"GetRgnBox", (PyCFunction)PyRgn_GetRgnBox, METH_VARARGS, ""},
	{"DeleteObject", (PyCFunction)PyRgn_DeleteObject, METH_VARARGS, ""},
	{"Detach", (PyCFunction)PyRgn_Detach, METH_VARARGS, ""},
	{"GetSafeHandle", (PyCFunction)PyRgn_GetSafeHandle, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyRgn::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyRgn",			// tp_name
	sizeof(PyRgn),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyRgn::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyRgn::getattr,// tp_getattr
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

	"PyRgn Type" // Documentation string
	};

