#ifndef INC_WINUSER_WND
#define INC_WINUSER_WND

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef __WINDOWS__
#include <windows.h>
#endif

PyObject* Winuser_RegisterClassEx(PyObject *self, PyObject *args);
PyObject* Winuser_CreateWindowEx(PyObject *self, PyObject *args);
PyObject* Winuser_CreateWindowFromHandle(PyObject *self, PyObject *args);
PyObject* Winuser_GetDesktopWindow(PyObject *self, PyObject *args);

HINSTANCE GetAppHinstance();

LONG APIENTRY PyWnd_WndProc(HWND hWnd, UINT uMsg, UINT wParam, LONG lParam);
 
#ifdef _WIN32_WCE
#define DECLARE_WND_CLASS(WndClassName) \
static WNDCLASS& GetWndClass() \
{ \
	static WNDCLASS wc = \
	 {  CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS, PyWnd_WndProc, \
		  0, 0, GetAppHinstance(), NULL, NULL, (HBRUSH)(COLOR_WINDOW + 1), NULL, WndClassName}; \
	return wc; \
}

#else // not _WIN32_WCE
#define DECLARE_WND_CLASS(WndClassName) \
static WNDCLASSEX& GetWndClass() \
{ \
	static WNDCLASSEX wc = \
		{ sizeof(WNDCLASSEX), CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS, PyWnd_WndProc, \
		  0, 0, GetAppHinstance(), NULL, NULL, (HBRUSH)(COLOR_WINDOW + 1), NULL, WndClassName, NULL }; \
	return wc; \
}
#endif

inline HWND GetHandleFromPyWnd(PyObject *self)
	{
	struct PyWnd
		{
		PyObject_HEAD
		HWND m_hWnd;
		};
	return ((PyWnd*)self)->m_hWnd;
	}

#ifdef _WIN32_WCE
const UINT WM_CREATE_HOOK = WM_CREATE;
const UINT WM_DESTROY_HOOK = WM_DESTROY;
#else
const UINT WM_CREATE_HOOK = WM_NCCREATE;
const UINT WM_DESTROY_HOOK = WM_NCDESTROY;
#endif

#endif
