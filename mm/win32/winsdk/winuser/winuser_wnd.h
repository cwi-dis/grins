#ifndef INC_WINUSER_WND
#define INC_WINUSER_WND

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

PyObject* Winuser_RegisterClassEx(PyObject *self, PyObject *args);
PyObject* Winuser_CreateWindowEx(PyObject *self, PyObject *args);
PyObject* Winuser_CreateWindowFromHandle(PyObject *self, PyObject *args);
PyObject* Winuser_GetDesktopWindow(PyObject *self, PyObject *args);

HINSTANCE GetAppHinstance();

LONG APIENTRY PyWnd_WndProc(HWND hWnd, UINT uMsg, UINT wParam, LONG lParam);

#define DECLARE_WND_CLASS(WndClassName) \
static WNDCLASSEX& GetWndClass() \
{ \
	static WNDCLASSEX wc = \
		{ sizeof(WNDCLASSEX), CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS, PyWnd_WndProc, \
		  0, 0, GetAppHinstance(), NULL, NULL, (HBRUSH)(COLOR_WINDOW + 1), NULL, WndClassName, NULL }; \
	return wc; \
}


#endif
