#ifndef INC_WINGDI_BMP
#define INC_WINGDI_BMP

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

PyObject* Wingdi_CreateBitmapFromHandle(PyObject *self, PyObject *args);
PyObject* Wingdi_CreateCompatibleBitmap(PyObject *self, PyObject *args);
PyObject* Wingdi_LoadImage(PyObject *self, PyObject *args);

PyObject* CreateBitmapFromHandle(HBITMAP hBmp, int nWidth, int nHeight);


#ifndef LR_LOADFROMFILE
#define LR_LOADFROMFILE			0x0010
#endif

#ifndef LR_CREATEDIBSECTION
#define LR_CREATEDIBSECTION     0x2000
#endif

#endif
