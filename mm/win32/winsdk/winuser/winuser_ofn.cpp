
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "winuser_ofn.h"

#include "utils.h"
#include "winuser_wnd.h"

#include <tchar.h>

struct PyOfn
	{
	PyObject_HEAD
	OPENFILENAME m_ofn;	

	bool m_bOpenFileDialog;
	TCHAR *m_pszFilter;
	TCHAR *m_pszDefExt;
	TCHAR m_szFileTitle[MAX_PATH];
	TCHAR m_szFileName[MAX_PATH];
	TCHAR m_szInitialDir[MAX_PATH];
	TCHAR m_szTitle[MAX_PATH];

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyOfn *createInstance()
		{
		PyOfn *p = PyObject_NEW(PyOfn, &type);
		if(p == NULL) return NULL;
		
		p->m_bOpenFileDialog = true;
		p->m_pszFilter = NULL;
		p->m_pszDefExt = NULL;
		p->m_szFileTitle[0] = '\0';
		p->m_szFileName[0] = '\0';
		p->m_szInitialDir[0] = '\0';
		lstrcpy(p->m_szTitle, TEXT("Open"));

		memset(&p->m_ofn, 0, sizeof(p->m_ofn));
		p->m_ofn.lStructSize       = sizeof(OPENFILENAME);
		p->m_ofn.hwndOwner         = NULL;
		p->m_ofn.hInstance         = GetAppHinstance();
		p->m_ofn.lpstrFilter       = NULL;
		p->m_ofn.lpstrCustomFilter = NULL;
		p->m_ofn.nMaxCustFilter    = 0;
		p->m_ofn.nFilterIndex      = 0;
		p->m_ofn.lpstrFile         = p->m_szFileName;
		p->m_ofn.nMaxFile          = MAX_PATH;
		p->m_ofn.lpstrFileTitle    = p->m_szFileTitle;
		p->m_ofn.nMaxFileTitle     = MAX_PATH;
		p->m_ofn.lpstrInitialDir   = p->m_szInitialDir;
		p->m_ofn.lpstrTitle        = p->m_szTitle;
		p->m_ofn.nFileOffset       = 0;
		p->m_ofn.nFileExtension    = 0;
		p->m_ofn.lpstrDefExt       = NULL;
		p->m_ofn.lCustData         = NULL; 
		p->m_ofn.lpfnHook 		   = NULL; 
		p->m_ofn.lpTemplateName    = NULL;
		p->m_ofn.Flags             = OFN_EXPLORER;
		return p;
		}

	static void dealloc(PyOfn *p) 
		{ 
		if(p->m_pszFilter != NULL)
			delete[] p->m_pszFilter;
		if(p->m_pszDefExt != NULL)
			delete[] p->m_pszDefExt;
		PyMem_DEL(p);
		}

	static PyObject *getattr(PyOfn *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Winuser_CreateFileDialog(PyObject *self, PyObject *args)
	{
	BOOL bOpenFileDialog = TRUE;
	DWORD dwFlags = 0;
	char *pszDefExt = NULL, *pszFileName=NULL, *pszFilter = NULL;
	HWND hWndParent = NULL;
	if (!PyArg_ParseTuple(args, "|izziziz", 
		&bOpenFileDialog, &pszDefExt, &pszFileName, &dwFlags, &pszFilter, &hWndParent))
		return NULL;
	PyOfn *pyofn = PyOfn::createInstance();
	if(pyofn==NULL) return NULL;

	pyofn->m_bOpenFileDialog = bOpenFileDialog?true:false;

	if(pszFilter != NULL)
		{
		pyofn->m_pszFilter = new TCHAR[strlen(pszFilter)+1];
		lstrcpy(pyofn->m_pszFilter, TextPtr(pszFilter));
		TCHAR *pch = pyofn->m_pszFilter;
		while( (pch = text_strchr(pch, '|')) != NULL )
			*pch++ = '\0';
		}
	if(pszDefExt != NULL)
		{
		pyofn->m_pszDefExt = new TCHAR[strlen(pszDefExt)+1];
		lstrcpy(pyofn->m_pszDefExt, TextPtr(pszDefExt));
		}
	if (pszFileName != NULL)
		{
		lstrcpy(pyofn->m_szFileName, TextPtr(pszFileName));
		}
	pyofn->m_ofn.hwndOwner = hWndParent;
	pyofn->m_ofn.lpstrFile = pyofn->m_szFileName;
	pyofn->m_ofn.lpstrDefExt = pyofn->m_pszDefExt;
	pyofn->m_ofn.lpstrFilter = pyofn->m_pszFilter;
	pyofn->m_ofn.Flags = dwFlags;

	return (PyObject*) pyofn;
	}

/////////////////////
// Module

static PyObject* PyOfn_DoModal(PyOfn *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_bOpenFileDialog)
		{
		BOOL res;
		Py_BEGIN_ALLOW_THREADS
		res = GetOpenFileName(&self->m_ofn);
		Py_END_ALLOW_THREADS
		if(!res)
			{
			DWORD dw = GetLastError();
			if(dw == ERROR_INVALID_PARAMETER || dw == ERROR_OUTOFMEMORY)
				{
				seterror("GetOpenFileName", dw);
				return NULL;
				}
			}
		return Py_BuildValue("i", (res?IDOK:IDCANCEL));
		}
	BOOL res;
	Py_BEGIN_ALLOW_THREADS
	res = GetSaveFileName(&self->m_ofn);
	Py_END_ALLOW_THREADS
	if(!res)
		{
		DWORD dw = GetLastError();
		if(dw == ERROR_INVALID_PARAMETER || dw == ERROR_OUTOFMEMORY)
			{
			seterror("GetSaveFileName", dw);
			return NULL;
			}
		}
	return Py_BuildValue("i", (res?IDOK:IDCANCEL));
	}

static PyObject* PyOfn_GetOpenFileName(PyOfn *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res;
	Py_BEGIN_ALLOW_THREADS
	res = GetOpenFileName(&self->m_ofn);
	Py_END_ALLOW_THREADS
	if(!res)
		{
		DWORD dw = GetLastError();
		if(dw == ERROR_INVALID_PARAMETER || dw == ERROR_OUTOFMEMORY)
			{
			seterror("GetOpenFileName", dw);
			return NULL;
			}
		}
	return Py_BuildValue("i", res);
	}

static PyObject* PyOfn_GetSaveFileName(PyOfn *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	BOOL res;
	Py_BEGIN_ALLOW_THREADS
	res = GetSaveFileName(&self->m_ofn);
	Py_END_ALLOW_THREADS
	if(!res)
		{
		DWORD dw = GetLastError();
		if(dw == ERROR_INVALID_PARAMETER || dw == ERROR_OUTOFMEMORY)
			{
			seterror("GetSaveFileName", dw);
			return NULL;
			}
		}
	return Py_BuildValue("i", res);
	}

static PyObject* PyOfn_SetOFNTitle(PyOfn *self, PyObject *args)
	{
	PyObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	if (obj != Py_None && !PyString_Check(obj))
		{
		seterror("SetOFNTitle", "Argument must be a string, or None");
		return NULL;
		}
	if(obj == Py_None)
		lstrcpy(self->m_szTitle, TEXT("Open"));
	else
		{
		lstrcpy(self->m_szTitle, TextPtr(PyString_AsString(obj)));
		}
	return none();
	}

static PyObject* PyOfn_SetOFNInitialDir(PyOfn *self, PyObject *args)
	{
	PyObject *obj;
	if (!PyArg_ParseTuple(args, "O", &obj))
		return NULL;
	if (obj != Py_None && !PyString_Check(obj))
		{
		seterror("SetOFNInitialDir", "Argument must be a string, or None");
		return NULL;
		}
	if(obj == Py_None)
		self->m_szInitialDir[0] = '\0';
	else
		{
		lstrcpy(self->m_szInitialDir, TextPtr(PyString_AsString(obj)));
		}
	return none();
	}

static PyObject* PyOfn_GetPathName(PyOfn *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_ofn.lpstrFile == NULL)
		return Py_BuildValue("s", "");
	TextPtr tstr(self->m_ofn.lpstrFile);
	return Py_BuildValue("s", tstr.str());
	}

static PyObject* PyOfn_GetFileName(PyOfn *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_ofn.lpstrFileTitle == NULL)
		return Py_BuildValue("s", "");
	TextPtr tstr(self->m_ofn.lpstrFileTitle);
	return Py_BuildValue("s", tstr.str());
	}

PyMethodDef PyOfn::methods[] = {
	{"DoModal", (PyCFunction)PyOfn_DoModal, METH_VARARGS, ""},
	{"GetOpenFileName", (PyCFunction)PyOfn_GetOpenFileName, METH_VARARGS, ""},
	{"GetSaveFileName", (PyCFunction)PyOfn_GetSaveFileName, METH_VARARGS, ""},
	{"SetOFNTitle", (PyCFunction)PyOfn_SetOFNTitle, METH_VARARGS, ""},
	{"SetOFNInitialDir", (PyCFunction)PyOfn_SetOFNInitialDir, METH_VARARGS, ""},
	{"GetPathName", (PyCFunction)PyOfn_GetPathName, METH_VARARGS, ""},
	{"GetFileName", (PyCFunction)PyOfn_GetFileName, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyOfn::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyOfn",			// tp_name
	sizeof(PyOfn),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyOfn::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyOfn::getattr,// tp_getattr
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

	"PyFileDialog Type" // Documentation string
	};
