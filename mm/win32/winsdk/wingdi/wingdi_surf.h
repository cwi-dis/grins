#ifndef INC_WINGDI_SURF
#define INC_WINGDI_SURF

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

PyObject* Wingdi_CreateDIBSurface(PyObject *self, PyObject *args);
PyObject* Wingdi_CreateDIBSurfaceFromFile(PyObject *self, PyObject *args);
PyObject* Wingdi_BitBltDIBSurface(PyObject *self, PyObject *args);
PyObject* Wingdi_BltBlendDIBSurface(PyObject *self, PyObject *args);

#endif
