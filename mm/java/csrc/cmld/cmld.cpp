
/**************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

***************************************************************************/

#include <stdafx.h>

#include "Python.h"


static PyObject *ErrorObject;


void seterror(const char *msg){ PyErr_SetString(ErrorObject, msg);}


static struct PyMethodDef cmld_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


static char cmld_module_documentation[] =
"Windows Media Format API"
;

extern "C" __declspec(dllexport)
void initcmld()
{
	PyObject *m, *d;
	
	// Create the module and add the functions
	m = Py_InitModule4("cmld", cmld_methods,
		cmld_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("cmld.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module cmld");
}



