#ifndef INC_WINUSER_MAIN
#define INC_WINUSER_MAIN

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Winuser_MessageLoop(PyObject *self, PyObject *args);
PyObject* Winuser_PostQuitMessage(PyObject *self, PyObject *args);
PyObject* Winuser_MessageBox(PyObject *self, PyObject *args);
PyObject* Winuser_GetSystemMetrics(PyObject *self, PyObject *args);
PyObject* Winuser_GetSysColor(PyObject *self, PyObject *args);
PyObject* Winuser_GetDC(PyObject *self, PyObject *args);
PyObject* Winuser_LoadStandardCursor(PyObject *self, PyObject *args);
PyObject* Winuser_LoadCursor(PyObject *self, PyObject *args);
PyObject* Winuser_SetCursor(PyObject *self, PyObject *args);
PyObject* Winuser_ShellExecute(PyObject *self, PyObject *args);
PyObject* Winuser_GetFileSize(PyObject *self, PyObject *args);


#endif

