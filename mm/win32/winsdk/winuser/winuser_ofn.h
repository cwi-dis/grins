#ifndef INC_WINUSER_OFN
#define INC_WINUSER_OFN

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef __WINDOWS__
#include <windows.h>
#endif

#ifndef _INC_COMMDLG
#include <commdlg.h>
#endif

extern HINSTANCE GetAppHinstance();

PyObject* Winuser_CreateFileDialog(PyObject *self, PyObject *args);


#endif

