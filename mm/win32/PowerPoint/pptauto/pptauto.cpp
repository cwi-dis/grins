
/*************************************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

**************************************************************************/

#include "Python.h"

#include <windows.h>

#include "DispatchDriver.h"
#include "msocon.h"
#include "ppcon.h"

static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}

static void seterror(const char *funcname, HRESULT hr)
{
	char* pszmsg;
	FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 hr,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(ErrorObject, "%s failed, error = %x, %s", funcname, hr, pszmsg);
	LocalFree(pszmsg);
}

#define BEGIN_LIFETIME_BLOCK(x) {
#define END_LIFETIME_BLOCK(x) }

static char Export__doc__[] =
"Export slides of a PowerPoint presentation as wmf"
;
static PyObject*
Export(PyObject *self, PyObject *args) 
	{
	char *filename;
	char *outdir = NULL;
	if (!PyArg_ParseTuple(args, "s|s", &filename, &outdir))
		return NULL;

	bool release_outdir = (outdir == NULL);
	if(outdir == NULL)
		{
		outdir = new char[strlen(filename)+16];
		strcpy(outdir, filename);
		char *pd = strrchr(outdir,'.');
		if(pd != NULL)
			{
			*pd = '\0';
			strcat(outdir, "_files");
			}
		}
	OleUtil::Libs olelibs;
	if(FAILED(olelibs.m_hr))
		{
		seterror("OleInitialize", olelibs.m_hr);
		return false;
		}

	HRESULT hr;
	int nslides = 0;

	BEGIN_LIFETIME_BLOCK("app")
	ComAuto::DispatchDriver app;

	Py_BEGIN_ALLOW_THREADS
	hr = app.create(L"PowerPoint.Application");
	Py_END_ALLOW_THREADS
	if(FAILED(hr))
		{
		seterror("create PowerPoint.Application", hr);
		return NULL;
		}

	Py_BEGIN_ALLOW_THREADS
	hr = app.set(L"WindowState", VT_I4, ppWindowMinimized);
	Py_END_ALLOW_THREADS
	if(FAILED(hr))
		{
		return NULL;
		}
	
	Py_BEGIN_ALLOW_THREADS
	hr = app.set(L"Visible", VT_I4, msoTrue);
	Py_END_ALLOW_THREADS
	if(FAILED(hr))
		{
		seterror("set app.Visible", hr);
		return NULL;
		}

	BEGIN_LIFETIME_BLOCK("presentation")
	ComAuto::DispatchDriver presentation;

	BEGIN_LIFETIME_BLOCK("presentations")
	ComAuto::DispatchDriver presentations;

	Py_BEGIN_ALLOW_THREADS
	hr = app.getInterface(L"Presentations", &presentations);
	Py_END_ALLOW_THREADS
	if(FAILED(hr))
		{
		seterror("get app.Presentations", hr);
		return NULL;
		}
	wchar_t * pwfilename = OleUtil::ToWideChar(filename);
	Py_BEGIN_ALLOW_THREADS
	hr = presentations.getInterface(L"Open", &presentation, VT_BSTR, pwfilename);
	Py_END_ALLOW_THREADS
	delete[] pwfilename;
	if(FAILED(hr))
		{
		seterror("presentations.Open()", hr);
		return NULL;
		}
	END_LIFETIME_BLOCK("presentations")

	VARTYPE inParamsInfo[] = {VT_BSTR, VT_I4, VT_I4, 0};
	wchar_t * pwoutdir = OleUtil::ToWideChar(outdir);
	Py_BEGIN_ALLOW_THREADS
	hr = presentation.invoke(L"SaveCopyAs", DISPATCH_METHOD, 
		VT_EMPTY, NULL,
		inParamsInfo, pwoutdir, ppSaveAsMetaFile, msoFalse);
	Py_END_ALLOW_THREADS
	delete[] pwoutdir;
	if(release_outdir) delete[] outdir;
	if(FAILED(hr))
		{
		seterror("presentation.SaveCopyAs()", hr);
		return NULL;
		}

	BEGIN_LIFETIME_BLOCK("slides")
	ComAuto::DispatchDriver slides;
	Py_BEGIN_ALLOW_THREADS
	hr = presentation.getInterface(L"Slides", &slides);
	Py_END_ALLOW_THREADS
	if(FAILED(hr))
		{
		seterror("get presentation.Slides", hr);
		return NULL;
		}
	Py_BEGIN_ALLOW_THREADS
	hr = slides.getNumericValue(L"Count", &nslides);
	Py_END_ALLOW_THREADS
	END_LIFETIME_BLOCK("slides")
	if(FAILED(hr))
		{
		seterror("get Slides.Count", hr);
		return NULL;
		}

	Py_BEGIN_ALLOW_THREADS
	hr = presentation.invoke(L"Close");
	Py_END_ALLOW_THREADS
	if(FAILED(hr))
		{
		seterror("presentation.Close()", hr);
		return NULL;
		}
	END_LIFETIME_BLOCK("presentation")
		
	Py_BEGIN_ALLOW_THREADS
	hr = app.invoke(L"Quit");
	Py_END_ALLOW_THREADS
	if(FAILED(hr))
		{
		seterror("app.Quit()", hr);
		return NULL;
		}
	END_LIFETIME_BLOCK("app")

	return Py_BuildValue("i", nslides);
	}

static struct PyMethodDef pptauto_methods[] = {
	{"Export", (PyCFunction)Export, METH_VARARGS, Export__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static char pptauto_module_documentation[] =
"PowerPoint automation module"
;

extern "C" __declspec(dllexport)
void initpptauto()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("pptauto", pptauto_methods,
		pptauto_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);
	
	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("pptauto.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	if (PyErr_Occurred())
		Py_FatalError("can't initialize module pptauto");
}
