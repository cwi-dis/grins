
#include "wingdi_bmp.h"

#include "utils.h"

struct PyBmp
	{
	PyObject_HEAD
	HBITMAP m_hBmp;
	int m_width;
	int m_height;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyBmp *createInstance(HBITMAP hBmp = NULL, int  width=0, int height=0)
		{
		PyBmp *instance = PyObject_NEW(PyBmp, &type);
		if (instance == NULL) return NULL;
		instance->m_hBmp = hBmp;
		instance->m_width = width;
		instance->m_height = height;
		return instance;
		}

	static void dealloc(PyBmp *instance) 
		{ 
		if(instance->m_hBmp)
			DeleteObject((HGDIOBJ)instance->m_hBmp);
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyBmp *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Wingdi_CreateCompatibleBitmap(PyObject *self, PyObject *args)
	{
	PyObject *obj;
	int nWidth, nHeight;
	if (!PyArg_ParseTuple(args, "Oii", &obj, &nWidth, &nHeight))
		return NULL;
	HDC hDC = (HDC)GetGdiObjHandle(obj);
	HBITMAP hBmp = CreateCompatibleBitmap(hDC, nWidth, nHeight);
	if(hBmp==NULL)
		{
		seterror("CreateCompatibleBitmap", GetLastError());
		return NULL;
		}
	return (PyObject*)PyBmp::createInstance(hBmp, nWidth, nHeight);
	}

PyObject* Wingdi_CreateBitmapFromHandle(PyObject *self, PyObject *args)
	{
	HBITMAP hBmp;
	if (!PyArg_ParseTuple(args, "i", &hBmp))
		return NULL;
	return (PyObject*)PyBmp::createInstance(hBmp);
	}

PyObject* CreateBitmapFromHandle(HBITMAP hBmp, int nWidth, int nHeight)
	{
	return (PyObject*)PyBmp::createInstance(hBmp, nWidth, nHeight);
	}

PyObject* Wingdi_LoadImage(PyObject *self, PyObject *args)
	{
	char *filename;
	if (!PyArg_ParseTuple(args, "s", &filename))
		return NULL;
	HBITMAP hBmp = (HBITMAP)LoadImage(NULL, TextPtr(filename), 
		0, 0, 0, LR_LOADFROMFILE | LR_CREATEDIBSECTION);
	if(hBmp==NULL)
		{
		seterror("LoadImage", GetLastError());
		return NULL;
		}
    BITMAP bm;
    GetObject(hBmp, sizeof(hBmp),&bm); // get size of bitmap
	return (PyObject*)PyBmp::createInstance(hBmp, bm.bmWidth, bm.bmHeight);
	}


////////////////////////////
// module

static PyObject* PyBmp_DeleteObject(PyBmp *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	DeleteObject((HGDIOBJ)self->m_hBmp);
	self->m_hBmp = NULL;
	return none();
	}

static PyObject* PyBmp_Detach(PyBmp *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	HBITMAP hBmp = self->m_hBmp;
	self->m_hBmp = NULL;
	return Py_BuildValue("i", hBmp);
	}

static PyObject* PyBmp_GetSafeHandle(PyBmp *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i", self->m_hBmp);
	}

static PyObject* PyBmp_GetSize(PyBmp *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_hBmp == NULL)
		return Py_BuildValue("ii", 0, 0);
	return Py_BuildValue("ii", self->m_width, self->m_height);
	}

PyMethodDef PyBmp::methods[] = {
	{"DeleteObject", (PyCFunction)PyBmp_DeleteObject, METH_VARARGS, ""},
	{"Detach", (PyCFunction)PyBmp_Detach, METH_VARARGS, ""},
	{"GetSafeHandle", (PyCFunction)PyBmp_GetSafeHandle, METH_VARARGS, ""},
	{"GetSize", (PyCFunction)PyBmp_GetSize, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyBmp::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyBmp",			// tp_name
	sizeof(PyBmp),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyBmp::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyBmp::getattr,// tp_getattr
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

	"PyBmp Type" // Documentation string
	};

