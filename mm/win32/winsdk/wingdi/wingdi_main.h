#ifndef INC_WINGDI_MAIN
#define INC_WINGDI_MAIN

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Wingdi_IntersectRect(PyObject *self, PyObject *args);
PyObject* Wingdi_UnionRect(PyObject *self, PyObject *args);

#endif
