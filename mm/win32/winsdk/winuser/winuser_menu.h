#ifndef INC_WINUSER_MENU
#define INC_WINUSER_MENU

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Winuser_CreateMenu(PyObject *self, PyObject *args);
PyObject* Winuser_CreatePopupMenu(PyObject *self, PyObject *args);
PyObject* Winuser_CreateMenuFromHandle(PyObject *self, PyObject *args);

#endif

