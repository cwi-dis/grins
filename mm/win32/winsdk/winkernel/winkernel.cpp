
/*************************************************************************
Copyright 1991-2001 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

/*************************************************************************/
#include <windows.h>

#include "Python.h"

#include "utils.h"

PyObject *WinKernel_ErrorObject;

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

static PyObject* SetThreadPriority(PyObject *self, PyObject *args)
{
	int nPriority;
	if (!PyArg_ParseTuple(args, "i", &nPriority))
		return NULL;
	if(!SetThreadPriority(GetCurrentThread(), nPriority)){
		seterror("SetThreadPriority", GetLastError());
		return NULL;
		}
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
	HMODULE hModule = GetModuleHandle(TextPtr(filename));
	if(hModule == NULL) 
		{
		hModule = LoadLibraryEx(TextPtr(filename), NULL, flags);
		if(hModule == NULL) 
			{
			seterror("LoadLibrary", GetLastError());
			return NULL;
			}
		}
	return Py_BuildValue("i", hModule);
}

static PyObject* FindResource(PyObject *self, PyObject *args)
{
	HMODULE hModule;
	UINT rcId;
	UINT rcType; // ex: RT_DIALOG
	if (!PyArg_ParseTuple(args, "iii", &hModule, &rcId, &rcType))
		return NULL;
	HRSRC hrsrc = FindResource(hModule, MAKEINTRESOURCE(rcId), (LPCTSTR)rcType);
	if(hrsrc == NULL) 
		{
		seterror("FindResource", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", hrsrc);
}

typedef void* (__stdcall *LRF)(struct HINSTANCE__ *, TCHAR *);

static PyObject* LoadResourceType(const char *what, LRF fn, PyObject *self, PyObject *args)
{
	HMODULE hModule;
	UINT rcId;
	if (!PyArg_ParseTuple(args, "ii", &hModule, &rcId))
		return NULL;
	HANDLE handle = (*fn)(hModule, MAKEINTRESOURCE(rcId));
	if(handle == NULL) 
		{
		seterror("LoadAccelerators", GetLastError());
		return NULL;
		}
	return Py_BuildValue("i", handle);
}

static PyObject* Winkernel_LoadAccelerators(PyObject *self, PyObject *args)
	{return LoadResourceType("LoadAccelerators", (LRF)LoadAccelerators, self, args);}

static PyObject* Winkernel_LoadBitmap(PyObject *self, PyObject *args)
	{return LoadResourceType("LoadBitmap", (LRF)LoadBitmap, self, args);}

static PyObject* Winkernel_LoadCursor(PyObject *self, PyObject *args)
	{return LoadResourceType("LoadCursor", (LRF)LoadCursor, self, args);}

static PyObject* Winkernel_LoadIcon(PyObject *self, PyObject *args)
	{return LoadResourceType("LoadIcon", (LRF)LoadIcon, self, args);}

static PyObject* Winkernel_LoadMenu(PyObject *self, PyObject *args)
	{return LoadResourceType("LoadMenu", (LRF)LoadMenu, self, args);}

	
static struct PyMethodDef winkernel_methods[] = {
	{"GetVersionEx", (PyCFunction)GetVersionEx, METH_VARARGS, ""},
	{"Sleep", (PyCFunction)Sleep, METH_VARARGS, ""},
	{"SetThreadPriority", (PyCFunction)SetThreadPriority, METH_VARARGS, ""},
	{"GetTickCount", (PyCFunction)GetTickCount, METH_VARARGS, ""},
	{"LoadLibrary", (PyCFunction)LoadLibrary, METH_VARARGS, ""},
	{"FindResource", (PyCFunction)FindResource, METH_VARARGS, ""},
	{"LoadAccelerators", (PyCFunction)Winkernel_LoadAccelerators, METH_VARARGS, ""},
	{"LoadBitmap", (PyCFunction)Winkernel_LoadBitmap, METH_VARARGS, ""},
	{"LoadCursor", (PyCFunction)Winkernel_LoadCursor, METH_VARARGS, ""},
	{"LoadIcon", (PyCFunction)Winkernel_LoadIcon, METH_VARARGS, ""},
	{"LoadMenu", (PyCFunction)Winkernel_LoadMenu, METH_VARARGS, ""},
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
	WinKernel_ErrorObject = PyString_FromString("winkernel.error");
	PyDict_SetItemString(d, "error", WinKernel_ErrorObject);


	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module winkernel");
}
