#include "Python.h"

#include <windows.h>

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
	static PyObject *winuser;
	};

PyObject* AppPyInterface::s_pyapp = NULL;
PyObject* AppPyInterface::s_pystdout = NULL;
PyObject* AppPyInterface::winuser = NULL;

bool AppPyInterface::initialize(HWND hWnd)
	{
	s_pystdout = CreatePyStdOut(hWnd);
	set_pysys_stdout(s_pystdout);
		{
			AcquireThread at(PyInterface::getPyThreadState());
			winuser = PyImport_ImportModule("winuser");
			if (winuser == NULL) {
				MessageBox (NULL, TEXT("Failed to import winuser module"), GetApplicationName(), MB_OK);
				return false;
			}
		}
	s_pyapp = get_application();
	if(s_pyapp == NULL)
		{
		MessageBox (NULL, TEXT("Failed to attach to winuser module"), GetApplicationName(), MB_OK);
		return false;
		}

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

	return true;
	}

void AppPyInterface::finalize()
	{
	AcquireThread at(PyInterface::getPyThreadState());
	restore_pysys_stdout(s_pystdout);
	Py_XDECREF(s_pystdout);
	Py_XDECREF(s_pyapp);
	s_pyapp = NULL;
	}

PyObject* AppPyInterface::get_application()
	{
	AcquireThread at(PyInterface::getPyThreadState());
	PyObject *d = PyModule_GetDict(winuser);
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
	AcquireThread at(PyInterface::getPyThreadState());
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
	AcquireThread at(PyInterface::getPyThreadState());
	PySys_SetObject("stderr", pystdout);
	PySys_SetObject("stdout", pystdout);
	return true;
	}

void AppPyInterface::restore_pysys_stdout(PyObject *pystdout)
	{
	AcquireThread at(PyInterface::getPyThreadState());
	DetachPyStdOut(pystdout);
	}

bool InitializePythonInterface(HWND hWnd)
	{	
	PyInterface::setPythonHome(python_home);
	if(!PyInterface::initialize(GetApplicationName()))
		{
		MessageBox(NULL, TEXT("PyInterface::initialize failed"), GetApplicationName(), MB_OK);
		return false;
		}

	PyInterface::addto_sys_path_dir(grins_bin);
	AppPyInterface::initialize(hWnd);

	PyInterface::run_command(grins_startup_cmd);

	return true;
	}

void FinalizePythonInterface()
	{
	AppPyInterface::finalize();
	PyInterface::finalize();	
	}
