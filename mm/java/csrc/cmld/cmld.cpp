
/**************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

***************************************************************************/

#include <stdafx.h>

#include "Python.h"

#include "mtpycall.h"

#include "ServerThread.h"

static PyObject *ErrorObject;

PyInterpreterState* PyCallbackBlock::s_interpreterState;

void seterror(const char *msg){ PyErr_SetString(ErrorObject, msg);}


typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	ServerThread *pServer;
} CMLServerObject;

staticforward PyTypeObject CMLServerType;

static CMLServerObject *
newCMLServerObject()
{
	CMLServerObject *self;

	self = PyObject_NEW(CMLServerObject, &CMLServerType);
	if (self == NULL)
		return NULL;
	self->pServer = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


////////////////////////////////////////////
// CMLServer object

static char CMLServer_SetCmdListener__doc__[] =
""
;
static PyObject *
CMLServer_SetCmdListener(CMLServerObject *self, PyObject *args)
{
	PyObject *pycbobj;
	if (!PyArg_ParseTuple(args,"O",&pycbobj))
		return NULL;
	
	Py_BEGIN_ALLOW_THREADS
	self->pServer->SetCmdListener(pycbobj);
	Py_END_ALLOW_THREADS
		
	Py_INCREF(Py_None);
	return Py_None;
}

static char CMLServer_Start__doc__[] =
""
;
static PyObject *
CMLServer_Start(CMLServerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	
	Py_BEGIN_ALLOW_THREADS
	self->pServer->Start();
	Py_END_ALLOW_THREADS
		
	Py_INCREF(Py_None);
	return Py_None;
}

static char CMLServer_Stop__doc__[] =
""
;
static PyObject *
CMLServer_Stop(CMLServerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	

	Py_BEGIN_ALLOW_THREADS
	self->pServer->Stop();
	Py_END_ALLOW_THREADS
		
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef CMLServer_methods[] = {
	{"SetCmdListener", (PyCFunction)CMLServer_SetCmdListener, METH_VARARGS, CMLServer_SetCmdListener__doc__},
	{"Start", (PyCFunction)CMLServer_Start, METH_VARARGS, CMLServer_Start__doc__},
	{"Stop", (PyCFunction)CMLServer_Stop, METH_VARARGS, CMLServer_Stop__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
CMLServer_dealloc(CMLServerObject *self)
{
	/* XXXX Add your own cleanup code here */
	if(self->pServer)
		delete self->pServer;
	PyMem_DEL(self);
}

static PyObject *
CMLServer_getattr(CMLServerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(CMLServer_methods, (PyObject *)self, name);
}

static char CMLServerType__doc__[] =
""
;

static PyTypeObject CMLServerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"CMLServer",			/*tp_name*/
	sizeof(CMLServerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)CMLServer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)CMLServer_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	CMLServerType__doc__ /* Documentation string */
};

// End of code for CMLServer object 
////////////////////////////////////////////


///////////////////////////////////
static char CreateCMLServer__doc__[] =
""
;
static PyObject *
CreateCMLServer(PyObject *self, PyObject *args)
{
	int port;
	if (!PyArg_ParseTuple(args,"i",&port))
		return NULL;
	
	CMLServerObject *obj = newCMLServerObject();
	if (obj == NULL)
		return NULL;
	obj->pServer = new ServerThread(port);
	
	return (PyObject*)obj;
}

static struct PyMethodDef cmld_methods[] = {
	{"CreateCMLServer", (PyCFunction)CreateCMLServer, METH_VARARGS, CreateCMLServer__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


static char cmld_module_documentation[] =
"CML Server"
;

extern "C" __declspec(dllexport)
void initcmld()
{
	PyObject *m, *d;
	
	// Create the module and add the functions
	m = Py_InitModule4("cmld", cmld_methods,
		cmld_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("cmld.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	PyCallbackBlock::init();
	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module cmld");
}



