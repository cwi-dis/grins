#ifndef INC_WINUSER_OFN
#define INC_WINUSER_OFN

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

extern HINSTANCE GetAppHinstance();

PyObject* Winuser_CreateFileDialog(PyObject *self, PyObject *args);


#endif

