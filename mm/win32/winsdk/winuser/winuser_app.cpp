
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "winuser_app.h"

#include "utils.h"

struct PyApp
	{
	PyObject_HEAD
	HINSTANCE m_hInstance;
	PyObject *m_mainWnd;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static void dealloc(PyApp *instance) 
		{ 
		Py_XDECREF(instance->m_mainWnd);
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyApp *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	static PyApp *s_instance;
	static PyApp *createInstance()
		{
		if(s_instance != NULL)
			{
			Py_INCREF(s_instance);
			return s_instance;
			}
		s_instance = PyObject_NEW(PyApp, &type);
		if (s_instance == NULL) return NULL;
		s_instance->m_hInstance = NULL;
		s_instance->m_mainWnd = NULL;
		return s_instance;
		}
	};
PyApp* PyApp::s_instance = NULL; 

PyObject* Winuser_GetApplication(PyObject *self, PyObject *args)
	{
	return (PyObject*)PyApp::createInstance();
	}

///////////////////////////
// module

static PyObject* PyApp_GetInstance(PyApp *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args,""))
		return NULL;
	return Py_BuildValue("i", self->m_hInstance);
	}

static PyObject* PyApp_GetMainWnd(PyApp *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args,""))
		return NULL;
	PyObject *obj = self->m_mainWnd;
	if(obj == NULL)
		return none();
	return Py_BuildValue("O", obj);
	}

static PyObject* PyApp_SetInstance(PyApp *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args,"i", &self->m_hInstance))
		return NULL;
	return none();
	}

static PyObject* PyApp_SetMainWnd(PyApp *self, PyObject *args)
	{ 
	PyObject *obj;
	if(!PyArg_ParseTuple(args,"O", &obj))
		return NULL;
	Py_XDECREF(self->m_mainWnd);
	if(obj == Py_None)
		self->m_mainWnd = NULL;
	else
		{
		Py_INCREF(obj);
		self->m_mainWnd = obj;
		}
	return none();
	}

PyMethodDef PyApp::methods[] = {
	{"GetInstance", (PyCFunction)PyApp_GetInstance, METH_VARARGS, ""},
	{"GetMainWnd", (PyCFunction)PyApp_GetMainWnd, METH_VARARGS, ""},
	{"SetInstance", (PyCFunction)PyApp_SetInstance, METH_VARARGS, ""},
	{"SetMainWnd", (PyCFunction)PyApp_SetMainWnd, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyApp::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyApp",			// tp_name
	sizeof(PyApp),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyApp::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyApp::getattr,// tp_getattr
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

	"PyApplication Type" // Documentation string
	};
