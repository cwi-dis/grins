#include "stdafx.h"

#include "DataObject.h"

struct PyDataObject
	{
	PyObject_HEAD
	COleDataObject* m_pOleDataObject;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyDataObject *createInstance(COleDataObject* pOleDataObject = NULL)
		{
		PyDataObject *instance = PyObject_NEW(PyDataObject, &type);
		if (instance == NULL) return NULL;
		instance->m_pOleDataObject = pOleDataObject;
		return instance;
		}

	static void dealloc(PyDataObject *instance) 
		{ 
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyDataObject *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

//////////////////////
// Create PyDataObject (wrapper of COleDataObject)

PyObject* CreatePyDataObject(COleDataObject *pOleDataObject)
	{
	return (PyObject*)PyDataObject::createInstance(pOleDataObject);
	}

//////////////////////
// PyDataObject methos

static PyObject *
PyDataObject_IsDataAvailable(PyDataObject *self, PyObject *args)
	{
	int cf; 
	if (!PyArg_ParseTuple(args,"i:IsDataAvailable",&cf))
		return NULL;
	CLIPFORMAT cfPrivate=(CLIPFORMAT)cf;
	BOOL bRes = self->m_pOleDataObject->IsDataAvailable(cfPrivate);
	return Py_BuildValue("i",bRes);
	}

static PyObject *
PyDataObject_GetGlobalData(PyDataObject *self, PyObject *args)
	{
	int cf; 
	if (!PyArg_ParseTuple(args,"i:GetGlobalData",&cf))
		return NULL;
	CLIPFORMAT cfPrivate=(CLIPFORMAT)cf;
	HGLOBAL hObjDesc = self->m_pOleDataObject->GetGlobalData(cfPrivate);
	if(!hObjDesc) 
		{
		Py_INCREF(Py_None);
		return Py_None;
		}
	LPSTR lpClipMem=(LPSTR)GlobalLock(hObjDesc);
	CString str(lpClipMem);
	::GlobalUnlock(lpClipMem);
	return Py_BuildValue("s",str);
	}


PyMethodDef PyDataObject::methods[] = {
	{"IsDataAvailable", (PyCFunction)PyDataObject_IsDataAvailable, 1},
	{"GetGlobalData", (PyCFunction)PyDataObject_GetGlobalData, 1},
	{NULL, (PyCFunction)NULL, 0}		// sentinel
};

PyTypeObject PyDataObject::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyDataObject",			// tp_name
	sizeof(PyDataObject),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyDataObject::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyDataObject::getattr,// tp_getattr
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

	"PyDataObject Type" // Documentation string
	};


