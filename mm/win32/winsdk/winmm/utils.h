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

#endif  // INC_UTILS
