#ifndef INC_UTILS
#define INC_UTILS

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef __WINDOWS__
#include <windows.h>
#endif

#ifndef INC_CHARCONV
#include "../common/charconv.h"
#endif

extern PyObject *ErrorObject;

inline PyObject* none() { Py_INCREF(Py_None); return Py_None;}

extern PyObject *ErrorObject;

inline void seterror(const char *msg){ PyErr_SetString(ErrorObject, msg);}

inline void seterror(const char *funcname, const char *msg)
	{
	PyErr_Format(ErrorObject, "%s failed, %s", funcname, msg);
	PyErr_SetString(ErrorObject, msg);
	}

inline void seterror(const char *funcname, DWORD err)
	{
	TCHAR* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 err,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (TCHAR*) &pszmsg,
		 0,
		 NULL 
		);
	TextPtr tmsg(pszmsg);
	PyErr_Format(ErrorObject, "%s failed, error = %x, %s", funcname, err, tmsg.str());
	LocalFree(pszmsg);
	}

inline int GetObjHandle(PyObject *obj)
	{
	if(obj==Py_None)
		return 0;
	if(PyInt_Check(obj))
		return PyInt_AsLong(obj);
	struct WrapperObj { PyObject_HEAD; int m_h;};
	return ((WrapperObj*)obj)->m_h;
	}

#ifndef INC_SURFACE
#include "../common/surface.h"
#endif

struct DIBSurfHeader
	{
	PyObject_HEAD
	HBITMAP m_hBmp;
	surface<color_repr_t> *m_psurf;
	bool m_is_transparent;
	BYTE m_rgb[3];
	};

inline surface<color_repr_t>* GetPyDIBSurfPtr(PyObject *obj)
	{
	if(obj==Py_None)
		return 0;
	return ((DIBSurfHeader*)obj)->m_psurf;
	}

#endif  // INC_UTILS
