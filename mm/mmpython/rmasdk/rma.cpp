#include "std.h"
#include "PyCppApi.h"

static char moduleName[] = "rma";
static char errorName[] =  "rma error";
PyObject *module_error;

// Objects served by this module
extern PyObject* EngineObject_CreateInstance(PyObject *self, PyObject *args);
//extern PyObject* PlayerObject_CreateInstance(PyObject *self, PyObject *args);

static struct PyMethodDef module_functions[] = {
    {"CreateEngine",EngineObject_CreateInstance,1}, 
//    {"CreatePlayer",PlayerObject_CreateInstance,1}, 
	{NULL,NULL}
};

PY_API
void initrma()
{
	PyObject *module = Py_InitModule(moduleName,module_functions);
	PyObject *dict = PyModule_GetDict(module);
	module_error = PyString_FromString(errorName);
	PyDict_SetItemString(dict,"error",module_error);
	PyObject *copyright = PyString_FromString("Copyright 1999 Oratrix");
	PyDict_SetItemString(dict,"copyright",copyright);
	Py_XDECREF(copyright);
}
