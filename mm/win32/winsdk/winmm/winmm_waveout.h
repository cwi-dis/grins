#ifndef INC_WINMM_WAVEOUT
#define INC_WINMM_WAVEOUT

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Winmm_WaveOutQuery(PyObject *self, PyObject *args);
PyObject* Winmm_WaveOutOpen(PyObject *self, PyObject *args);
PyObject* Winmm_WaveOutFromHandle(PyObject *self, PyObject *args);

#endif  // INC_WINMM_WAVEOUT

