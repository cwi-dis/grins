
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


static char Sleep__doc__[] =
"suspends the execution of the current thread for the specified milliseconds interval"
;
static PyObject*
Sleep(PyObject *self, PyObject *args)
{
	DWORD dwMilliseconds;
	if (!PyArg_ParseTuple(args, "i", &dwMilliseconds))
		return NULL;
	Sleep(dwMilliseconds);
	Py_INCREF(Py_None);
	return Py_None;
}

	
static struct PyMethodDef winkernel_methods[] = {
	{"Sleep", (PyCFunction)Sleep, METH_VARARGS, Sleep__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
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

	// add symbolic constants
	//FATAL_ERROR_IF(SetItemEnum(d,_sdk)<0)

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module winkernel");
}
