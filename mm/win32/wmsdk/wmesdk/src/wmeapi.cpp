
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>

#include <objbase.h>


/////////////////////

static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}


/////////////////////

#define RELEASE(x) if(x) x->Release();x=NULL;

static void
seterror(const char *funcname, HRESULT hr, const char *moreinfo=NULL)
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
	if(moreinfo)
		PyErr_Format(ErrorObject, "%s failed, %s error = %s", funcname, moreinfo, pszmsg);
	else
		PyErr_Format(ErrorObject, "%s failed, error = %s", funcname, pszmsg);
	LocalFree(pszmsg);
}


static void
seterror(const char *funcname, HRESULT hr,EXCEPINFO *pExcepInfo)
{
	if (hr == DISP_E_EXCEPTION){
		if (pExcepInfo->pfnDeferredFillIn != NULL)
			{
			(*(pExcepInfo->pfnDeferredFillIn))(pExcepInfo) ;
			}
		int iLength = wcslen(pExcepInfo->bstrSource)+1 ;
		char* psz = new char[iLength] ;
		wcstombs(psz, pExcepInfo->bstrSource, iLength) ;
		seterror(funcname, hr, psz);
		delete [] psz;
	} else
		seterror(funcname, hr);
}


///////////////////////////////////////////
///////////////////////////////////////////
// Objects declarations

//(general but defined here for indepentance)
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDispatch *pI;
} AsfRTEncoderObject;

staticforward PyTypeObject AsfRTEncoderType;

static AsfRTEncoderObject *
newAsfRTEncoderObject()
{
	AsfRTEncoderObject *self;

	self = PyObject_NEW(AsfRTEncoderObject, &AsfRTEncoderType);
	if (self == NULL)
		return NULL;
	self->pI=NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//(general but defined here for indepentance)
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IUnknown* pI;
} UnknownObject;

staticforward PyTypeObject UnknownType;

static UnknownObject *
newUnknownObject()
{
	UnknownObject *self;

	self = PyObject_NEW(UnknownObject, &UnknownType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//(general but defined here for indepentance)
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	GUID guid;
} GUIDObject;

staticforward PyTypeObject GUIDType;

static GUIDObject *
newGUIDObject(const GUID *p=NULL)
{
	GUIDObject *self;
	self = PyObject_NEW(GUIDObject, &GUIDType);
	if (self == NULL)
		return NULL;
	self->guid=p?*p:IID_IUnknown;
	/* XXXX Add your own initializers here */
	return self;
}

///////////////////////////////////////////
///////////////////////////////////////////
// Objects definitions



////////////////////////////////////////////
// AsfRTEncoder object 

static char AsfRTEncoder_InvokeMethod__doc__[] =
""
;
static PyObject *
AsfRTEncoder_InvokeMethod(AsfRTEncoderObject *self, PyObject *args)
{
	char *szFunc;
	if (!PyArg_ParseTuple(args, "s",&szFunc))
		return NULL;

	WCHAR wszFunc[256];
	MultiByteToWideChar(CP_ACP,0,szFunc,-1,wszFunc,MAX_PATH);
	
	HRESULT hr;
	LCID lcid = GetUserDefaultLCID();
	DISPID dispid;
	OLECHAR *fname=(OLECHAR *)&wszFunc;
	hr=self->pI->GetIDsOfNames(IID_NULL,&fname,1,lcid,&dispid);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_InvokeMethod::GetIDsOfNames", hr);
		return NULL;
	}	
	DISPPARAMS dp = {NULL,NULL,0,0};
	VARIANT varResult;
	::VariantInit(&varResult);
	EXCEPINFO excepinfo;	
    hr = self->pI->Invoke(dispid,IID_NULL,lcid,DISPATCH_METHOD,&dp,&varResult,&excepinfo,NULL);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_InvokeMethod", hr,&excepinfo);
		return NULL;
	}
	if(varResult.vt==VT_I4)
		return Py_BuildValue("i",varResult.intVal);
	else if(varResult.vt==VT_BOOL)
		return Py_BuildValue("i",-varResult.boolVal);
	Py_INCREF(Py_None);
	return Py_None;
}


static char AsfRTEncoder_IntPropertyPut__doc__[] =
""
;
static PyObject *
AsfRTEncoder_IntPropertyPut(AsfRTEncoderObject *self, PyObject *args)
{
	char *szFunc;
	int val;
	if (!PyArg_ParseTuple(args, "si",&szFunc,&val))
		return NULL;

	WCHAR wszFunc[256];
	MultiByteToWideChar(CP_ACP,0,szFunc,-1,wszFunc,MAX_PATH);
	
	VARIANT varg;VariantInit(&varg);varg.vt=VT_I4;varg.lVal=val;
	
	HRESULT hr;
	LCID lcid = GetUserDefaultLCID();
	DISPID dispid;
	OLECHAR *fname=(OLECHAR *)&wszFunc;
	hr=self->pI->GetIDsOfNames(IID_NULL,&fname,1,lcid,&dispid);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_LoadASD::GetIDsOfNames", hr);
		return NULL;
	}	
	DISPPARAMS dp = {&varg,NULL,1,0};
	EXCEPINFO excepinfo;	
    hr = self->pI->Invoke(dispid,IID_NULL,lcid,DISPATCH_METHOD,&dp,NULL,&excepinfo,NULL);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_IntPropertyPut", hr,&excepinfo);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



static char AsfRTEncoder_LoadASD__doc__[] =
""
;
static PyObject *
AsfRTEncoder_LoadASD(AsfRTEncoderObject *self, PyObject *args)
{
	char *szFileName;
	if (!PyArg_ParseTuple(args, "s",&szFileName))
		return NULL;

	WCHAR wszFileName[MAX_PATH];
	MultiByteToWideChar(CP_ACP,0,szFileName,-1,wszFileName,MAX_PATH);
	BSTR bstr=::SysAllocString(wszFileName);
	VARIANT varg;VariantInit(&varg);varg.vt=VT_BSTR;varg.bstrVal=bstr;
	
	HRESULT hr;
	LCID lcid = GetUserDefaultLCID();
	DISPID dispid;
	OLECHAR *fname=L"LoadASD";
	hr=self->pI->GetIDsOfNames(IID_NULL,&fname,1,lcid,&dispid);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_LoadASD::GetIDsOfNames", hr);
		return NULL;
	}	
	DISPPARAMS dp = {&varg,NULL,1,0};
	VARIANT varResult;
	::VariantInit(&varResult);	
    hr = self->pI->Invoke(dispid,IID_NULL,lcid,DISPATCH_METHOD,&dp,&varResult,NULL,NULL);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_LoadASD::Invoke", hr);
		return NULL;
	}	
	::SysFreeString(bstr);
	Py_INCREF(Py_None);
	return Py_None;
}

static char AsfRTEncoder_Start__doc__[] =
""
;
static PyObject *
AsfRTEncoder_Start(AsfRTEncoderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	VARIANT varg;VariantInit(&varg);varg.vt=VT_NULL;
	
	HRESULT hr;
	LCID lcid = GetUserDefaultLCID();
	DISPID dispid;
	OLECHAR *fname=L"Start";
	hr=self->pI->GetIDsOfNames(IID_NULL,&fname,1,lcid,&dispid);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_Start::GetIDsOfNames", hr);
		return NULL;
	}		
	DISPPARAMS dp = {NULL,NULL,0,0};
	VARIANT varResult;
	EXCEPINFO excepinfo;
	::VariantInit(&varResult);	
	hr = self->pI->Invoke(dispid,IID_NULL,lcid,DISPATCH_METHOD,&dp,&varResult,&excepinfo,NULL);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_Start::Invoke", hr, &excepinfo);
		return NULL;
	}	
	Py_INCREF(Py_None);
	return Py_None;
}

static char AsfRTEncoder_Stop__doc__[] =
""
;
static PyObject *
AsfRTEncoder_Stop(AsfRTEncoderObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
	//LCID lcid = GetUserDefaultLCID();
	LCID lcid = GetSystemDefaultLCID();
	DISPID dispid;
	OLECHAR *fname=L"Stop";
	hr=self->pI->GetIDsOfNames(IID_NULL,&fname,1,lcid,&dispid);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_Stop::GetIDsOfNames", hr);
		return NULL;
	}	
	DISPPARAMS dp = {NULL,NULL,0,0};
    hr = self->pI->Invoke(dispid,IID_NULL,lcid,DISPATCH_METHOD,&dp,NULL,NULL,NULL);
	if (FAILED(hr)){
		seterror("AsfRTEncoder_Stop::Invoke", hr);
		return NULL;
	}	
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef AsfRTEncoder_methods[] = {
	{"InvokeMethod", (PyCFunction)AsfRTEncoder_InvokeMethod, METH_VARARGS, AsfRTEncoder_InvokeMethod__doc__},
	{"IntPropertyPut", (PyCFunction)AsfRTEncoder_IntPropertyPut, METH_VARARGS, AsfRTEncoder_IntPropertyPut__doc__},
	{"IntPropertyGet", (PyCFunction)AsfRTEncoder_InvokeMethod, METH_VARARGS, AsfRTEncoder_InvokeMethod__doc__},
	{"LoadASD", (PyCFunction)AsfRTEncoder_LoadASD, METH_VARARGS, AsfRTEncoder_LoadASD__doc__},
	{"Start", (PyCFunction)AsfRTEncoder_Start, METH_VARARGS, AsfRTEncoder_Start__doc__},
	{"Stop", (PyCFunction)AsfRTEncoder_Stop, METH_VARARGS, AsfRTEncoder_Stop__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
AsfRTEncoder_dealloc(AsfRTEncoderObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
AsfRTEncoder_getattr(AsfRTEncoderObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(AsfRTEncoder_methods, (PyObject *)self, name);
}

static char AsfRTEncoderType__doc__[] =
""
;

static PyTypeObject AsfRTEncoderType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"AsfRTEncoder",			/*tp_name*/
	sizeof(AsfRTEncoderObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)AsfRTEncoder_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)AsfRTEncoder_getattr,	/*tp_getattr*/
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
	AsfRTEncoderType__doc__ /* Documentation string */
};

// End of code for AsfRTEncoder object 
////////////////////////////////////////////

////////////////////////////////////////////
// Unknown object (general but defined here for indepentance) 

static struct PyMethodDef Unknown_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
Unknown_dealloc(UnknownObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
Unknown_getattr(UnknownObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(Unknown_methods, (PyObject *)self, name);
}

static char UnknownType__doc__[] =
""
;

static PyTypeObject UnknownType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"Unknown",			/*tp_name*/
	sizeof(UnknownObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)Unknown_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)Unknown_getattr,	/*tp_getattr*/
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
	UnknownType__doc__ /* Documentation string */
};

// End of code for Unknown object 
////////////////////////////////////////////


////////////////////////////////////////////
// GUID object (general but defined here for indepentance) 
			
static struct PyMethodDef GUID_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
GUID_dealloc(GUIDObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
GUID_getattr(GUIDObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(GUID_methods, (PyObject *)self, name);
}

static int
GUID_compare(GUIDObject *l, GUIDObject *r)
{
	int mr = memcmp((const void*)&l->guid,(const void*)&r->guid,sizeof(GUID));
	return (mr<0) ? -1 : ((mr>0) ? 1 : 0);
}

static char GUIDType__doc__[] =
""
;
static PyTypeObject GUIDType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"GUID",			/*tp_name*/
	sizeof(GUIDObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)GUID_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)GUID_getattr,	/*tp_getattr*/
	(setattrfunc)0,	/*tp_setattr*/
	(cmpfunc)GUID_compare, /*tp_compare*/
	(reprfunc)0,		/*tp_repr*/
	0,			/*tp_as_number*/
	0,		/*tp_as_sequence*/
	0,		/*tp_as_mapping*/
	(hashfunc)0,		/*tp_hash*/
	(ternaryfunc)0,		/*tp_call*/
	(reprfunc)0,		/*tp_str*/

	/* Space for future expansion */
	0L,0L,0L,0L,
	GUIDType__doc__ /* Documentation string */
};

// End of code for GUID object 
////////////////////////////////////////////


///////////////////////////////////////////
///////////////////////////////////////////
// MODULE
//

static char CreateAsfRTEncoder__doc__[] =
""
;
static PyObject *
CreateAsfRTEncoder(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	AsfRTEncoderObject *obj = newAsfRTEncoderObject();
	if (obj == NULL)
		return NULL;

	HRESULT hr;
	static const GUID CLSID_IAsfRTEncoder = 
		{ 0x7DEBA670, 0x68AB, 0x11D0, { 0x98, 0xEB, 0x00, 0xaa, 0x00, 0xbb, 0xb5, 0x2c } };	
	Py_BEGIN_ALLOW_THREADS
	hr = CoCreateInstance(CLSID_IAsfRTEncoder,
                        NULL, 
                        CLSCTX_LOCAL_SERVER, 
                        IID_IDispatch, 
                        (void **)&obj->pI);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreateAsfRTEncoder", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

// std com stuff for independance
static char CoInitialize__doc__[] =
""
;
static PyObject*
CoInitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr=CoInitialize(NULL);
	int res=(hr==S_OK || hr==S_FALSE)?1:0;
	return Py_BuildValue("i",res);
	}

// std com stuff for independance
static char CoUninitialize__doc__[] =
""
;
static PyObject*
CoUninitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	CoUninitialize();
	Py_INCREF(Py_None);
	return Py_None;
	}

// std com stuff for independance
static char OleInitialize__doc__[] =
""
;
static PyObject*
OleInitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr=OleInitialize(NULL);
	int res=(hr==S_OK || hr==S_FALSE)?1:0;
	return Py_BuildValue("i",res);
	}
static char OleUninitialize__doc__[] =
""
;
static PyObject*
OleUninitialize(PyObject *self, PyObject *args) 
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	OleUninitialize();
	Py_INCREF(Py_None);
	return Py_None;
	}

static struct PyMethodDef wmeapi_methods[] = {
	{"CreateAsfRTEncoder", (PyCFunction)CreateAsfRTEncoder, METH_VARARGS, CreateAsfRTEncoder__doc__},
	{"OleInitialize", (PyCFunction)OleInitialize, METH_VARARGS, OleInitialize__doc__},
	{"OleUninitialize", (PyCFunction)OleUninitialize, METH_VARARGS, OleUninitialize__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


#define FATAL_ERROR_IF(exp) if(exp){Py_FatalError("can't initialize module wmeapi");return;}	

static char wmeapi_module_documentation[] =
"Windows Media Encoder API"
;

extern "C" __declspec(dllexport)
void initwmeapi()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("wmeapi", wmeapi_methods,
		wmeapi_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("wmeapi.error");
	PyDict_SetItemString(d, "error", ErrorObject);
	
	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module wmeapi");
}



