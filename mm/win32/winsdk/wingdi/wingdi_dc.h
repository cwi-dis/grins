#ifndef INC_WINGDI_REG
#define INC_WINGDI_REG

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

PyObject* Wingdi_CreateDCFromHandle(PyObject *self, PyObject *args);
PyObject* Wingdi_GetDesktopDC(PyObject *self, PyObject *args);

inline HDC GetHandleFromPyDC(PyObject *self)
	{
	struct PyRgn
		{
		PyObject_HEAD
		HDC m_hDC;
		};
	return ((PyRgn*)self)->m_hDC;
	}

#endif
