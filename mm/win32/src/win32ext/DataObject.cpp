#include "stdafx.h"

#include "DataObject.h"


// this returns a pointer that should not be stored.
COleDataObject *ui_data_object::GetDataObject(PyObject *self)
	{
	return (COleDataObject *)ui_assoc_object::GetGoodCppObject(self, &type);
	}

void ui_data_object::DoKillAssoc( BOOL bDestructing /*= FALSE*/ )
	{
	if (m_deleteDO) 
		{
		COleDataObject *pDO = GetDataObject(this);
		if (pDO)delete pDO;
		}
	ui_assoc_object::DoKillAssoc(bDestructing);
	}

ui_data_object::~ui_data_object()
	{
	DoKillAssoc(TRUE);
	}

void *ui_data_object::GetGoodCppObject(ui_type *ui_type_check) const
	{
	COleDataObject* pDO= (COleDataObject*)ui_assoc_object::GetGoodCppObject(ui_type_check);
	if (!pDO)RETURN_ERR("There is no OleDataObject associated with the object");
	return pDO;
	}

// @pymethod |win32ui|CreateOleDataObject|Creates an OleDataObject.
PyObject *create_ole_data_object( PyObject *self, PyObject *args )
	{
	CHECK_NO_ARGS2(args, CreateOleDataObject);
	COleDataObject* pDO= new COleDataObject;
    ui_data_object *pPyDO =
      (ui_data_object *) ui_assoc_object::make (ui_data_object::type, pDO)->GetGoodRet();
    pPyDO->m_deleteDO=TRUE;
	return pPyDO;
	}

// @pymethod int|PyDataObject|IsDataAvailable|Returns TRUE if there are data in the specified format. FALSE if not.
static PyObject *
ui_data_object_is_data_available(PyObject *self, PyObject *args)
	{
	int cf; 
	if (!PyArg_ParseTuple(args,"i:IsDataAvailable",&cf))
		return NULL;

	COleDataObject* pDO = ui_data_object::GetDataObject(self);
	if (!pDO)return NULL;

	CLIPFORMAT cfPrivate=(CLIPFORMAT)cf;
	BOOL bRes = pDO->IsDataAvailable(cfPrivate);

	return Py_BuildValue("i",bRes);
	}

// @pymethod int|PyDataObject|GetGlobalData|Returns the global data in the specified format as a string. None if not available.
static PyObject *
ui_data_object_get_global_data(PyObject *self, PyObject *args)
	{
	int cf; 
	if (!PyArg_ParseTuple(args,"i:GetGlobalData",&cf))
		return NULL;

	COleDataObject* pDO = ui_data_object::GetDataObject(self);
	if (!pDO)return NULL;

	CLIPFORMAT cfPrivate=(CLIPFORMAT)cf;
	HGLOBAL hObjDesc = pDO->GetGlobalData(cfPrivate);
	if(!hObjDesc) RETURN_NONE;
;
	LPSTR lpClipMem=(LPSTR)GlobalLock(hObjDesc);
	CString str(lpClipMem);
	::GlobalUnlock(lpClipMem);

	return Py_BuildValue("s",str);
	}



static struct PyMethodDef ui_data_object_methods[] = 
	{
	{"IsDataAvailable",ui_data_object_is_data_available,1},
	{"GetGlobalData",ui_data_object_get_global_data,1},
	{NULL,			NULL},
	};


ui_type ui_data_object::type("PyDataObject", 
						   &ui_assoc_object::type, 
						   sizeof(ui_data_object), 
						   ui_data_object_methods, 
						   GET_PY_CTOR(ui_data_object));
