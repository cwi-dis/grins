// CMIF_ADD


#include "moddef.h"

DECLARE_PYMODULECLASS(Win32Sdk);
DECLARE_PYMODULECLASS(Afx);

//#include "win32rgn.h"
//extern PyObject *ui_create_frame(PyObject *self, PyObject *args);
//extern PyObject *PyCToolTipCtrl_create(PyObject *self, PyObject *args);

//extern PyObject *ui_create_dc_from_handle (PyObject *self, PyObject *args);

extern PyObject *create_ole_data_object( PyObject *self, PyObject *args );

// @pymeth GetWin32Sdk|Creates a Win32 SDK module wrapper object.
// @pymeth GetAfx|Creates an Afx module wrapper object.

#define DEF_NEW_PY_METHODS\
	{"GetWin32Sdk",MWin32Sdk::create,1},\
	{"GetAfx",MAfx::create,1},\
//	{"CreateFrame",ui_create_frame,1},\
//	{"CreateToolTipCtrl",PyCToolTipCtrl_create,1},
//	{"CreateRgn",PyCRgn::create,1},\
//	{"CreateDCFromHandle",ui_create_dc_from_handle,1},\
