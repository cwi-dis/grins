
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#include <windows.h>
#include <wtypes.h>
#include <assert.h>

#include <mmsystem.h>
#include <ddraw.h>

#pragma comment (lib,"winmm.lib")
#pragma comment (lib,"ddraw.lib")

static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}

/////////////////////

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


///////////////////////////////////////////
///////////////////////////////////////////
// Objects declarations

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectDraw* pI;
} DirectDrawObject;

staticforward PyTypeObject DirectDrawType;

static DirectDrawObject *
newDirectDrawObject()
{
	DirectDrawObject *self;

	self = PyObject_NEW(DirectDrawObject, &DirectDrawType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectDrawSurface* pI;
} DirectDrawSurfaceObject;

staticforward PyTypeObject DirectDrawSurfaceType;

static DirectDrawSurfaceObject *
newDirectDrawSurfaceObject()
{
	DirectDrawSurfaceObject *self;

	self = PyObject_NEW(DirectDrawSurfaceObject, &DirectDrawSurfaceType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectDrawClipper* pI;
} DirectDrawClipperObject;

staticforward PyTypeObject DirectDrawClipperType;

static DirectDrawClipperObject *
newDirectDrawClipperObject()
{
	DirectDrawClipperObject *self;

	self = PyObject_NEW(DirectDrawClipperObject, &DirectDrawClipperType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	IDirectDrawPalette* pI;
} DirectDrawPaletteObject;

staticforward PyTypeObject DirectDrawPaletteType;

static DirectDrawPaletteObject *
newDirectDrawPaletteObject()
{
	DirectDrawPaletteObject *self;

	self = PyObject_NEW(DirectDrawPaletteObject, &DirectDrawPaletteType);
	if (self == NULL)
		return NULL;
	self->pI = NULL;
	/* XXXX Add your own initializers here */
	return self;
}


//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	DDSURFACEDESC sd;
} DDSURFACEDESCObject;

staticforward PyTypeObject DDSURFACEDESCType;

static DDSURFACEDESCObject *
newDDSURFACEDESCObject()
{
	DDSURFACEDESCObject *self;

	self = PyObject_NEW(DDSURFACEDESCObject, &DDSURFACEDESCType);
	if (self == NULL)
		return NULL;
	memset(&self->sd, 0, sizeof(self->sd));
	self->sd.dwSize = sizeof(self->sd);
	/* XXXX Add your own initializers here */
	return self;
}

///////////////////////////////////////////
///////////////////////////////////////////
// Objects definitions



////////////////////////////////////////////
// DirectDraw object 

static char DirectDraw_SetCooperativeLevel__doc__[] =
""
;
static PyObject *
DirectDraw_SetCooperativeLevel(DirectDrawObject *self, PyObject *args)
{
	HWND hWnd;
	DWORD dwFlags = DDSCL_NORMAL;
	if (!PyArg_ParseTuple(args, "i|i",&hWnd,&dwFlags))
		return NULL;	
	HRESULT hr;
	hr = self->pI->SetCooperativeLevel(hWnd, dwFlags);
	if (FAILED(hr)){
		seterror("DirectDraw_SetCooperativeLevel", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectDraw_CreateSurface__doc__[] =
""
;
static PyObject *
DirectDraw_CreateSurface(DirectDrawObject *self, PyObject *args)
{
	int cx=0,cy=0;
	if (!PyArg_ParseTuple(args, "|ii",&cx,&cy))
		return NULL;	
	HRESULT hr;
	// avoid transfering this struct for now
	DDSURFACEDESC ddsd; 
	memset(&ddsd, 0, sizeof(ddsd));
	ddsd.dwSize = sizeof(ddsd);
	if(cx>0 && cy>0)
		{
		ddsd.dwFlags = DDSD_WIDTH | DDSD_HEIGHT | DDSD_CAPS;
		ddsd.dwWidth = cx;
		ddsd.dwHeight = cy;
		ddsd.ddsCaps.dwCaps = DDSCAPS_OFFSCREENPLAIN | DDSCAPS_3DDEVICE;
		}
	else
		{
		ddsd.dwFlags = DDSD_CAPS;
		ddsd.ddsCaps.dwCaps = DDSCAPS_PRIMARYSURFACE;
		}	
	DirectDrawSurfaceObject *obj = newDirectDrawSurfaceObject();	
	hr = self->pI->CreateSurface(&ddsd, &obj->pI, NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDraw_CreateSurface", hr);
		return NULL;
	}
	return (PyObject*) obj;
}

static char DirectDraw_CreateClipper__doc__[] =
""
;
static PyObject *
DirectDraw_CreateClipper(DirectDrawObject *self, PyObject *args)
{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i",&hwnd))
		return NULL;	
	HRESULT hr;
	DirectDrawClipperObject *obj = newDirectDrawClipperObject();	
	hr = self->pI->CreateClipper(0, &obj->pI, NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDraw_CreateClipper", hr);
		return NULL;
	}
	hr = obj->pI->SetHWnd(0, hwnd);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDraw_CreateClipper:SetHWnd", hr);
		return NULL;
	}
	return (PyObject*) obj;
}

static char DirectDraw_CreatePalette__doc__[] =
""
;
static PyObject *
DirectDraw_CreatePalette(DirectDrawObject *self, PyObject *args)
{
	DWORD dwFlags = DDPCAPS_8BIT | DDPCAPS_INITIALIZE;
	if (!PyArg_ParseTuple(args, "|i",&dwFlags))
		return NULL;	
	HRESULT hr;
	PALETTEENTRY colorTable[256]; // XXX: arg or create
	DirectDrawPaletteObject *obj = newDirectDrawPaletteObject();	
	hr = self->pI->CreatePalette(dwFlags, (PALETTEENTRY*)&colorTable, &obj->pI, NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDraw_CreatePalette", hr);
		return NULL;
	}
	return (PyObject*) obj;
}

static struct PyMethodDef DirectDraw_methods[] = {
	{"SetCooperativeLevel", (PyCFunction)DirectDraw_SetCooperativeLevel, METH_VARARGS, DirectDraw_SetCooperativeLevel__doc__},
	{"CreateSurface", (PyCFunction)DirectDraw_CreateSurface, METH_VARARGS, DirectDraw_CreateSurface__doc__},
	{"CreateClipper", (PyCFunction)DirectDraw_CreateClipper, METH_VARARGS, DirectDraw_CreateClipper__doc__},
	{"CreatePalette", (PyCFunction)DirectDraw_CreatePalette, METH_VARARGS, DirectDraw_CreatePalette__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectDraw_dealloc(DirectDrawObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectDraw_getattr(DirectDrawObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectDraw_methods, (PyObject *)self, name);
}

static char DirectDrawType__doc__[] =
""
;

static PyTypeObject DirectDrawType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectDraw",			/*tp_name*/
	sizeof(DirectDrawObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectDraw_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectDraw_getattr,	/*tp_getattr*/
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
	DirectDrawType__doc__ /* Documentation string */
};

// End of code for DirectDraw object 
////////////////////////////////////////////


////////////////////////////////////////////
// DirectDrawSurface object 

static char DirectDrawSurface_Empty__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Empty(DirectDrawSurfaceObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr = S_OK;
	//hr = self->pI->Empty();
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Empty", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



static struct PyMethodDef DirectDrawSurface_methods[] = {
	{"Empty", (PyCFunction)DirectDrawSurface_Empty, METH_VARARGS, DirectDrawSurface_Empty__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectDrawSurface_dealloc(DirectDrawSurfaceObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectDrawSurface_getattr(DirectDrawSurfaceObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectDrawSurface_methods, (PyObject *)self, name);
}

static char DirectDrawSurfaceType__doc__[] =
""
;

static PyTypeObject DirectDrawSurfaceType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectDrawSurface",			/*tp_name*/
	sizeof(DirectDrawSurfaceObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectDrawSurface_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectDrawSurface_getattr,	/*tp_getattr*/
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
	DirectDrawSurfaceType__doc__ /* Documentation string */
};

// End of code for DirectDrawSurface object 
////////////////////////////////////////////

////////////////////////////////////////////
// DirectDrawClipper object 

static struct PyMethodDef DirectDrawClipper_methods[] = {
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectDrawClipper_dealloc(DirectDrawClipperObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectDrawClipper_getattr(DirectDrawClipperObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectDrawClipper_methods, (PyObject *)self, name);
}

static char DirectDrawClipperType__doc__[] =
""
;

static PyTypeObject DirectDrawClipperType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectDrawClipper",			/*tp_name*/
	sizeof(DirectDrawClipperObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectDrawClipper_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectDrawClipper_getattr,	/*tp_getattr*/
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
	DirectDrawClipperType__doc__ /* Documentation string */
};

// End of code for DirectDrawClipper object 
////////////////////////////////////////////

////////////////////////////////////////////
// DirectDrawPalette object 

static char DirectDrawPalette_Empty__doc__[] =
""
;
static PyObject *
DirectDrawPalette_Empty(DirectDrawPaletteObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr = S_OK;
	//hr = self->pI->Empty();
	if (FAILED(hr)){
		seterror("DirectDrawPalette_Empty", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



static struct PyMethodDef DirectDrawPalette_methods[] = {
	{"Empty", (PyCFunction)DirectDrawPalette_Empty, METH_VARARGS, DirectDrawPalette_Empty__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectDrawPalette_dealloc(DirectDrawPaletteObject *self)
{
	/* XXXX Add your own cleanup code here */
	RELEASE(self->pI);
	PyMem_DEL(self);
}

static PyObject *
DirectDrawPalette_getattr(DirectDrawPaletteObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DirectDrawPalette_methods, (PyObject *)self, name);
}

static char DirectDrawPaletteType__doc__[] =
""
;

static PyTypeObject DirectDrawPaletteType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DirectDrawPalette",			/*tp_name*/
	sizeof(DirectDrawPaletteObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DirectDrawPalette_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DirectDrawPalette_getattr,	/*tp_getattr*/
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
	DirectDrawPaletteType__doc__ /* Documentation string */
};

// End of code for DirectDrawPalette object 
////////////////////////////////////////////

////////////////////////////////////////////
// DDSURFACEDESC object 

static char DDSURFACEDESC_Empty__doc__[] =
""
;
static PyObject *
DDSURFACEDESC_Empty(DDSURFACEDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr = S_OK;
	//hr = self->pI->Empty();
	if (FAILED(hr)){
		seterror("DDSURFACEDESC_Empty", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



static struct PyMethodDef DDSURFACEDESC_methods[] = {
	{"Empty", (PyCFunction)DDSURFACEDESC_Empty, METH_VARARGS, DDSURFACEDESC_Empty__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DDSURFACEDESC_dealloc(DDSURFACEDESCObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
DDSURFACEDESC_getattr(DDSURFACEDESCObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DDSURFACEDESC_methods, (PyObject *)self, name);
}

static char DDSURFACEDESCType__doc__[] =
""
;

static PyTypeObject DDSURFACEDESCType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DDSURFACEDESC",			/*tp_name*/
	sizeof(DDSURFACEDESCObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DDSURFACEDESC_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DDSURFACEDESC_getattr,	/*tp_getattr*/
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
	DDSURFACEDESCType__doc__ /* Documentation string */
};

// End of code for DDSURFACEDESC object 
////////////////////////////////////////////



///////////////////////////////////////////
///////////////////////////////////////////
// MODULE
//

//
static char CreateDirectDraw__doc__[] =
""
;
static PyObject *
CreateDirectDraw(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	
	DirectDrawObject *obj = newDirectDrawObject();
	if (obj == NULL)
		return NULL;
	
	HRESULT hr;
	hr = DirectDrawCreate(NULL, &obj->pI, NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreateDirectDraw", hr);
		return NULL;
	}
	return (PyObject*)obj;
}

//
static char CreateDDSURFACEDESC__doc__[] =
"DDSURFACEDESC structure"
;
static PyObject *
CreateDDSURFACEDESC(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	DDSURFACEDESCObject *obj = newDDSURFACEDESCObject();
	if (obj == NULL)
		return NULL;
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

static struct PyMethodDef ddraw_methods[] = {
	{"CreateDirectDraw", (PyCFunction)CreateDirectDraw, METH_VARARGS, CreateDirectDraw__doc__},
	{"CreateDDSURFACEDESC", (PyCFunction)CreateDDSURFACEDESC, METH_VARARGS, CreateDDSURFACEDESC__doc__},
	{"CoInitialize", (PyCFunction)CoInitialize, METH_VARARGS, CoInitialize__doc__},
	{"CoUninitialize", (PyCFunction)CoUninitialize, METH_VARARGS, CoUninitialize__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static char ddraw_module_documentation[] =
"DirectDraw module"
;

extern "C" __declspec(dllexport)
void initddraw()
{
	PyObject *m, *d;
	bool bPyErrOccurred = false;
	
	// Create the module and add the functions
	m = Py_InitModule4("ddraw", ddraw_methods,
		ddraw_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("ddraw.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module ddraw");
}
