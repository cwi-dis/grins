/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/
#include "stdafx.h"

#include "Python.h"

#include "VViewer.h"

static PyObject *ErrorObject;


static void
seterror(const char *funcname, const char *pszmsg)
{
	PyErr_Format(ErrorObject, "%s failed, error = %s", funcname, pszmsg);
}


typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	CVViewer *pVV;
} VViewerObject;

staticforward PyTypeObject VViewerType;

static VViewerObject *
newVViewerObject()
{
	VViewerObject *self;

	self = PyObject_NEW(VViewerObject, &VViewerType);
	if (self == NULL)
		return NULL;
	self->pVV=NULL;
	/* XXXX Add your own initializers here */
	return self;
}


////////////////////////////////////////////
// VViewer object 

static char VViewer_CreateWindow__doc__[] =
""
;

static PyObject *
VViewer_CreateWindow(VViewerObject *self, PyObject *args)
{
	HWND hWnd=0;
	if (!PyArg_ParseTuple(args, "i",&hWnd))
		return NULL;
	if(!IsWindow(hWnd))
		{
		seterror("VViewer_CreateWindow","The parent is not an os window");
		return NULL;
		}
	CRect rectClient;
	AfxEnableControlContainer();
	GetClientRect(hWnd,&rectClient);

	Py_BEGIN_ALLOW_THREADS
	// create the control
	self->pVV=CVViewer::CreateVViewer(CWnd::FromHandle(hWnd),rectClient);
	Py_END_ALLOW_THREADS

	Py_INCREF(Py_None);
	return Py_None;
}

static char VViewer_SetSource__doc__[] =
""
;

static PyObject *
VViewer_SetSource(VViewerObject *self, PyObject *args)
{
	char *psz;
	if (!PyArg_ParseTuple(args, "s",&psz))
		return NULL;
	if(!IsWindow(self->pVV->GetSafeHwnd()))
		{
		seterror("VViewer_SetSrc","The comtrol has not been created");
		return NULL;
		}
	Py_BEGIN_ALLOW_THREADS
	self->pVV->SetSource(psz);
	Py_END_ALLOW_THREADS

	Py_INCREF(Py_None);
	return Py_None;
}

static char VViewer_GetSafeHwnd__doc__[] =
""
;

static PyObject *
VViewer_GetSafeHwnd(VViewerObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(!self->pVV->GetSafeHwnd() || !IsWindow(self->pVV->GetSafeHwnd()))
		return Py_BuildValue("i",0);
	else
		return Py_BuildValue("i",self->pVV->GetSafeHwnd());
}



static struct PyMethodDef VViewer_methods[] = {
	{"CreateWindow", (PyCFunction)VViewer_CreateWindow, METH_VARARGS, VViewer_CreateWindow__doc__},
	{"SetSource", (PyCFunction)VViewer_SetSource, METH_VARARGS, VViewer_SetSource__doc__},
	{"GetSafeHwnd", (PyCFunction)VViewer_GetSafeHwnd, METH_VARARGS, VViewer_GetSafeHwnd__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


static void
VViewer_dealloc(VViewerObject *self)
{
	/* XXXX Add your own cleanup code here */
	if(self->pVV->GetSafeHwnd() && IsWindow(self->pVV->GetSafeHwnd()))
		self->pVV->DestroyWindow();
	PyMem_DEL(self);
}

static PyObject *
VViewer_getattr(VViewerObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(VViewer_methods, (PyObject *)self, name);
}

static char VViewerType__doc__[] =
"VViewer Control"
;

static PyTypeObject VViewerType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"VViewer",			/*tp_name*/
	sizeof(VViewerObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)VViewer_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)VViewer_getattr,	/*tp_getattr*/
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
	VViewerType__doc__ /* Documentation string */
};

// End of code for VViewer object 
////////////////////////////////////////////

static char CreateVViewer__doc__[] =
""
;

static PyObject *
CreateVViewer(PyObject *self, PyObject *args)
{
	VViewerObject *obj;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	obj = newVViewerObject();
	if (obj == NULL)
		return NULL;
	return (PyObject *) obj;
}


static struct PyMethodDef vview_methods[] = {
	{"CreateVViewer", (PyCFunction)CreateVViewer, METH_VARARGS, CreateVViewer__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static char vview_module_documentation[] =
"Viewer of DXF, DWG, DWF vector files using Autodesk's Volo Viewer Control"
;

extern "C" __declspec(dllexport)
void initvview()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("vview", vview_methods,
		vview_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("vview.error");
	PyDict_SetItemString(d, "error", ErrorObject);


	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module vview");
}
