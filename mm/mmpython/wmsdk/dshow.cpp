/***********************************************************
Copyright 1991-1999 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <streams.h>
#include <stdio.h>
#include <UUIDS.H> // CLSID_FilterGraph,...

#pragma comment (lib,"winmm.lib")
#pragma comment (lib,"amstrmid.lib")
#pragma comment (lib,"guids.lib")
#pragma comment (lib,"strmbase.lib")


static PyObject *ErrorObject;

#define RELEASE(x) if(x) x->Release();x=NULL;

static void
seterror(const char *funcname, HRESULT hr)
{
	char* pszmsg;
	::FormatMessage( 
		 FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
		 NULL,
		 hr,
		 MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
		 (LPTSTR) &pszmsg,
		 0,
		 NULL 
		);
	PyErr_Format(ErrorObject, "%s failed, error = %s", funcname, pszmsg);
	LocalFree(pszmsg);
}


/* Declarations for objects of type MMStream */

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IGraphBuilder* pGraphBuilder;
} GraphBuilderObject;

staticforward PyTypeObject GraphBuilderType;

static GraphBuilderObject *
newGraphBuilderObject()
{
	GraphBuilderObject *self;

	self = PyObject_NEW(GraphBuilderObject, &GraphBuilderType);
	if (self == NULL)
		return NULL;
	self->pGraphBuilder = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IBaseFilter* pFilter;
} BaseFilterObject;

staticforward PyTypeObject BaseFilterType;

static BaseFilterObject *
newBaseFilterObject()
{
	BaseFilterObject *self;

	self = PyObject_NEW(BaseFilterObject, &BaseFilterType);
	if (self == NULL)
		return NULL;
	self->pFilter = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IPin* pPin;
} PinObject;

staticforward PyTypeObject PinType;

static PinObject *
newPinObject()
{
	PinObject *self;

	self = PyObject_NEW(PinObject, &PinType);
	if (self == NULL)
		return NULL;
	self->pPin = NULL;
	/* XXXX Add your own initializers here */
	return self;
}




////////////////////////////////////////////////////

static char GraphBuilder_AddSourceFilter__doc__[] =
""
;


static PyObject *
GraphBuilder_AddSourceFilter(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	char *pszFile;
	BaseFilterObject *pBFO;
	if (!PyArg_ParseTuple(args, "s", &pszFile))
		return NULL;
	pBFO = newBaseFilterObject();
	WCHAR wPath[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,pszFile,-1,wPath,MAX_PATH);
	res = self->pGraphBuilder->AddSourceFilter(wPath,L"File reader",&pBFO->pFilter);
	if (FAILED(res)) {
		seterror("GraphBuilder_AddSourceFilter", res);
		pBFO->pFilter=NULL;
		Py_DECREF(pBFO);
		return NULL;
	}
	return (PyObject *) pBFO;
}

static char GraphBuilder_AddFilter__doc__[] =
""
;

static PyObject *
GraphBuilder_AddFilter(GraphBuilderObject *self, PyObject *args)
{
	HRESULT res;
	char *psz;
	BaseFilterObject *pBFO;
	if (!PyArg_ParseTuple(args, "Os", &psz,&pBFO))
		return NULL;

	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,wsz,MAX_PATH);
	res = self->pGraphBuilder->AddFilter(pBFO->pFilter,wsz);
	if (FAILED(res)) {
		seterror("GraphBuilder_AddFilter", res);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef GraphBuilder_methods[] = {
	{"AddSourceFilter", (PyCFunction)GraphBuilder_AddSourceFilter, METH_VARARGS, GraphBuilder_AddSourceFilter__doc__},
	{"AddFilter", (PyCFunction)GraphBuilder_AddFilter, METH_VARARGS, GraphBuilder_AddFilter__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


static void
GraphBuilder_dealloc(GraphBuilderObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pGraphBuilder);
	PyMem_DEL(self);
}

static PyObject *
GraphBuilder_getattr(GraphBuilderObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(GraphBuilder_methods, (PyObject *)self, name);
}

static char GraphBuilderType__doc__[] =
""
;

static PyTypeObject GraphBuilderType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"GraphBuilder",			/*tp_name*/
	sizeof(GraphBuilderObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)GraphBuilder_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)GraphBuilder_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	GraphBuilderType__doc__ /* Documentation string */
};

// End of code for GraphBuilder object 
/////////////////////////////////////////////////////////////


static char BaseFilter_FindPin__doc__[] =
""
;

static PyObject *
BaseFilter_FindPin(BaseFilterObject *self, PyObject *args)
{
	HRESULT res;
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	PinObject *obj = newPinObject();
	WCHAR wsz[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,psz,-1,wsz,MAX_PATH);
	res = self->pFilter->FindPin(wsz,&obj->pPin);
	if (FAILED(res)) {
		seterror("BaseFilter_FindPin", res);
		Py_DECREF(obj);
		obj->pPin=NULL;
		return NULL;
	}
	return (PyObject *) obj;
}

static struct PyMethodDef BaseFilter_methods[] = {
	{"FindPin", (PyCFunction)BaseFilter_FindPin, METH_VARARGS, BaseFilter_FindPin__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
BaseFilter_dealloc(BaseFilterObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pFilter);
	PyMem_DEL(self);
}

static PyObject *
BaseFilter_getattr(BaseFilterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(BaseFilter_methods, (PyObject *)self, name);
}

static char BaseFilterType__doc__[] =
""
;

static PyTypeObject BaseFilterType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"BaseFilter",			/*tp_name*/
	sizeof(BaseFilterObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)BaseFilter_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)BaseFilter_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	BaseFilterType__doc__ /* Documentation string */
};

// End of code for BaseFilter object 
////////////////////////////////////////////

static struct PyMethodDef Pin_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
Pin_dealloc(PinObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pPin);
	PyMem_DEL(self);
}

static PyObject *
Pin_getattr(BaseFilterObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(Pin_methods, (PyObject *)self, name);
}

static char PinType__doc__[] =
""
;

static PyTypeObject PinType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Pin",			/*tp_name*/
	sizeof(PinObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)Pin_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)Pin_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)0,		/*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	PinType__doc__ /* Documentation string */
};

// End of code for Pin object 
////////////////////////////////////////////

//
static char CreateGraphBuilder__doc__[] =
""
;

static PyObject *
CreateGraphBuilder(PyObject *self, PyObject *args)
{
	HRESULT res;
	GraphBuilderObject *obj;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	obj = newGraphBuilderObject();
	if (obj == NULL)
		return NULL;

    IGraphBuilder *pGraphBuilder=NULL;
	res=CoCreateInstance(CLSID_FilterGraph,NULL,CLSCTX_INPROC_SERVER,
				 IID_IGraphBuilder,(void**)&pGraphBuilder);
	if (!SUCCEEDED(res)) {
		Py_DECREF(obj);
		seterror("CoCreateInstance FilterGraph", res);
		return NULL;
	}
	else
		obj->pGraphBuilder=pGraphBuilder;
	return (PyObject *) obj;
}

static IBaseFilter* CreateDirectShowFilter(LPCTSTR strFilter)
	{
	static const GUID CLSID_ActiveMovieFilterClassManager =
		{0x083863F1,0x70DE,0x11d0,{0xBD,0x40,0x00,0xA0,0xC9,0x11,0xCE,0x86}};

	HRESULT hr;
    ICreateDevEnum *pCreateDevEnum;
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
			  IID_ICreateDevEnum, (void**)&pCreateDevEnum);
    if (hr != S_OK)
		{
		//cout << "Failed to create system device enumerator" << endl;
		return NULL;
		}
	else 
		;//cout << "System device enumerator created" << endl;


    IEnumMoniker *pEnMk;
    hr = pCreateDevEnum->CreateClassEnumerator(CLSID_ActiveMovieFilterClassManager,&pEnMk,0);
    pCreateDevEnum->Release();
    if (hr != S_OK)
		{
		//cout << "Failed to create class enumerator" << endl;
		return NULL;
		}
	else
		;//cout << "Class enumerator created" << endl;

    pEnMk->Reset();
    ULONG cFetched;
    IMoniker *pMk;
	IBaseFilter *pFilter=NULL;
	bool bFound=false;
	//cout << "Enumerating DirectShow filters" << endl;
    while(!bFound && pEnMk->Next(1,&pMk,&cFetched)==S_OK)
		{
		IPropertyBag *pBag;
		hr = pMk->BindToStorage(0,0,IID_IPropertyBag,(void **)&pBag);
		if(SUCCEEDED(hr)) 
			{
			VARIANT var;
			var.vt = VT_BSTR;
			hr = pBag->Read(L"FriendlyName",&var,NULL);
			if(SUCCEEDED(hr)) 
				{
				char achName[256];
				WideCharToMultiByte(CP_ACP, 0,var.bstrVal,-1,achName, 80,NULL, NULL);
				SysFreeString(var.bstrVal);
				if(lstrcmpi(strFilter,achName)==0)
					{
					//cout << "Requested filter "<< strFilter <<  " found!" << endl;
					IBindCtx *pbc=NULL;
					CreateBindCtx(0,&pbc);
					hr = pMk->BindToObject(pbc,NULL,IID_IBaseFilter, (void**)&pFilter);
					pbc->Release();
					bFound=true;
					if(FAILED(hr)) 
						{
						//cout << "BindToObject failed" << endl;
						//ErrorMessage(hr);
						pFilter=NULL;
						}
					}
				}
			pBag->Release();
			}
	    pMk->Release();
		}
    pEnMk->Release();
	return pFilter;
    }

static char CreateFilter__doc__[] =
""
;

static PyObject *
CreateFilter(PyObject *self, PyObject *args)
{
	BaseFilterObject *obj;
	char *psz;
	if (!PyArg_ParseTuple(args, "s", &psz))
		return NULL;
	obj = newBaseFilterObject();
	if (obj == NULL)
		return NULL;
	IBaseFilter *pFilter=CreateDirectShowFilter(psz);
	if (!pFilter) {
		Py_DECREF(obj);
		seterror("CreateFilter", S_OK);
		return NULL;
	}
	else
		obj->pFilter=pFilter;
	return (PyObject *) obj;
	}

static struct PyMethodDef DShow_methods[] = {
	{"CreateGraphBuilder", (PyCFunction)CreateGraphBuilder, METH_VARARGS, CreateGraphBuilder__doc__},
	{"CreateFilter", (PyCFunction)CreateFilter, METH_VARARGS, CreateFilter__doc__},

	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static char dshow_module_documentation[] =
""
;

extern "C" __declspec(dllexport)
void initdshow()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("dshow", DShow_methods,
		dshow_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("dshow.error");
	PyDict_SetItemString(d, "error", ErrorObject);


	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module dshow");
}
