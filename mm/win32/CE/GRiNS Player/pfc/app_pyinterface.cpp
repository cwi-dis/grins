#include "Python.h"

#include <windows.h>

#include "resource.h"

#include "pyinterface.h"
#include "app_pyinterface.h"

#include "app_wnd.h"
#include "app_stdout.h"

#include "ttl.h"

#include "app_pyconfig.h"

class AppPyInterface
	{
	public:
	static bool initialize(HWND hWnd);
	static void finalize();

	private:
	static PyObject* get_application();
	static bool set_mainwnd(PyObject *appobj, PyObject *pwnd);
	static bool set_pysys_stdout(PyObject *pystdout);
	static void restore_pysys_stdout(PyObject *pystdout);
	static PyObject *s_pyapp;
	static PyObject *s_pystdout;
	static PyObject *s_winuser;
	};

PyObject* AppPyInterface::s_pyapp = NULL;
PyObject* AppPyInterface::s_pystdout = NULL;
PyObject* AppPyInterface::s_winuser = NULL;

LRESULT CALLBACK ProfileSelectionDialogFunc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
	switch (message) {
	case WM_INITDIALOG:
		ShowWindow(hDlg, SW_SHOW);
		return TRUE;
	case WM_COMMAND:
		char *name = NULL;
		switch (LOWORD(wParam)) {
		case IDC_BASIC:
			name = "SMIL_BASIC_MODULES";
			break;
		case IDC_PSS4:
			name = "SMIL_PSS4_MODULES";
			break;
		case IDC_PSS5:
			name = "SMIL_PSS5_MODULES";
			break;
		case IDC_LANGUAGE:
			name = "SMIL_20_MODULES";
			break;
		default:
			return TRUE;
		}
		ShowWindow(hDlg, SW_HIDE);
		DestroyWindow(hDlg);
		PyObject *settings = PyInterface::import(TEXT("settings"));
		PyObject *d = PyModule_GetDict(settings); // borrowed reference
		PyObject *l = PyDict_GetItemString(d, name); // borrowed reference
		PyObject *t = Py_BuildValue("(O)", l); // to be deleted
		PyObject *f = PyDict_GetItemString(d, "switch_profile"); // borrowed reference
		PyObject *r = PyEval_CallObject(f, t);
		Py_XDECREF(r);
		Py_XDECREF(t);
		return TRUE;
	}
	return FALSE;
}

HWND CreateSelectionDialog(HWND hWndParent)
{
	HWND hWnd;
	hWnd = CreateDialog(GetApplicationInstance(), MAKEINTRESOURCE(IDD_PROFILE), 
			    hWndParent, (DLGPROC)ProfileSelectionDialogFunc);
	return hWnd;
}

bool AppPyInterface::initialize(HWND hWnd)
	{
	// replace sys.stdout and sys.stderr
	s_pystdout = CreatePyStdOut(hWnd);
	set_pysys_stdout(s_pystdout);

	// import winuser
	s_winuser = PyInterface::import(TEXT("winuser"));
	
	if(s_winuser == NULL)
		{
		MessageBox (NULL, TEXT("Failed to import winuser module"), GetApplicationName(), MB_OK);
		return false;
		}
	
	// get application representation from winuser module
	s_pyapp = get_application();
	if(s_pyapp == NULL)
		{
		MessageBox (NULL, TEXT("Failed to attach to winuser module"), GetApplicationName(), MB_OK);
		return false;
		}

	// set main window in application representation in winuser module
	PyWnd *pywnd = PyWnd::createInstance();
	if(pywnd == NULL)
		{
		MessageBox (NULL, TEXT("Failed to create python wnd"), GetApplicationName(), MB_OK);
		Py_XDECREF(s_pyapp);
		s_pyapp = NULL;
		return false;
		}
	pywnd->m_hWnd = hWnd;
	pywnd->m_phooks = new std::map<UINT, PyObject*>();
	PyWnd::wnds[hWnd] = pywnd;
	if(!set_mainwnd(s_pyapp, (PyObject*)pywnd))
		MessageBox(NULL, TEXT("Failed to set_mainwnd"), GetApplicationName(), MB_OK);

	(void) CreateSelectionDialog(hWnd);

	return true;
	}

void AppPyInterface::finalize()
	{
#ifdef WITH_THREAD
	AcquireThread at(PyInterface::getPyThreadState());
#endif

	Py_XDECREF(s_pyapp);
	s_pyapp = NULL;
	
	Py_XDECREF(s_pystdout);
	s_pystdout = NULL;

	Py_XDECREF(s_winuser);
	s_winuser = NULL;
	}

PyObject* AppPyInterface::get_application()
	{
#ifdef WITH_THREAD
	AcquireThread at(PyInterface::getPyThreadState());
#endif
	PyObject *d = PyModule_GetDict(s_winuser);
	PyObject *ga = PyDict_GetItemString(d, "GetApplication");
	PyObject *arglist = Py_BuildValue("()");
	PyObject *retobj = PyEval_CallObject(ga, arglist);
	Py_DECREF(arglist);
	if (retobj == NULL)
		{
		PyErr_Show();
		PyErr_Clear();
		return NULL;
		}
	return retobj;
	}

bool AppPyInterface::set_mainwnd(PyObject *appobj, PyObject *pwnd)
	{
#ifdef WITH_THREAD
	AcquireThread at(PyInterface::getPyThreadState());
#endif
	PyObject *method = PyObject_GetAttrString(appobj, "SetMainWnd");
	PyObject *arglist = Py_BuildValue("(O)", pwnd);
	PyObject *retobj = PyEval_CallObject(method, arglist);
	Py_DECREF(arglist);
	if (retobj == NULL)
		{
		PyErr_Show();
		PyErr_Clear();
		return false;
		}
	Py_DECREF(retobj);
	return true;
	}

bool AppPyInterface::set_pysys_stdout(PyObject *pystdout)
	{
#ifdef WITH_THREAD
	AcquireThread at(PyInterface::getPyThreadState());
#endif
	PySys_SetObject("stderr", pystdout);
	PySys_SetObject("stdout", pystdout);
	return true;
	}

void AppPyInterface::restore_pysys_stdout(PyObject *pystdout)
	{
#ifdef WITH_THREAD
	AcquireThread at(PyInterface::getPyThreadState());
#endif
	DetachPyStdOut(pystdout);
	}

void *PyInterfaceImport(const TCHAR *psztmodule)
{
	return (void *) PyInterface::import(psztmodule);
}

bool InitializePythonInterface(HWND hWnd)
	{	
	Py_OptimizeFlag = 2;
//	Py_VerboseFlag = 2;
	PyInterface::setPythonHome(python_home);
	if(!PyInterface::initialize(GetApplicationName()))
		{
		MessageBox(NULL, TEXT("PyInterface::initialize failed"), GetApplicationName(), MB_OK);
		return false;
		}

	PyInterface::addto_sys_path_dir(grins_bin);

	AppPyInterface::initialize(hWnd);

	SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_HIGHEST);
	PyInterface::run_command(grins_startup_cmd);
	SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_NORMAL);

	return true;
	}

void FinalizePythonInterface()
	{
	AppPyInterface::finalize();
	PyInterface::finalize();	
	}
