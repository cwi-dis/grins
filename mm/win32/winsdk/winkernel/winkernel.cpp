
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/

#include "Python.h"

#include <windows.h>

static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}

static void
seterror(const char *funcname, DWORD err)
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

static PyObject* GetVersionEx(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	OSVERSIONINFO vi;
	memset(&vi, 0, sizeof(OSVERSIONINFO));
	vi.dwOSVersionInfoSize = sizeof(OSVERSIONINFO); 
	BOOL res = GetVersionEx(&vi);
	if(!res){
		seterror("GetVersionEx", GetLastError());
		return NULL;
		}
	return Py_BuildValue("iiiis", vi.dwMajorVersion, vi.dwMinorVersion, vi.dwBuildNumber, 
		vi.dwPlatformId, vi.szCSDVersion);
}

static PyObject* Sleep(PyObject *self, PyObject *args)
{
	DWORD dwMilliseconds;
	if (!PyArg_ParseTuple(args, "i", &dwMilliseconds))
		return NULL;
	Py_BEGIN_ALLOW_THREADS
	Sleep(dwMilliseconds);
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* GetTickCount(PyObject *self, PyObject *args)
{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	DWORD ticks;
	Py_BEGIN_ALLOW_THREADS
	ticks = GetTickCount();
	Py_END_ALLOW_THREADS
	return Py_BuildValue("l",ticks);
}

static PyObject* LoadLibrary(PyObject *self, PyObject *args)
{
	char *filename;
	int flags = 0;
	if (!PyArg_ParseTuple(args, "s|i", &filename, &flags))
		return NULL;
	HMODULE hModule = GetModuleHandle(filename);
	if(hModule == NULL) 
		{
		hModule = LoadLibraryEx(filename, NULL, flags);
		if(hModule == NULL) 
			{
			seterror("LoadLibrary", GetLastError());
			return NULL;
			}
		}
	return Py_BuildValue("i", hModule);
}
	
static struct PyMethodDef winkernel_methods[] = {
	{"GetVersionEx", (PyCFunction)GetVersionEx, METH_VARARGS, ""},
	{"Sleep", (PyCFunction)Sleep, METH_VARARGS, ""},
	{"GetTickCount", (PyCFunction)GetTickCount, METH_VARARGS, ""},
	{"LoadLibrary", (PyCFunction)LoadLibrary, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

/////////////////////////////////////

static char winkernel_module_documentation[] =
"Windows kernel module"
;

extern "C" __declspec(dllexport)
void initwinkernel()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("winkernel", winkernel_methods,
		winkernel_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("winkernel.error");
	PyDict_SetItemString(d, "error", ErrorObject);


	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module winkernel");
}
