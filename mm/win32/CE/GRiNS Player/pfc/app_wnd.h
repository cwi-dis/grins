#ifndef INC_APP_WND
#define INC_APP_WND

#ifndef Py_PYTHON_H
#include "Python.h"
#endif

#ifndef INC_PYINTERFACE
#include "pyinterface.h"
#endif

#ifndef _WINDOWS_
#include <windows.h>
#endif

#pragma warning(disable: 4786) // long names trunc (debug)
#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <map>

struct PyWnd
	{
	PyObject_HEAD
	HWND m_hWnd;
	std::map<UINT, PyObject*> *m_phooks;

	static PyTypeObject type;
	static PyMethodDef methods[];
	static std::map<HWND, PyWnd*> wnds;
	static PyWnd *createInstance()
		{
#ifdef WITH_THREAD
		AcquireThread at(PyInterface::getPyThreadState());
#endif
		PyWnd *instance = PyObject_NEW(PyWnd, &type);
		if (instance == NULL) return NULL;
		instance->m_hWnd = NULL;
		instance->m_phooks = NULL;
		return instance;
		}

	static void dealloc(PyWnd *instance) 
		{ 
		if(instance->m_phooks != NULL)
			{
			std::map<UINT, PyObject*>::iterator it;
			for(it = instance->m_phooks->begin();it!=instance->m_phooks->end();it++)
				Py_XDECREF((*it).second);
			delete instance->m_phooks;
			}
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyWnd *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

#endif // INC_APP_WND
