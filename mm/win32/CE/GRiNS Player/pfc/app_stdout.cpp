#include "Python.h"

#include <windows.h>

#include "app_stdout.h"

#include "ttl.h"
#include "resource.h"

#include "pyinterface.h"

#include "charconv.h"
#include "strutil.h"

// PyStdOut extends PyWnd
#include "app_wnd.h"

struct PyStdOut
	{
	PyObject_HEAD
	HWND m_hWnd;
	int m_softspace;

	static PyTypeObject type;
	static PyMethodDef methods[];
	static PyStdOut *createInstance(HWND hWnd=NULL)
		{
		AcquireThread at(PyInterface::getPyThreadState());
		PyStdOut *instance = PyObject_NEW(PyStdOut, &type);
		if (instance == NULL) return NULL;
		instance->m_hWnd = hWnd;
		instance->m_softspace = 1;
		return instance;
		}

	static void dealloc(PyStdOut *instance) 
		{ 
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyStdOut *instance, char *name)
		{ 
		if (strcmp(name, "softspace") == 0)
			return PyInt_FromLong(instance->m_softspace);
		PyObject *attr = Py_FindMethod(methods, (PyObject*)instance, name);
		if (attr != NULL)
			return attr;
		PyErr_Clear();
		return Py_FindMethod(PyWnd::methods, (PyObject*)instance, name);
		}

	static void append(HWND hWnd, const TCHAR *text)
		{
		if(!IsWindow(hWnd)) return;
		HWND hEditBox = GetDlgItem(hWnd, IDC_STDOUT);
		if(hEditBox == NULL) return;
		int len  = SendMessage(hEditBox, WM_GETTEXTLENGTH, 0, 0);
		SendMessage(hEditBox, EM_SETSEL, (WPARAM)len, (LPARAM)len);
		SendMessage(hEditBox, EM_REPLACESEL, (WPARAM)0, (LPARAM)text);
		}
	};

LRESULT CALLBACK PyStdOutDialogFunc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
	{
	if(message == WM_INITDIALOG)
		{
		std::basic_string<TCHAR> tstr = PyInterface::get_copyright();
		PyStdOut::append(hDlg, tstr.c_str());
		ShowWindow(hDlg, SW_SHOW);
		SetFocus(GetParent(hDlg));
		return TRUE; 
		}
	else if(message == WM_CLOSE)
		{
		ShowWindow(hDlg, SW_HIDE);
		return TRUE;
		}
	else if(message == WM_COMMAND)
		{
		WORD cmdid = LOWORD(wParam);
		if(cmdid == IDOK || cmdid == IDCANCEL)
			{
			ShowWindow(hDlg, SW_HIDE);
			return TRUE;
			}
		}
    return FALSE;
	}

PyObject* CreatePyStdOut(HWND hWndParent)
	{
	HWND hWnd = CreateDialog(GetApplicationInstance(), MAKEINTRESOURCE(IDD_PYSTDOUT), 
		hWndParent, (DLGPROC)PyStdOutDialogFunc);
	RECT rc;
	SystemParametersInfo(SPI_GETWORKAREA, 0, &rc, 0);
	int w = rc.right-rc.left, h = rc.bottom-rc.top;
	MoveWindow(hWnd, rc.left+2, rc.bottom-h/3-MENU_HEIGHT, w-4, h/3, 0);
	GetClientRect(hWnd, &rc);
	MoveWindow(GetDlgItem(hWnd, IDC_STDOUT), 4, 4, rc.right-rc.left-8, rc.bottom-rc.top-8, 0);
	return (PyObject*)PyStdOut::createInstance(hWnd);
	}

void DetachPyStdOut(PyObject *obj)
	{
	PyStdOut *p = (PyStdOut*)obj;
	DestroyWindow(p->m_hWnd);
	p->m_hWnd = NULL;
	}


///////////////////////////////////////////
// module

static PyObject* PyStdOut_write(PyStdOut *self, PyObject *args)
	{
	char *psz;
	if(!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	std::string str = fixendl(psz);
#ifdef UNICODE
	int n = str.length()+1;
	WCHAR *ptext = new WCHAR[n];
	MultiByteToWideChar(CP_ACP, 0, str.c_str(), n, ptext, n);
	PyStdOut::append(self->m_hWnd, ptext);
	delete[] ptext;
#else
	PyStdOut::append(self->m_hWnd, str.c_str());
#endif
	ShowWindow(self->m_hWnd, SW_SHOW);
	SetFocus(GetParent(self->m_hWnd));
	return none();
	}

static PyObject* PyStdOut_isatty(PyStdOut *self, PyObject *args) 
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return PyInt_FromLong(0);
	}

static PyObject* PyStdOut_flush(PyStdOut *self, PyObject *args) 
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return none();
	}

static PyObject* PyStdOut_reset(PyStdOut *self, PyObject *args) 
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return none();
	}
static PyObject* PyStdOut_close(PyStdOut *self, PyObject *args) 
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	ShowWindow(self->m_hWnd, SW_HIDE);
	return none();
	}


PyMethodDef PyStdOut::methods[] = {
	{"write", (PyCFunction)PyStdOut_write, METH_VARARGS, ""},
	{"isatty", (PyCFunction)PyStdOut_isatty, METH_VARARGS, ""},
	{"flush", (PyCFunction)PyStdOut_flush, METH_VARARGS, ""},
	{"reset", (PyCFunction)PyStdOut_reset, METH_VARARGS, ""},
	{"close", (PyCFunction)PyStdOut_close, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};


PyTypeObject PyStdOut::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyStdOut",			// tp_name
	sizeof(PyStdOut),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyStdOut::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyStdOut::getattr,// tp_getattr
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

	"PyStdOut Type" // Documentation string
	};

