#include "Python.h"

#include <windows.h>

#include "app_pyinterface.h"

#include "app_wnd.h"
#include "ttl.h"

class AppPyInterface
	{
	public:
	static bool initialize(HWND hWnd);
	static void finalize();

	private:
	static PyObject* get_application();
	static bool set_mainwnd(PyObject *appobj, PyObject *pwnd);
	static PyObject *s_pyapp;
	};

PyObject* AppPyInterface::s_pyapp;

bool AppPyInterface::initialize(HWND hWnd)
	{
	PyInterface::run_command(TEXT("import winuser"));
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
	Py_XDECREF(s_pyapp);
	s_pyapp = NULL;
	}

PyObject* AppPyInterface::get_application()
	{
	AcquireThread at(PyInterface::getPyThreadState());
	PyObject *m = PyImport_AddModule("winuser");
	if (m == NULL)
		{
		PyErr_Show();
		PyErr_Clear();
		return NULL;
		}
	PyObject *d = PyModule_GetDict(m);
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


bool InitializePythonInterface(HWND hWnd)
	{		
	if(!PyInterface::initialize(GetApplicationName()))
		{
		MessageBox(NULL, TEXT("PyInterface::initialize failed"), GetApplicationName(), MB_OK);
		return false;
		}

	TCHAR dir[] = TEXT("\\Windows\\cmif\\bin\\wince");
	PyInterface::addto_sys_path_dir(dir);
	AppPyInterface::initialize(hWnd);

	PyInterface::run_command(TEXT("import startup\nstartup.main()"));

	return true;
	}

void FinalizePythonInterface()
	{
	AppPyInterface::finalize();
	PyInterface::finalize();	
	}
