#ifndef INC_APP_STDOUT
#define INC_APP_STDOUT

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

#define MENU_HEIGHT 26

PyObject* CreatePyStdOut(HWND hWndParent);
void DetachPyStdOut(PyObject *obj);

#endif


