#include "Std.h"
#include "PyCppApi.h"

// consts
#include "StdRma.h"

static char moduleName[] = "rma";
static char errorName[] =  "rma error";
PyObject *module_error;

// Objects served by this module
extern PyObject* EngineObject_CreateInstance(PyObject *self, PyObject *args);

struct constentry {char* s;int n;};


static struct constentry _rma_const[] ={

	// RMA image formats
	{"RMA_RGB",RMA_RGB}, // Windows-compatible RGB formats
	{"RMA_RLE8",RMA_RLE8},
	{"RMA_RLE4",RMA_RLE4},
	{"RMA_BITFIELDS",RMA_BITFIELDS},
	{"RMA_I420",RMA_I420}, // planar YCrCb
	{"RMA_YV12",RMA_YV12}, // planar YVU420
	{"RMA_YUY2",RMA_YUY2}, // packed YUV422
	{"RMA_UYVY",RMA_UYVY}, // packed YUV422
	{"RMA_YVU9",RMA_YVU9}, // Intel YVU9

	// Non-standard FOURCC formats for backward compatibility only
	{"RMA_RGB3",RMA_RGB3_ID},
	{"RMA_RGB555",RMA_RGB555_ID},
	{"RMA_RGB565",RMA_RGB565_ID},
	{"RMA_RGB24",RMA_RGB24_ID},
	{"RMA_8BIT",RMA_8BIT_ID},
	{"RMA_YUV420",RMA_YUV420_ID},
	{NULL,0}
	};

// add symbolic constants to dictionary
static int 
SetItemEnum(PyObject *d,constentry e[])
	{
	PyObject *x;
	for(int i=0;e[i].s;i++)
		{
		x = PyInt_FromLong((long) e[i].n);
		if (x == NULL || PyDict_SetItemString(d, e[i].s, x) < 0)
			return -1;
		Py_DECREF(x);
		}
	return 0;
	}
#define FATAL_ERROR_IF(exp) if(exp){Py_FatalError("can't initialize module rma");return;}	

static struct PyMethodDef module_functions[] = {
    {"CreateEngine",EngineObject_CreateInstance,1}, 
	{NULL,NULL}
};

PY_API
void initrma()
{
	PyObject *module = Py_InitModule(moduleName,module_functions);
	PyObject *dict = PyModule_GetDict(module);
	module_error = PyString_FromString(errorName);
	PyDict_SetItemString(dict,"error",module_error);
	PyObject *copyright = PyString_FromString("Copyright 1999-2000 Oratrix");
	PyDict_SetItemString(dict,"copyright",copyright);
	Py_XDECREF(copyright);
	
	FATAL_ERROR_IF(SetItemEnum(dict,_rma_const)<0)

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module ddraw");
	
}
