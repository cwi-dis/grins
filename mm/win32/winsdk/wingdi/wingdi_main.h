#ifndef INC_WINGDI_MAIN
#define INC_WINGDI_MAIN

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Wingdi_DeleteObject(PyObject *self, PyObject *args);
PyObject* Wingdi_GetStockObject(PyObject *self, PyObject *args);
PyObject* Wingdi_ExtCreatePen(PyObject *self, PyObject *args);
PyObject* Wingdi_CreateSolidBrush(PyObject *self, PyObject *args);
PyObject* Wingdi_CreateBrushIndirect(PyObject *self, PyObject *args);
PyObject* Wingdi_CreateFontIndirect(PyObject *self, PyObject *args);

PyObject* Wingdi_IntersectRect(PyObject *self, PyObject *args);
PyObject* Wingdi_UnionRect(PyObject *self, PyObject *args);

PyObject* Wingdi_GetRGBValues(PyObject *self, PyObject *args);

#endif
