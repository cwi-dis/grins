#ifndef INC_WINMM_VIDEO
#define INC_WINMM_VIDEO

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Winmm_CreateVideoPlayerFromFile(PyObject *self, PyObject *args);
PyObject* Winmm_GXOpenDisplay(PyObject *self, PyObject *args);
PyObject* Winmm_GXCloseDisplay(PyObject *self, PyObject *args);

#endif  // INC_WINMM_VIDEO

