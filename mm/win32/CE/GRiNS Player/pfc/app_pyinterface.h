
#ifndef INC_APP_PYINTERFACE
#define INC_APP_PYINTERFACE

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

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

#endif  // INC_APP_PYINTERFACE
