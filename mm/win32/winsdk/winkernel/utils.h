#ifndef INC_UTILS
#define INC_UTILS

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef __WINDOWS__
#include <windows.h>
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


// For use from a single thread

#ifdef UNICODE
inline WCHAR* toTEXT(char *p)
	{
	static WCHAR wsz[512];
	MultiByteToWideChar(CP_ACP, 0, p, -1, wsz, 512);
	return wsz;
	}
inline WCHAR* toTEXT(WCHAR *p)
	{
	return p;
	}
#define textchr wcschr

#else

inline char* toTEXT(char *p)
	{
	return p;
	}
inline char* toTEXT(WCHAR *p)
	{
	static char buf[512];
	WideCharToMultiByte(CP_ACP, 0, p, -1, buf, 512, NULL, NULL);		
	return buf;
	}
#define textchr strchr

#endif

#endif  // INC_UTILS
