#ifndef INC_WINUSER_GLOBALS
#define INC_WINUSER_GLOBALS

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

inline PyObject* none() { Py_INCREF(Py_None); return Py_None;}

extern PyObject *ErrorObject;

inline void seterror(const char *msg){ PyErr_SetString(ErrorObject, msg);}

inline void seterror(const char *funcname, DWORD err)
	{
	char* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 err,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(ErrorObject, "%s failed, error = %x, %s", funcname, err, pszmsg);
	LocalFree(pszmsg);
	}

PyObject* Winuser_RegisterClassEx(PyObject *self, PyObject *args);
PyObject* Winuser_CreateWindowEx(PyObject *self, PyObject *args);
PyObject* Winuser_CreateWindowFromHandle(PyObject *self, PyObject *args);
PyObject* Winuser_GetDesktopWindow(PyObject *self, PyObject *args);

PyObject* Winuser_CreateMenu(PyObject *self, PyObject *args);
PyObject* Winuser_CreateMenuFromHandle(PyObject *self, PyObject *args);
PyObject* Winuser_CreatePopupMenu(PyObject *self, PyObject *args);


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


#endif // INC_WINUSER_GLOBALS

