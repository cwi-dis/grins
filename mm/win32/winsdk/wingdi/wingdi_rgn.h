#ifndef INC_WINGDI_RGN
#define INC_WINGDI_RGN

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Wingdi_CreateRectRgn(PyObject *self, PyObject *args);
PyObject* Wingdi_CreatePolygonRgn(PyObject *self, PyObject *args);
PyObject* Wingdi_PathToRegion(PyObject *self, PyObject *args);
PyObject* Wingdi_CombineRgn(PyObject *self, PyObject *args);

inline HRGN GetHandleFromPyRgn(PyObject *self)
	{
	struct PyRgn
		{
		PyObject_HEAD
		HRGN m_hRgn;
		};
	return ((PyRgn*)self)->m_hRgn;
	}

#endif
