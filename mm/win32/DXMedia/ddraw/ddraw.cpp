
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

static char DirectDrawSurface_GetSurfaceDesc__doc__[] =
""
;
static PyObject *
DirectDrawSurface_GetSurfaceDesc(DirectDrawSurfaceObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	DDSURFACEDESCObject *obj = newDDSURFACEDESCObject();	
	hr = self->pI->GetSurfaceDesc(&obj->sd);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDrawSurface_GetSurfaceDesc", hr);
		return NULL;
	}
	return (PyObject *)obj;
}



static struct PyMethodDef DirectDrawSurface_methods[] = {
	{"GetSurfaceDesc", (PyCFunction)DirectDrawSurface_GetSurfaceDesc, METH_VARARGS, DirectDrawSurface_GetSurfaceDesc__doc__},
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

static char DDSURFACEDESC_Clear__doc__[] =
"Clear DDSURFACEDESC for reuse"
;
static PyObject *
DDSURFACEDESC_Clear(DDSURFACEDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	memset(&self->sd, 0, sizeof(self->sd));
	self->sd.dwSize = sizeof(self->sd);
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDSURFACEDESC_SetFlags__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_SetFlags(DDSURFACEDESCObject *self, PyObject *args)
{
	DWORD dwFlags;
	if (!PyArg_ParseTuple(args, "i",&dwFlags))
		return NULL;
	self->sd.dwFlags = dwFlags;
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDSURFACEDESC_SetCaps__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_SetCaps(DDSURFACEDESCObject *self, PyObject *args)
{
	DWORD dwCaps;
	if (!PyArg_ParseTuple(args, "i",&dwCaps))
		return NULL;
	self->sd.ddsCaps.dwCaps = dwCaps;
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDSURFACEDESC_SetSize__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_SetSize(DDSURFACEDESCObject *self, PyObject *args)
{
	DWORD cx, cy;
	if (!PyArg_ParseTuple(args, "ii",&cx,&cy))
		return NULL;
	self->sd.dwWidth = cx;
	self->sd.dwHeight = cy;
	Py_INCREF(Py_None);
	return Py_None;
}

static struct PyMethodDef DDSURFACEDESC_methods[] = {
	{"Clear", (PyCFunction)DDSURFACEDESC_Clear, METH_VARARGS, DDSURFACEDESC_Clear__doc__},
	{"SetFlags", (PyCFunction)DDSURFACEDESC_SetFlags, METH_VARARGS, DDSURFACEDESC_SetFlags__doc__},
	{"SetCaps", (PyCFunction)DDSURFACEDESC_SetCaps, METH_VARARGS, DDSURFACEDESC_SetCaps__doc__},
	{"SetSize", (PyCFunction)DDSURFACEDESC_SetSize, METH_VARARGS, DDSURFACEDESC_SetSize__doc__},
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


struct constentry {char* s;int n;};

static struct constentry _ddscl[] ={
	{"DDSCL_FULLSCREEN",DDSCL_FULLSCREEN},
	{"DDSCL_ALLOWREBOOT",DDSCL_ALLOWREBOOT},
	{"DDSCL_NOWINDOWCHANGES",DDSCL_NOWINDOWCHANGES},
	{"DDSCL_NORMAL",DDSCL_NORMAL},
	{"DDSCL_EXCLUSIVE",DDSCL_EXCLUSIVE},
	{"DDSCL_ALLOWMODEX",DDSCL_ALLOWMODEX},
	{"DDSCL_SETFOCUSWINDOW",DDSCL_SETFOCUSWINDOW},
	{"DDSCL_SETDEVICEWINDOW",DDSCL_SETDEVICEWINDOW},
	{"DDSCL_CREATEDEVICEWINDOW",DDSCL_CREATEDEVICEWINDOW},
	{NULL,0}
	};

static struct constentry _ddsd[] ={
	{"DDSD_CAPS",DDSD_CAPS},
	{"DDSD_HEIGHT",DDSD_HEIGHT},
	{"DDSD_WIDTH",DDSD_WIDTH},
	{"DDSD_PITCH",DDSD_PITCH},
	{"DDSD_BACKBUFFERCOUNT",DDSD_BACKBUFFERCOUNT},
	{"DDSD_ZBUFFERBITDEPTH",DDSD_ZBUFFERBITDEPTH},
	{"DDSD_ALPHABITDEPTH",DDSD_ALPHABITDEPTH},
	{"DDSD_LPSURFACE",DDSD_LPSURFACE},
	{"DDSD_PIXELFORMAT",DDSD_PIXELFORMAT},
	{"DDSD_CKDESTOVERLAY",DDSD_CKDESTOVERLAY},
	{"DDSD_CKDESTBLT",DDSD_CKDESTBLT},
	{"DDSD_CKSRCOVERLAY",DDSD_CKSRCOVERLAY},
	{"DDSD_CKSRCBLT",DDSD_CKSRCBLT},
	{"DDSD_MIPMAPCOUNT",DDSD_MIPMAPCOUNT},
	{"DDSD_REFRESHRATE",DDSD_REFRESHRATE},
	{"DDSD_LINEARSIZE",DDSD_LINEARSIZE},
	{"DDSD_ALL",DDSD_ALL},
	{NULL,0}
	};

static struct constentry _ddscaps[] ={
	{"DDSCAPS_RESERVED1",DDSCAPS_RESERVED1},
	{"DDSCAPS_ALPHA",DDSCAPS_ALPHA},
	{"DDSCAPS_BACKBUFFER",DDSCAPS_BACKBUFFER},
	{"DDSCAPS_COMPLEX",DDSCAPS_COMPLEX},
	{"DDSCAPS_FLIP",DDSCAPS_FLIP},
	{"DDSCAPS_FRONTBUFFER",DDSCAPS_FRONTBUFFER},
	{"DDSCAPS_OFFSCREENPLAIN",DDSCAPS_OFFSCREENPLAIN},
	{"DDSCAPS_OVERLAY",DDSCAPS_OVERLAY},
	{"DDSCAPS_PALETTE",DDSCAPS_PALETTE},
	{"DDSCAPS_PRIMARYSURFACE",DDSCAPS_PRIMARYSURFACE},
	{"DDSCAPS_PRIMARYSURFACELEFT",DDSCAPS_PRIMARYSURFACELEFT},
	{"DDSCAPS_SYSTEMMEMORY",DDSCAPS_SYSTEMMEMORY},
	{"DDSCAPS_TEXTURE",DDSCAPS_TEXTURE},
	{"DDSCAPS_3DDEVICE",DDSCAPS_3DDEVICE},
	{"DDSCAPS_VIDEOMEMORY",DDSCAPS_VIDEOMEMORY},
	{"DDSCAPS_VISIBLE",DDSCAPS_VISIBLE},
	{"DDSCAPS_WRITEONLY",DDSCAPS_WRITEONLY},
	{"DDSCAPS_ZBUFFER",DDSCAPS_ZBUFFER},
	{"DDSCAPS_OWNDC",DDSCAPS_OWNDC},
	{"DDSCAPS_LIVEVIDEO",DDSCAPS_LIVEVIDEO},
	{"DDSCAPS_HWCODEC",DDSCAPS_HWCODEC},
	{"DDSCAPS_MODEX",DDSCAPS_MODEX},
	{"DDSCAPS_MIPMAP",DDSCAPS_MIPMAP},
	{"DDSCAPS_RESERVED2",DDSCAPS_RESERVED2},
	{"DDSCAPS_ALLOCONLOAD",DDSCAPS_ALLOCONLOAD},
	{"DDSCAPS_VIDEOPORT",DDSCAPS_VIDEOPORT},
	{"DDSCAPS_LOCALVIDMEM",DDSCAPS_LOCALVIDMEM},
	{"DDSCAPS_NONLOCALVIDMEM",DDSCAPS_NONLOCALVIDMEM},
	{"DDSCAPS_STANDARDVGAMODE",DDSCAPS_STANDARDVGAMODE},
	{"DDSCAPS_OPTIMIZED",DDSCAPS_OPTIMIZED},
	{NULL,0}
	};

static struct constentry _ddblt[] ={
	{"DDBLT_ALPHADEST",DDBLT_ALPHADEST},
	{"DDBLT_ALPHADESTCONSTOVERRIDE",DDBLT_ALPHADESTCONSTOVERRIDE},
	{"DDBLT_ALPHADESTNEG",DDBLT_ALPHADESTNEG},
	{"DDBLT_ALPHADESTSURFACEOVERRIDE",DDBLT_ALPHADESTSURFACEOVERRIDE},
	{"DDBLT_ALPHAEDGEBLEND",DDBLT_ALPHAEDGEBLEND},
	{"DDBLT_ALPHASRC",DDBLT_ALPHASRC},
	{"DDBLT_ALPHASRCCONSTOVERRIDE",DDBLT_ALPHASRCCONSTOVERRIDE},
	{"DDBLT_ALPHASRCNEG",DDBLT_ALPHASRCNEG},
	{"DDBLT_ALPHASRCSURFACEOVERRIDE",DDBLT_ALPHASRCSURFACEOVERRIDE},
	{"DDBLT_ASYNC",DDBLT_ASYNC},
	{"DDBLT_COLORFILL",DDBLT_COLORFILL},
	{"DDBLT_DDFX",DDBLT_DDFX},
	{"DDBLT_DDROPS",DDBLT_DDROPS},
	{"DDBLT_KEYDEST",DDBLT_KEYDEST},
	{"DDBLT_KEYDESTOVERRIDE",DDBLT_KEYDESTOVERRIDE},
	{"DDBLT_KEYSRC",DDBLT_KEYSRC},
	{"DDBLT_KEYSRCOVERRIDE",DDBLT_KEYSRCOVERRIDE},
	{"DDBLT_ROP",DDBLT_ROP},
	{"DDBLT_ROTATIONANGLE",DDBLT_ROTATIONANGLE},
	{"DDBLT_ZBUFFER",DDBLT_ZBUFFER},
	{"DDBLT_ZBUFFERDESTCONSTOVERRIDE",DDBLT_ZBUFFERDESTCONSTOVERRIDE},
	{"DDBLT_ZBUFFERDESTOVERRIDE",DDBLT_ZBUFFERDESTOVERRIDE},
	{"DDBLT_ZBUFFERSRCCONSTOVERRIDE",DDBLT_ZBUFFERSRCCONSTOVERRIDE},
	{"DDBLT_ZBUFFERSRCOVERRIDE",DDBLT_ZBUFFERSRCOVERRIDE},
	{"DDBLT_WAIT",DDBLT_WAIT},
	{"DDBLT_DEPTHFILL",DDBLT_DEPTHFILL},
	{NULL,0}
	};

static struct constentry _ddbltfast[] ={
	{"DDBLTFAST_NOCOLORKEY",DDBLTFAST_NOCOLORKEY},
	{"DDBLTFAST_SRCCOLORKEY",DDBLTFAST_SRCCOLORKEY},
	{"DDBLTFAST_DESTCOLORKEY",DDBLTFAST_DESTCOLORKEY},
	{"DDBLTFAST_WAIT",DDBLTFAST_WAIT},
	{NULL,0}
	};

static struct constentry _ddflip[] ={
	{"DDFLIP_WAIT",DDFLIP_WAIT},
	{"DDFLIP_EVEN",DDFLIP_EVEN},
	{"DDFLIP_ODD",DDFLIP_ODD},
	{NULL,0}
	};

static struct constentry _ddlock[] ={
	{"DDLOCK_SURFACEMEMORYPTR",DDLOCK_SURFACEMEMORYPTR},
	{"DDLOCK_WAIT",DDLOCK_WAIT},
	{"DDLOCK_EVENT",DDLOCK_EVENT},
	{"DDLOCK_READONLY",DDLOCK_READONLY},
	{"DDLOCK_WRITEONLY",DDLOCK_WRITEONLY},
	{"DDLOCK_NOSYSLOCK",DDLOCK_NOSYSLOCK},
	{NULL,0}
	};

static struct constentry _ddgbs[] ={
	{"DDGBS_CANBLT",DDGBS_CANBLT},
	{"DDGBS_ISBLTDONE",DDGBS_ISBLTDONE},
	{NULL,0}
	};


// add symbolic constants of enum
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
#define FATAL_ERROR_IF(exp) if(exp){Py_FatalError("can't initialize module ddraw");return;}	


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

	// add symbolic constants of enum
	FATAL_ERROR_IF(SetItemEnum(d,_ddscl)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddsd)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddscaps)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddblt)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddbltfast)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddflip)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddlock)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddgbs)<0)

	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module ddraw");
}
