
/***********************************************************
Copyright 1991-2000 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"

#define INITGUID
#include <objbase.h>

#include <windows.h>
#include <wtypes.h>
#include <assert.h>
#include <math.h>

#include <mmsystem.h>
#include <ddraw.h>

#pragma comment (lib,"winmm.lib")
#pragma comment (lib,"ddraw.lib")

#ifdef USE_DDRAWEX
// += extensions
#include <ddrawex.h>
#endif


static PyObject *ErrorObject;

void seterror(const char *msg){PyErr_SetString(ErrorObject, msg);}

/////////////////////

#define RELEASE(x) if(x) x->Release();x=NULL;

static void
seterror(const char *funcname, HRESULT hr)
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
	bool releaseI;
	RECT rc;
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
	self->releaseI = true;
	memset(&self->rc,0,sizeof(RECT));
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
	memset(&self->sd, 0, sizeof(DDSURFACEDESC));
	self->sd.dwSize = sizeof(DDSURFACEDESC);
	/* XXXX Add your own initializers here */
	return self;
}

//
typedef struct {
	PyObject_HEAD
	/* XXXX Add your own stuff here */
	DDBLTFX bltfx;
} DDBLTFXObject;

staticforward PyTypeObject DDBLTFXType;

static DDBLTFXObject *
newDDBLTFXObject()
{
	DDBLTFXObject *self;

	self = PyObject_NEW(DDBLTFXObject, &DDBLTFXType);
	if (self == NULL)
		return NULL;
	memset(&self->bltfx, 0, sizeof(self->bltfx));
	self->bltfx.dwSize = sizeof(self->bltfx);
	/* XXXX Add your own initializers here */
	return self;
}

///////////////////////////////////////////
// helpers

static HRESULT GetSurfaceRect(IDirectDrawSurface* pI, RECT *prc)
	{
	if(!pI) return false;
	DDSURFACEDESC desc;
	ZeroMemory( &desc, sizeof(desc) );
	desc.dwSize=sizeof(desc);
	desc.dwFlags=DDSD_WIDTH | DDSD_HEIGHT;
	HRESULT hr = pI->GetSurfaceDesc(&desc);
	if(FAILED(hr)) return hr;
	prc->left = prc->top = 0;
	prc->right = desc.dwWidth;
	prc->bottom = desc.dwHeight;
	return hr;
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

static char DirectDraw_SetDisplayMode__doc__[] =
""
;
static PyObject *
DirectDraw_SetDisplayMode(DirectDrawObject *self, PyObject *args)
{
	DWORD dwWidth, dwHeight, dwBPP;
  	if (!PyArg_ParseTuple(args, "iii",&dwWidth, &dwHeight, &dwBPP))
		return NULL;	
	HRESULT hr;
	hr = self->pI->SetDisplayMode(dwWidth, dwHeight, dwBPP);
	if (FAILED(hr)){
		seterror("DirectDraw_SetDisplayMode", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}
static char DirectDraw_RestoreDisplayMode__doc__[] =
""
;
static PyObject *
DirectDraw_RestoreDisplayMode(DirectDrawObject *self, PyObject *args)
{
  	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	hr = self->pI->RestoreDisplayMode();
	if (FAILED(hr)){
		seterror("DirectDraw_RestoreDisplayMode", hr);
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
	DDSURFACEDESCObject *ddsdObj;
	if (!PyArg_ParseTuple(args, "O!",&DDSURFACEDESCType,&ddsdObj))
		return NULL;
	
	DirectDrawSurfaceObject *obj = newDirectDrawSurfaceObject();
	if( (ddsdObj->sd.dwFlags & DDSD_WIDTH)  && (ddsdObj->sd.dwFlags & DDSD_HEIGHT) ){
		obj->rc.right = ddsdObj->sd.dwWidth;
		obj->rc.bottom = ddsdObj->sd.dwHeight;
		}
	HRESULT hr = self->pI->CreateSurface(&ddsdObj->sd, &obj->pI, NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDraw_CreateSurface", hr);
		return NULL;
	}
	hr = GetSurfaceRect(obj->pI, &obj->rc);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDraw_CreateSurface:GetSurfaceRect", hr);
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
	DWORD dwFlags = DDPCAPS_8BIT | DDPCAPS_ALLOW256;
	if (!PyArg_ParseTuple(args, "|i", &dwFlags))
		return NULL;	
	HRESULT hr;
	PALETTEENTRY colorTable[256];
	HDC hdc = GetDC(NULL);
	GetSystemPaletteEntries(hdc, 0, 256, colorTable);
	ReleaseDC(NULL, hdc);
	for(int i=0;i<256;i++) colorTable[i].peFlags = PC_RESERVED;
	DirectDrawPaletteObject *obj = newDirectDrawPaletteObject();	
	hr = self->pI->CreatePalette(dwFlags, (PALETTEENTRY*)colorTable, &obj->pI, NULL);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDraw_CreatePalette", hr);
		return NULL;
	}
	return (PyObject*) obj;
}

static struct PyMethodDef DirectDraw_methods[] = {
	{"SetCooperativeLevel", (PyCFunction)DirectDraw_SetCooperativeLevel, METH_VARARGS, DirectDraw_SetCooperativeLevel__doc__},
	{"SetDisplayMode", (PyCFunction)DirectDraw_SetDisplayMode, METH_VARARGS, DirectDraw_SetDisplayMode__doc__},
	{"RestoreDisplayMode", (PyCFunction)DirectDraw_RestoreDisplayMode, METH_VARARGS, DirectDraw_RestoreDisplayMode__doc__},
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

static char DirectDrawSurface_GetAttachedSurface__doc__[] =
""
;
static PyObject *
DirectDrawSurface_GetAttachedSurface(DirectDrawSurfaceObject *self, PyObject *args)
{
	DWORD dwCaps;
	if (!PyArg_ParseTuple(args, "i",&dwCaps))
		return NULL;	
	HRESULT hr;
	DDSCAPS caps; caps.dwCaps = dwCaps;
	DirectDrawSurfaceObject *obj = newDirectDrawSurfaceObject();	
	obj->releaseI = false;
	hr = self->pI->GetAttachedSurface(&caps, &obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("DirectDrawSurface_GetAttachedSurface", hr);
		return NULL;
	}
	return (PyObject *)obj;
}

static char DirectDrawSurface_AddAttachedSurface__doc__[] =
""
;
static PyObject *
DirectDrawSurface_AddAttachedSurface(DirectDrawSurfaceObject *self, PyObject *args)
{
	DirectDrawSurfaceObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&DirectDrawSurfaceType,&obj))
		return NULL;	
	HRESULT hr;
	hr = self->pI->AddAttachedSurface(obj->pI);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_AddAttachedSurface", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectDrawSurface_SetClipper__doc__[] =
""
;
static PyObject *
DirectDrawSurface_SetClipper(DirectDrawSurfaceObject *self, PyObject *args)
{
	DirectDrawClipperObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&DirectDrawClipperType,&obj))
		return NULL;	
	HRESULT hr;
	hr = self->pI->SetClipper(obj->pI);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_SetClipper", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectDrawSurface_SetPalette__doc__[] =
""
;
static PyObject *
DirectDrawSurface_SetPalette(DirectDrawSurfaceObject *self, PyObject *args)
{
	DirectDrawPaletteObject *obj;
	if (!PyArg_ParseTuple(args, "O!",&DirectDrawPaletteType,&obj))
		return NULL;	
	HRESULT hr;
	hr = self->pI->SetPalette(obj->pI);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_SetPalette", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}


static char DirectDrawSurface_Blt__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt(DirectDrawSurfaceObject *self, PyObject *args)
{
	RECT rcTo;
	DirectDrawSurfaceObject *ddsFrom;
	RECT rcFrom;
	DWORD dwFlags = DDBLT_WAIT;	
	DDBLTFXObject *pbltfx = NULL;
	if (!PyArg_ParseTuple(args, "(iiii)O!(iiii)|iO!",
			&rcTo.left,&rcTo.top,&rcTo.right,&rcTo.bottom, 
			&DirectDrawSurfaceType,&ddsFrom,
			&rcFrom.left,&rcFrom.top,&rcFrom.right,&rcFrom.bottom, 
			&dwFlags,
			&DDBLTFXType,&pbltfx
			))
		return NULL;

	if(IsRectEmpty(&rcTo) || IsRectEmpty(&rcFrom)){
		// nothing to blit
		Py_INCREF(Py_None);
		return Py_None;	
		}

	HRESULT hr;

	// check first destination surface
	hr = self->pI->IsLost();
	if(hr==DDERR_SURFACELOST)
		hr = self->pI->Restore();
	
	if(FAILED(hr)){
		// failed to restore,
		// we can not do the blt now
		Py_INCREF(Py_None);
		return Py_None;
	}

	// abd then the source
	hr = ddsFrom->pI->IsLost();
	if(FAILED(hr)){
		// no point in proceeding
		// what we have draw at the source surface
		// has been lost
		Py_INCREF(Py_None);
		return Py_None;
	}

	// cache source surface dimensions
	if(IsRectEmpty(&ddsFrom->rc)){
		hr = GetSurfaceRect(ddsFrom->pI, &ddsFrom->rc);
		if (FAILED(hr)){
			seterror("DirectDrawSurface_BltFill:GetSurfaceRect", hr);
			return NULL;
			}
		}
	
	// check validity of rcFrom
	RECT rcFromInSurf;
	if(!IntersectRect(&rcFromInSurf, &rcFrom, &ddsFrom->rc)){
		seterror("DirectDrawSurface_Blt: Invalid source rectangle");
		return NULL;
		}
	if(!EqualRect(&rcFromInSurf,&rcFrom)){
		seterror("DirectDrawSurface_Blt: Invalid source rectangle");
		return NULL;
		}
	
	// cache destination surface dimensions
	if(IsRectEmpty(&self->rc)){
		hr = GetSurfaceRect(self->pI, &self->rc);
		if (FAILED(hr)){
			seterror("DirectDrawSurface_BltFill:GetSurfaceRect", hr);
			return NULL;
			}
		}
	RECT rcToInSurf;
	if(!IntersectRect(&rcToInSurf, &rcTo, &self->rc)){
		// nothing to draw
		Py_INCREF(Py_None);
		return Py_None;
		}
	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Blt(&rcTo,ddsFrom->pI,&rcFrom,dwFlags,NULL);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectDrawSurface_Flip__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Flip(DirectDrawSurfaceObject *self, PyObject *args)
{
	DWORD dwFlags = DDFLIP_WAIT;	
	if (!PyArg_ParseTuple(args, "|i",&dwFlags))
		return NULL;	
	HRESULT hr;

	hr = self->pI->IsLost();
	if(hr==DDERR_SURFACELOST)
		hr = self->pI->Restore();
	
	if(FAILED(hr)){
		// failed to restore
		// we can not do the blt now
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->Flip(NULL,dwFlags);
	Py_END_ALLOW_THREADS
		
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Flip", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectDrawSurface_GetDC__doc__[] =
""
;
static PyObject *
DirectDrawSurface_GetDC(DirectDrawSurfaceObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	HRESULT hr;
	
	hr = self->pI->IsLost();
	if(hr==DDERR_SURFACELOST)
		hr = self->pI->Restore();
	
	if (FAILED(hr)){
		seterror("DirectDrawSurface_GetDC:Restore", hr);
		return NULL;
	}
	
	HDC hdc;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->GetDC(&hdc);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DirectDrawSurface_GetDC", hr);
		return NULL;
	}
	return Py_BuildValue("i",hdc);
}

static char DirectDrawSurface_ReleaseDC__doc__[] =
""
;
static PyObject *
DirectDrawSurface_ReleaseDC(DirectDrawSurfaceObject *self, PyObject *args)
{
	HDC hdc;
	if (!PyArg_ParseTuple(args, "i",&hdc))
		return NULL;	
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr = self->pI->ReleaseDC(hdc);
	Py_END_ALLOW_THREADS
	if (FAILED(hr)){
		seterror("DirectDrawSurface_ReleaseDC", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static char DirectDrawSurface_SetColorKey__doc__[] =
""
;
static PyObject *
DirectDrawSurface_SetColorKey(DirectDrawSurfaceObject *self, PyObject *args)
{
	DWORD dwFlags = DDCKEY_SRCBLT;
	DWORD dwLow = 0, dwHigh=0; // black
	if (!PyArg_ParseTuple(args, "|i(ii)",&dwFlags,&dwLow,&dwHigh))
		return NULL;	
	HRESULT hr;
	DDCOLORKEY ck;
	ck.dwColorSpaceLowValue = dwLow;
	ck.dwColorSpaceHighValue = dwHigh;
	Py_BEGIN_ALLOW_THREADS	
	hr = self->pI->SetColorKey(dwFlags,&ck);
	Py_END_ALLOW_THREADS	
	if (FAILED(hr)){
		seterror("DirectDrawSurface_SetColorKey", hr);
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}




static WORD LowBitPos(DWORD dword)
	{
	DWORD test=1;
	for (WORD i=0;i<32;i++)
		{
		if ( dword & test )
			return i;
		test<<=1;
		}
	return 0;
	}
static WORD HighBitPos(DWORD dword)
	{
	DWORD test=1;
	test<<=31;
	for (WORD i=0;i<32;i++)
		{
		if ( dword & test )
			return (WORD)(31-i);
		test>>=1;
		}
	return 0;
	}

static DWORD dwRGBBitCount = 24;  // in (4, 8, 16, 24, 32)
static WORD numREDbits=8, numGREENbits=8, numBLUEbits=8;
static WORD loREDbit=16, loGREENbit=8, loBLUEbit=0;
static PALETTEENTRY paletteEntry[256];
static BYTE blendTable[256][256];

static char DirectDrawSurface_GetPixelFormat__doc__[] =
""
;
static PyObject *
DirectDrawSurface_GetPixelFormat(DirectDrawSurfaceObject *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	DDPIXELFORMAT format;
	ZeroMemory(&format, sizeof(format) );
	format.dwSize=sizeof(format);
	HRESULT hr = self->pI->GetPixelFormat(&format);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_GetPixelFormat", hr);
		return NULL;
	}	

	dwRGBBitCount = format.dwRGBBitCount;
		
	loREDbit = LowBitPos( format.dwRBitMask );
	WORD hiREDbit = HighBitPos( format.dwRBitMask );
	numREDbits=(WORD)(hiREDbit-loREDbit+1);

	loGREENbit = LowBitPos( format.dwGBitMask );
	WORD hiGREENbit = HighBitPos( format.dwGBitMask );
	numGREENbits=(WORD)(hiGREENbit-loGREENbit+1);

	loBLUEbit  = LowBitPos( format.dwBBitMask );
	WORD hiBLUEbit  = HighBitPos(format.dwBBitMask);
	numBLUEbits=(WORD)(hiBLUEbit-loBLUEbit+1);

	Py_BEGIN_ALLOW_THREADS	
	if(format.dwRGBBitCount==8)
		{
		HDC hdc = GetDC(NULL);
		GetSystemPaletteEntries(hdc, 0, 256, paletteEntry);
		ReleaseDC(NULL, hdc);
		}
	Py_END_ALLOW_THREADS	
	return Py_BuildValue("iiii",dwRGBBitCount, numREDbits, numGREENbits, numBLUEbits);
	}

__forceinline int blend(int w, int c1, int c2)
	{
	return (c1==c2)?c1:(c1 + w*(c2-c1)/256);
	}

int FindColour(int r, int g, int b)
	{
	LPPALETTEENTRY palette = paletteEntry;
	int   best = 0;
	int   best_error = INT_MAX;
	for(int i=0;i<256;i++)
		{
		int er,eg,eb;
		er = r - (int)palette[i].peRed; er *= er;
		eg = g - (int)palette[i].peGreen; eg *= eg;
		eb = b - (int)palette[i].peBlue; eb *= eb;
		int error = er + eg + eb;
		if (error < best_error)
			{
			best_error = error;
			best = i;
			}
		}
	return best;
	}

int FindColourFast(int r, int g, int b)
	{
	LPPALETTEENTRY palette = paletteEntry;
	int   best = 0;
	int   best_error = INT_MAX;
	for(int i=0;i<24;i++)
		{
		int er,eg,eb;
		er = r - (int)palette[i].peRed; er *= er;
		eg = g - (int)palette[i].peGreen; eg *= eg;
		eb = b - (int)palette[i].peBlue; eb *= eb;
		int error = er + eg + eb;
		if (error < best_error)
			{
			best_error = error;
			best = i;
			}
		}
	return best;
	}

void CreateBlendTable(float prop)
	{
	int weight = int(prop*256);
	for(int i=0;i<256;i++)
		{
		BYTE r1 = paletteEntry[i].peRed;
		BYTE g1 = paletteEntry[i].peGreen;
		BYTE b1 = paletteEntry[i].peBlue;
		for(int j=0;j<256;j++)
			{
			BYTE r2 = paletteEntry[j].peRed;
			BYTE g2 = paletteEntry[j].peGreen;
			BYTE b2 = paletteEntry[j].peBlue;

			int r = blend(weight, r1, r2);
			int g = blend(weight, g1, g2);
			int b = blend(weight, b1, b2);
	
			blendTable[i][j] = FindColour(r,g,b);
			}
		}
	}
HRESULT BltBlend8(IDirectDrawSurface *surf, 
					 IDirectDrawSurface *from, IDirectDrawSurface *to, 
					 float prop, DWORD w, DWORD h)
	{
	DDSURFACEDESC desc, desc1, desc2;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	ZeroMemory(&desc1, sizeof(desc1));
	desc1.dwSize=sizeof(desc1);
	ZeroMemory(&desc2, sizeof(desc2));
	desc2.dwSize=sizeof(desc2);
	HRESULT hr;
	hr=surf->Lock(0,&desc,DDLOCK_WAIT ,0);
	if(hr!=DD_OK) return hr;
	hr=from->Lock(0,&desc1,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;
	hr=to->Lock(0,&desc2,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;
	bool usingtable = false;
	if(w*h>65536)
		{
		CreateBlendTable(prop);
		usingtable = true;
		}
	int weight = int(prop*256);
	for(int row=h-1;row>=0;row--)
		{
		BYTE* surfpixel=(BYTE*)desc.lpSurface+row*desc.lPitch;		
		BYTE* surfpixel1=(BYTE*)desc1.lpSurface+row*desc1.lPitch;		
		BYTE* surfpixel2=(BYTE*)desc2.lpSurface+row*desc2.lPitch;		
		for(DWORD col=0;col<w;col++)
			{
			if(usingtable)
				*surfpixel++ = blendTable[*surfpixel1++][*surfpixel2++];
			else
				{
				BYTE r1 = paletteEntry[*surfpixel1].peRed;
				BYTE g1 = paletteEntry[*surfpixel1].peGreen;
				BYTE b1 = paletteEntry[*surfpixel1++].peBlue;

				BYTE r2 = paletteEntry[*surfpixel2].peRed;
				BYTE g2 = paletteEntry[*surfpixel2].peGreen;
				BYTE b2 = paletteEntry[*surfpixel2++].peBlue;

				int r = blend(weight, r1, r2);
				int g = blend(weight, g1, g2);
				int b = blend(weight, b1, b2);
			
				*surfpixel++ = FindColour(r,g,b);
				}
			}
		}
	surf->Unlock(0);
	from->Unlock(0);
	to->Unlock(0);
	return hr;
	}

HRESULT BltBlend16(IDirectDrawSurface *surf, 
					 IDirectDrawSurface *from, IDirectDrawSurface *to, 
					 float prop, DWORD w, DWORD h)
	{
	DDSURFACEDESC desc, desc1, desc2;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	ZeroMemory(&desc1, sizeof(desc1));
	desc1.dwSize=sizeof(desc1);
	ZeroMemory(&desc2, sizeof(desc2));
	desc2.dwSize=sizeof(desc2);
	HRESULT hr;
	hr=surf->Lock(0,&desc,DDLOCK_WAIT,0);
	if(hr!=DD_OK) return hr;
	hr=from->Lock(0,&desc1,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;
	hr=to->Lock(0,&desc2,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;
	int weight = int(prop*256);	
	for(int row=h-1;row>=0;row--)
		{
		WORD* surfpixel=(WORD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		WORD* surfpixel1=(WORD*)((BYTE*)desc1.lpSurface+row*desc1.lPitch);
		WORD* surfpixel2=(WORD*)((BYTE*)desc2.lpSurface+row*desc2.lPitch);
		for (DWORD col=0;col<w;col++)
			{
			// apply transform on pixel: *surfpixel
			WORD r1 = (*surfpixel1 & (WORD)desc1.ddpfPixelFormat.dwRBitMask) >> loREDbit;
			WORD g1 = (*surfpixel1 & (WORD)desc1.ddpfPixelFormat.dwGBitMask) >> loGREENbit;
			WORD b1 = (*surfpixel1++ & (WORD)desc1.ddpfPixelFormat.dwBBitMask) >> loBLUEbit;
			
			WORD r2 = (*surfpixel2 & (WORD)desc2.ddpfPixelFormat.dwRBitMask) >> loREDbit;
			WORD g2 = (*surfpixel2 & (WORD)desc2.ddpfPixelFormat.dwGBitMask) >> loGREENbit;
			WORD b2 = (*surfpixel2++ & (WORD)desc2.ddpfPixelFormat.dwBBitMask) >> loBLUEbit;

			WORD r = (WORD)blend(weight, r1, r2);
			WORD g = (WORD)blend(weight, g1, g2);
			WORD b = (WORD)blend(weight, b1, b2);
			
			*surfpixel++ = WORD((r << loREDbit) | (g << loGREENbit) | (b << loBLUEbit)) ;
			}
		}
	surf->Unlock(0);
	from->Unlock(0);
	to->Unlock(0);
	return hr;
	}

HRESULT BltBlend24(IDirectDrawSurface *surf, 
					 IDirectDrawSurface *from, IDirectDrawSurface *to, 
					 float prop, DWORD w, DWORD h)
	{
	DDSURFACEDESC desc, desc1, desc2;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	ZeroMemory(&desc1, sizeof(desc1));
	desc1.dwSize=sizeof(desc1);
	ZeroMemory(&desc2, sizeof(desc2));
	desc2.dwSize=sizeof(desc2);
	HRESULT hr;
	hr=surf->Lock(0,&desc,DDLOCK_WAIT,0);
	if(hr!=DD_OK) return hr;
	hr=from->Lock(0,&desc1,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;
	hr=to->Lock(0,&desc2,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;

	int weight = int(prop*256);	
	for(int row=h-1;row>=0;row--)
		{
		RGBTRIPLE* surfpixel=(RGBTRIPLE*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		RGBTRIPLE* surfpixel1=(RGBTRIPLE*)((BYTE*)desc1.lpSurface+row*desc1.lPitch);
		RGBTRIPLE* surfpixel2=(RGBTRIPLE*)((BYTE*)desc2.lpSurface+row*desc2.lPitch);
		for (DWORD col=0;col<w;col++)
			{
			// apply transform on pixel: *surfpixel
			DWORD r1 = (*(DWORD*)surfpixel1 & desc1.ddpfPixelFormat.dwRBitMask) >> loREDbit;
			DWORD g1 = (*(DWORD*)surfpixel1 & desc1.ddpfPixelFormat.dwGBitMask) >> loGREENbit;
			DWORD b1 = (*(DWORD*)surfpixel1++ & desc1.ddpfPixelFormat.dwBBitMask) >> loBLUEbit;
			
			DWORD r2 = (*(DWORD*)surfpixel2 & desc2.ddpfPixelFormat.dwRBitMask) >> loREDbit;
			DWORD g2 = (*(DWORD*)surfpixel2 & desc2.ddpfPixelFormat.dwGBitMask) >> loGREENbit;
			DWORD b2 = (*(DWORD*)surfpixel2++ & desc2.ddpfPixelFormat.dwBBitMask) >> loBLUEbit;

			DWORD r = (DWORD)blend(weight, r1, r2);
			DWORD g = (DWORD)blend(weight, g1, g2);
			DWORD b = (DWORD)blend(weight, b1, b2);

			*(DWORD*)surfpixel++ = (r << loREDbit) | (g << loGREENbit) | (b << loBLUEbit);
			}
		}
	surf->Unlock(0);
	from->Unlock(0);
	to->Unlock(0);
	return hr;
	}

HRESULT BltBlend32(IDirectDrawSurface *surf, 
					 IDirectDrawSurface *from, IDirectDrawSurface *to, 
					 float prop, DWORD w, DWORD h)
	{
	DDSURFACEDESC desc, desc1, desc2;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	ZeroMemory(&desc1, sizeof(desc1));
	desc1.dwSize=sizeof(desc1);
	ZeroMemory(&desc2, sizeof(desc2));
	desc2.dwSize=sizeof(desc2);
	HRESULT hr;
	hr=surf->Lock(0,&desc,DDLOCK_WAIT,0);
	if(hr!=DD_OK) return hr;
	hr=from->Lock(0,&desc1,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;
	hr=to->Lock(0,&desc2,DDLOCK_WAIT | DDLOCK_READONLY,0);
	if(hr!=DD_OK) return hr;
	int weight = int(prop*256);	
	for(int row=h-1;row>=0;row--)
		{
		RGBQUAD* surfpixel=(RGBQUAD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		RGBQUAD* surfpixel1=(RGBQUAD*)((BYTE*)desc1.lpSurface+row*desc1.lPitch);
		RGBQUAD* surfpixel2=(RGBQUAD*)((BYTE*)desc2.lpSurface+row*desc2.lPitch);
		for (DWORD col=0;col<w;col++)
			{
			DWORD r1 = (*(DWORD*)surfpixel1 & desc1.ddpfPixelFormat.dwRBitMask) >> loREDbit;
			DWORD g1 = (*(DWORD*)surfpixel1 & desc1.ddpfPixelFormat.dwGBitMask) >> loGREENbit;
			DWORD b1 = (*(DWORD*)surfpixel1++ & desc1.ddpfPixelFormat.dwBBitMask) >> loBLUEbit;
			
			DWORD r2 = (*(DWORD*)surfpixel2 & desc2.ddpfPixelFormat.dwRBitMask) >> loREDbit;
			DWORD g2 = (*(DWORD*)surfpixel2 & desc2.ddpfPixelFormat.dwGBitMask) >> loGREENbit;
			DWORD b2 = (*(DWORD*)surfpixel2++ & desc2.ddpfPixelFormat.dwBBitMask) >> loBLUEbit;

			DWORD r = (DWORD)blend(weight, r1, r2);
			DWORD g = (DWORD)blend(weight, g1, g2);
			DWORD b = (DWORD)blend(weight, b1, b2);

			*(DWORD*)surfpixel++ = (r << loREDbit) | (g << loGREENbit) | (b << loBLUEbit);
			}
		}
	surf->Unlock(0);
	from->Unlock(0);
	to->Unlock(0);
	return hr;
	}

static char DirectDrawSurface_BltBlend__doc__[] =
""
;
static PyObject *
DirectDrawSurface_BltBlend(DirectDrawSurfaceObject *self, PyObject *args)
	{
	float prop;
	DirectDrawSurfaceObject *ddsFrom, *ddsTo;
	if (!PyArg_ParseTuple(args, "O!O!f",&DirectDrawSurfaceType,&ddsFrom,
			&DirectDrawSurfaceType,&ddsTo, &prop))
		return NULL;

	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize = sizeof(desc);
	desc.dwFlags = DDSD_WIDTH | DDSD_HEIGHT;
	self->pI->GetSurfaceDesc(&desc);
	DWORD width  = desc.dwWidth;
	DWORD height = desc.dwHeight;

	HRESULT hr;

	// try restoring target if lost
	hr = self->pI->IsLost();
	if(hr==DDERR_SURFACELOST)
		hr = self->pI->Restore();
	if (FAILED(hr)){
		// we can not do anything, 
		// retry with next iteration
		Py_INCREF(Py_None);
		return Py_None;
	}

	// try next time if we lost sources
	// what we have paint has gone
	hr = ddsFrom->pI->IsLost();
	if (FAILED(hr)){
		Py_INCREF(Py_None);
		return Py_None;
	}
	hr = ddsTo->pI->IsLost();
	if (FAILED(hr)){
		Py_INCREF(Py_None);
		return Py_None;
	}

	Py_BEGIN_ALLOW_THREADS
	if (dwRGBBitCount==8)
		hr=BltBlend8(self->pI, ddsFrom->pI, ddsTo->pI, prop, width, height);
	else if (dwRGBBitCount==16)
		hr=BltBlend16(self->pI, ddsFrom->pI, ddsTo->pI, prop, width, height);
	else if (dwRGBBitCount==24)
		hr=BltBlend24(self->pI, ddsFrom->pI, ddsTo->pI, prop, width, height);
	else if (dwRGBBitCount==32)
		hr=BltBlend32(self->pI, ddsFrom->pI, ddsTo->pI, prop, width, height);
	Py_END_ALLOW_THREADS
		
	if (FAILED(hr)){
		seterror("DirectDrawSurface_BltBlend", hr);
		return NULL;
	}		
	Py_INCREF(Py_None);
	return Py_None;
	}


static char DirectDrawSurface_GetColorMatch__doc__[] =
""
;
static PyObject *
DirectDrawSurface_GetColorMatch(DirectDrawSurfaceObject *self, PyObject *args)
{
	int r,g,b;
	if (!PyArg_ParseTuple(args, "(iii)",&r,&g,&b))
		return NULL;
	
	DWORD ck = 0;
	if (dwRGBBitCount==8){
		ck = FindColour(r,g,b);
		}
	else if(dwRGBBitCount==16){
		int rs = 8-numREDbits;
		int gs = 8-numGREENbits;
		int bs = 8-numBLUEbits;
		ck = ((r >> rs) << loREDbit) | ((g>>gs) << loGREENbit) | ((b>>bs) << loBLUEbit);
		}
	else if (dwRGBBitCount==24 || dwRGBBitCount==32){
		ck = (r<<loREDbit) | (g<<loGREENbit) | (b<<loBLUEbit);		
		}
	
	return Py_BuildValue("i",ck);
}


static char DirectDrawSurface_BltFill__doc__[] =
""
;
static PyObject *
DirectDrawSurface_BltFill(DirectDrawSurfaceObject *self, PyObject *args)
	{
	RECT rect;
	DWORD ddcolor=0;
	if (!PyArg_ParseTuple(args, "(iiii)|i",&rect.left,&rect.top,
			&rect.right,&rect.bottom,&ddcolor))
		return NULL;

	// try first restoring target if lost
	HRESULT hr = self->pI->IsLost();
	if(hr==DDERR_SURFACELOST)
		hr = self->pI->Restore();
	if (FAILED(hr)){
		// next time please
		Py_INCREF(Py_None);
		return Py_None;
	}

	// cache surface dimensions
	if(IsRectEmpty(&self->rc)){
		hr = GetSurfaceRect(self->pI, &self->rc);
		if (FAILED(hr)){
			seterror("DirectDrawSurface_BltFill:GetSurfaceRect", hr);
			return NULL;
			}
		}
	
	// find part of rect inside surface
	RECT rcInSurf;
	if(!IntersectRect(&rcInSurf, &rect, &self->rc)){
		Py_INCREF(Py_None);
		return Py_None;
		}
	
	DDBLTFX bltfx;
	ZeroMemory(&bltfx,sizeof(bltfx));
	bltfx.dwSize = sizeof(bltfx);
	bltfx.dwFillColor = ddcolor;
	Py_BEGIN_ALLOW_THREADS
	hr=self->pI->Blt(&rcInSurf,0,0,DDBLT_COLORFILL | DDBLT_WAIT,&bltfx);
	Py_END_ALLOW_THREADS
		
	if (FAILED(hr)){
		seterror("DirectDrawSurface_BltFill", hr);
		return NULL;
	}		
		
	Py_INCREF(Py_None);
	return Py_None;
	}

static char DirectDrawSurface_IsLost__doc__[] =
""
;
static PyObject *
DirectDrawSurface_IsLost(DirectDrawSurfaceObject *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr=self->pI->IsLost();
	Py_END_ALLOW_THREADS

	if(hr!=DD_OK && hr!=DDERR_SURFACELOST){
		seterror("DirectDrawSurface_IsLost", hr);
		return NULL;
	}
	int ret = (hr==DDERR_SURFACELOST)?1:0;
	return Py_BuildValue("i",ret);
	}

static char DirectDrawSurface_Restore__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Restore(DirectDrawSurfaceObject *self, PyObject *args)
	{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HRESULT hr;
	Py_BEGIN_ALLOW_THREADS
	hr=self->pI->Restore();
	Py_END_ALLOW_THREADS
	int ret = (hr==DD_OK)?1:0;
	return Py_BuildValue("i",ret);
	}


static char DirectDrawSurface_Blt_RGB32_On_RGB32__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB32_On_RGB32(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB32_On_RGB32", hr);
		return NULL;
	}	
	
	Py_BEGIN_ALLOW_THREADS	
	RGBQUAD *p = (RGBQUAD*)pImageBits;
	for(int row=h-1;row>=0;row--)
		{
		RGBQUAD* surfpixel=(RGBQUAD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*(DWORD*)surfpixel++ = (p->rgbRed << loREDbit)|(p->rgbGreen << loGREENbit)| (p->rgbBlue << loBLUEbit);
			}
		}
	Py_END_ALLOW_THREADS
		
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_RGB32_On_RGB24__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB32_On_RGB24(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB32_On_RGB24", hr);
		return NULL;
	}
	
	Py_BEGIN_ALLOW_THREADS	
	RGBQUAD *p = (RGBQUAD*)pImageBits;
	for(int row=h-1;row>=0;row--)
		{
		RGBTRIPLE* surfpixel=(RGBTRIPLE*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*(DWORD*)surfpixel++ = (p->rgbRed << loREDbit)|(p->rgbGreen << loGREENbit)| (p->rgbBlue << loBLUEbit);
			}
		}
	Py_END_ALLOW_THREADS
		
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_RGB32_On_RGB16__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB32_On_RGB16(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB32_On_RGB16", hr);
		return NULL;
	}	
	int rs = 8-numREDbits;
	int gs = 8-numGREENbits;
	int bs = 8-numBLUEbits;	
	Py_BEGIN_ALLOW_THREADS		
	RGBQUAD *p = (RGBQUAD*)pImageBits;	
	for(int row=h-1;row>=0;row--)
		{
		WORD* surfpixel=(WORD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*surfpixel++ = WORD(((p->rgbRed >> rs) << loREDbit) | ((p->rgbGreen>>gs) << loGREENbit) | ((p->rgbBlue>>bs) << loBLUEbit));
			}
		}
	Py_END_ALLOW_THREADS	

	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_RGB32_On_RGB8__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB32_On_RGB8(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB32_On_RGB8", hr);
		return NULL;
	}	

	Py_BEGIN_ALLOW_THREADS	
	RGBQUAD *p = (RGBQUAD*)pImageBits;	
	for(int row=h-1;row>=0;row--)
		{
		BYTE* surfpixel=((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*surfpixel++ = FindColour(p->rgbRed,p->rgbGreen,p->rgbBlue);
			}
		}
	Py_END_ALLOW_THREADS
		
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_RGB24_On_RGB32__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB24_On_RGB32(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB24_On_RGB32", hr);
		return NULL;
	}
	
	Py_BEGIN_ALLOW_THREADS	
	RGBTRIPLE *p = (RGBTRIPLE*)pImageBits;
	for(int row=h-1;row>=0;row--)
		{
		RGBQUAD* surfpixel=(RGBQUAD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*(DWORD*)surfpixel++ = (p->rgbtRed << loREDbit) | (p->rgbtGreen << loGREENbit) | (p->rgbtBlue << loBLUEbit);
			}
		}
	Py_END_ALLOW_THREADS
		
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_RGB24_On_RGB24__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB24_On_RGB24(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB24_On_RGB24", hr);
		return NULL;
	}
	
	Py_BEGIN_ALLOW_THREADS	
	RGBTRIPLE *p = (RGBTRIPLE*)pImageBits;
	for(int row=h-1;row>=0;row--)
		{
		RGBTRIPLE* surfpixel=(RGBTRIPLE*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*(DWORD*)surfpixel++ = (p->rgbtRed << loREDbit) | (p->rgbtGreen << loGREENbit) | (p->rgbtBlue << loBLUEbit);
			}
		}
	Py_END_ALLOW_THREADS	

	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_RGB24_On_RGB16__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB24_On_RGB16(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB24_On_RGB16", hr);
		return NULL;
	}		
	int rs = 8-numREDbits;
	int gs = 8-numGREENbits;
	int bs = 8-numBLUEbits;	
	Py_BEGIN_ALLOW_THREADS	
	RGBTRIPLE *p = (RGBTRIPLE *)pImageBits;
	for(int row=h-1;row>=0;row--)
		{
		WORD* surfpixel=(WORD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*surfpixel++ = WORD(((p->rgbtRed >> rs) << loREDbit) | ((p->rgbtGreen>>gs) << loGREENbit) | ((p->rgbtBlue>>bs) << loBLUEbit));
			}
		}
	Py_END_ALLOW_THREADS	

	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_RGB24_On_RGB8__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_RGB24_On_RGB8(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_RGB24_On_RGB8", hr);
		return NULL;
	}
	
	Py_BEGIN_ALLOW_THREADS		
	RGBTRIPLE *p = (RGBTRIPLE *)pImageBits;
	for(int row=h-1;row>=0;row--)
		{
		BYTE* surfpixel=((BYTE*)desc.lpSurface+row*desc.lPitch);
		for (DWORD col=0;col<w;col++,p++)
			{
			*surfpixel++ = FindColour(p->rgbtRed,p->rgbtGreen,p->rgbtBlue);
			}
		}
	Py_END_ALLOW_THREADS	
	
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}


// optimized implementation of YCrCb2RGB
const int yuvScaleBits = 10;
const int yuvScale = (int)pow(2,yuvScaleBits);
const int yuvScaledMax = yuvScale*255;
static int y1164[256];
static int cr1596[256];
static int cr813[256];
static int cb391[256];
static int cb2018[256];

static void buildYUV420Tables(){
	double f1164 = 1.164*yuvScale;
	double f1596 = 1.596*yuvScale;
	double f813 =  0.813*yuvScale;
	double f391 =  0.391*yuvScale;
	double f2018 = 2.018*yuvScale;
	for(int i=0;i<256;i++){
		y1164[i] = int(f1164*(i - 16)+0.5); 
		cr1596[i] =int(f1596*(i - 128)+0.5);
		cr813[i] = int(f813*(i - 128)+0.5);
		cb391[i] = int(f391*(i - 128)+0.5);
		cb2018[i] = int(f2018*(i - 128)+0.5);
	}
}

__inline void YCrCb2RGB(int Y, int Cr, int Cb, BYTE& r, BYTE& g, BYTE& b){
	int rf, gf, bf;
	rf=gf=bf=y1164[Y];
	rf += cr1596[Cr];
	gf -= cr813[Cr] + cb391[Cb];
	bf += cb2018[Cb];
	r = BYTE( ((rf<=0)?0:(rf>=yuvScaledMax?yuvScaledMax:rf)) >> yuvScaleBits );
	g = BYTE( ((gf<=0)?0:(gf>=yuvScaledMax?yuvScaledMax:gf)) >> yuvScaleBits );
	b = BYTE( ((bf<=0)?0:(bf>=yuvScaledMax?yuvScaledMax:bf)) >> yuvScaleBits );
}

static char DirectDrawSurface_Blt_YUV420_On_RGB32__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_YUV420_On_RGB32(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_YUV420_On_RGB32", hr);
		return NULL;
	}	
	BYTE *pYp = pImageBits;
	BYTE *pCb = pImageBits + w*h;
	BYTE *pCr = pCb + w*h/4;
	
	Py_BEGIN_ALLOW_THREADS		
	for(DWORD row=0;row<h;row++)
		{
		RGBQUAD* surfpixel=(RGBQUAD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		BYTE *pCbRow = pCb + (row/2)*(w/2);
		BYTE *pCrRow = pCr + (row/2)*(w/2);				
		for (DWORD col=0;col<w;col+=2)
			{
			BYTE Cb = *pCbRow++;
			BYTE Cr = *pCrRow++;
			BYTE r,g,b;
			
			BYTE Yp = *pYp++;			
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*((DWORD*)surfpixel++) = (r << loREDbit) | (g << loGREENbit) | (b << loBLUEbit);
			
			Yp = *pYp++;			
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*((DWORD*)surfpixel++) = (r << loREDbit) | (g << loGREENbit) | (b << loBLUEbit);
			}
		}
	Py_END_ALLOW_THREADS
		
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_YUV420_On_RGB24__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_YUV420_On_RGB24(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_YUV420_On_RGB24", hr);
		return NULL;
	}			
	BYTE *pYp = pImageBits;
	BYTE *pCb = pImageBits + w*h;
	BYTE *pCr = pCb + w*h/4;
	Py_BEGIN_ALLOW_THREADS		
	for(DWORD row=0;row<h;row++)
		{
		RGBTRIPLE* surfpixel=(RGBTRIPLE*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		BYTE *pCbRow = pCb + (row/2)*(w/2);
		BYTE *pCrRow = pCr + (row/2)*(w/2);		
		for (DWORD col=0;col<w;col+=2)
			{
			BYTE Cb = *pCbRow++;
			BYTE Cr = *pCrRow++;
			BYTE r,g,b;
			
			BYTE Yp = *pYp++;			
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*((DWORD*)surfpixel) = (r << loREDbit) | (g << loGREENbit) | (b << loBLUEbit);
			surfpixel++;
			
			Yp = *pYp++;			
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*((DWORD*)surfpixel) = (r << loREDbit) | (g << loGREENbit) | (b << loBLUEbit);
			surfpixel++;
			}
		}
	Py_END_ALLOW_THREADS		
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_YUV420_On_RGB16__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_YUV420_On_RGB16(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_YUV420_On_RGB16", hr);
		return NULL;
	}	
	
	int rs = 8-numREDbits;
	int gs = 8-numGREENbits;
	int bs = 8-numBLUEbits;
	BYTE *pYp = pImageBits;
	BYTE *pCb = pImageBits + w*h;
	BYTE *pCr = pCb + w*h/4;
	Py_BEGIN_ALLOW_THREADS	
	for(DWORD row=0;row<h;row++)
		{
		WORD *surfpixel=(WORD*)((BYTE*)desc.lpSurface+row*desc.lPitch);
		BYTE *pCbRow = pCb + (row/2)*(w/2);
		BYTE *pCrRow = pCr + (row/2)*(w/2);
		for (DWORD col=0;col<w;col+=2)
			{
			BYTE Cb = *pCbRow++;
			BYTE Cr = *pCrRow++;
			BYTE r,g,b;
			
			BYTE Yp = *pYp++;
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*surfpixel++ = ((r >> rs) << loREDbit) | ((g>>gs) << loGREENbit) | ((b>>bs) << loBLUEbit);

			Yp = *pYp++;
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*surfpixel++ = ((r >> rs) << loREDbit) | ((g>>gs) << loGREENbit) | ((b>>bs) << loBLUEbit);
			}
		}
	Py_END_ALLOW_THREADS		
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char DirectDrawSurface_Blt_YUV420_On_RGB8__doc__[] =
""
;
static PyObject *
DirectDrawSurface_Blt_YUV420_On_RGB8(DirectDrawSurfaceObject *self, PyObject *args)
	{
	UCHAR* pImageBits;
	DWORD w, h;
	if (!PyArg_ParseTuple(args, "iii", &pImageBits, &w, &h))
		return NULL;
	
	DDSURFACEDESC desc;
	ZeroMemory(&desc, sizeof(desc));
	desc.dwSize=sizeof(desc);
	
	HRESULT hr;
	hr=self->pI->Lock(0,&desc, DDLOCK_WAIT, 0);
	if (FAILED(hr)){
		seterror("DirectDrawSurface_Blt_YUV420_On_RGB16", hr);
		return NULL;
	}			
	BYTE *pYp = pImageBits;
	BYTE *pCb = pImageBits + w*h;
	BYTE *pCr = pCb + w*h/4;
	Py_BEGIN_ALLOW_THREADS	
	for(DWORD row=0;row<h;row++)
		{
		BYTE* surfpixel= ((BYTE*)desc.lpSurface+row*desc.lPitch);
		BYTE *pCbRow = pCb + (row/2)*(w/2);
		BYTE *pCrRow = pCr + (row/2)*(w/2);		
		for (DWORD col=0;col<w;col++)
			{
			BYTE Cb = *pCbRow++;
			BYTE Cr = *pCrRow++;
			BYTE r,g,b;
			
			BYTE Yp = *pYp++;
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*surfpixel++ = FindColour(r,g,b);

			Yp = *pYp++;
			YCrCb2RGB(Yp,Cr,Cb,r,g,b);
			*surfpixel++ = FindColour(r,g,b);
			}
		}
	Py_END_ALLOW_THREADS	
	
	self->pI->Unlock(0);
	Py_INCREF(Py_None);
	return Py_None;	
	}

static struct PyMethodDef DirectDrawSurface_methods[] = {
	{"GetSurfaceDesc", (PyCFunction)DirectDrawSurface_GetSurfaceDesc, METH_VARARGS, DirectDrawSurface_GetSurfaceDesc__doc__},
	{"GetAttachedSurface", (PyCFunction)DirectDrawSurface_GetAttachedSurface, METH_VARARGS, DirectDrawSurface_GetAttachedSurface__doc__},
	{"AddAttachedSurface", (PyCFunction)DirectDrawSurface_AddAttachedSurface, METH_VARARGS, DirectDrawSurface_AddAttachedSurface__doc__},
	{"SetClipper", (PyCFunction)DirectDrawSurface_SetClipper, METH_VARARGS, DirectDrawSurface_SetClipper__doc__},
	{"SetPalette", (PyCFunction)DirectDrawSurface_SetPalette, METH_VARARGS, DirectDrawSurface_SetPalette__doc__},
	{"Blt", (PyCFunction)DirectDrawSurface_Blt, METH_VARARGS, DirectDrawSurface_Blt__doc__},
	{"Flip", (PyCFunction)DirectDrawSurface_Flip, METH_VARARGS, DirectDrawSurface_Flip__doc__},
	{"GetDC", (PyCFunction)DirectDrawSurface_GetDC, METH_VARARGS, DirectDrawSurface_GetDC__doc__},
	{"ReleaseDC", (PyCFunction)DirectDrawSurface_ReleaseDC, METH_VARARGS, DirectDrawSurface_ReleaseDC__doc__},
	{"SetColorKey", (PyCFunction)DirectDrawSurface_SetColorKey, METH_VARARGS, DirectDrawSurface_SetColorKey__doc__},
	{"GetColorMatch", (PyCFunction)DirectDrawSurface_GetColorMatch, METH_VARARGS, DirectDrawSurface_GetColorMatch__doc__},
	{"GetPixelFormat", (PyCFunction)DirectDrawSurface_GetPixelFormat, METH_VARARGS, DirectDrawSurface_GetPixelFormat__doc__},
	{"BltBlend", (PyCFunction)DirectDrawSurface_BltBlend, METH_VARARGS, DirectDrawSurface_BltBlend__doc__},
	{"BltFill", (PyCFunction)DirectDrawSurface_BltFill, METH_VARARGS, DirectDrawSurface_BltFill__doc__},
	{"IsLost", (PyCFunction)DirectDrawSurface_IsLost, METH_VARARGS, DirectDrawSurface_IsLost__doc__},
	{"Restore", (PyCFunction)DirectDrawSurface_Restore, METH_VARARGS, DirectDrawSurface_Restore__doc__},

	{"Blt_RGB32_On_RGB32", (PyCFunction)DirectDrawSurface_Blt_RGB32_On_RGB32, METH_VARARGS, DirectDrawSurface_Blt_RGB32_On_RGB32__doc__},
	{"Blt_RGB32_On_RGB24", (PyCFunction)DirectDrawSurface_Blt_RGB32_On_RGB24, METH_VARARGS, DirectDrawSurface_Blt_RGB32_On_RGB24__doc__},
	{"Blt_RGB32_On_RGB16", (PyCFunction)DirectDrawSurface_Blt_RGB32_On_RGB16, METH_VARARGS, DirectDrawSurface_Blt_RGB32_On_RGB16__doc__},
	{"Blt_RGB32_On_RGB8", (PyCFunction)DirectDrawSurface_Blt_RGB32_On_RGB8, METH_VARARGS, DirectDrawSurface_Blt_RGB32_On_RGB8__doc__},

	{"Blt_RGB24_On_RGB32", (PyCFunction)DirectDrawSurface_Blt_RGB24_On_RGB32, METH_VARARGS, DirectDrawSurface_Blt_RGB24_On_RGB32__doc__},
	{"Blt_RGB24_On_RGB24", (PyCFunction)DirectDrawSurface_Blt_RGB24_On_RGB24, METH_VARARGS, DirectDrawSurface_Blt_RGB24_On_RGB24__doc__},
	{"Blt_RGB24_On_RGB16", (PyCFunction)DirectDrawSurface_Blt_RGB24_On_RGB16, METH_VARARGS, DirectDrawSurface_Blt_RGB24_On_RGB16__doc__},
	{"Blt_RGB24_On_RGB8", (PyCFunction)DirectDrawSurface_Blt_RGB24_On_RGB8, METH_VARARGS, DirectDrawSurface_Blt_RGB24_On_RGB8__doc__},

	{"Blt_YUV420_On_RGB32", (PyCFunction)DirectDrawSurface_Blt_YUV420_On_RGB32, METH_VARARGS, DirectDrawSurface_Blt_YUV420_On_RGB32__doc__},
	{"Blt_YUV420_On_RGB24", (PyCFunction)DirectDrawSurface_Blt_YUV420_On_RGB24, METH_VARARGS, DirectDrawSurface_Blt_YUV420_On_RGB24__doc__},
	{"Blt_YUV420_On_RGB16", (PyCFunction)DirectDrawSurface_Blt_YUV420_On_RGB16, METH_VARARGS, DirectDrawSurface_Blt_YUV420_On_RGB16__doc__},
	{"Blt_YUV420_On_RGB8", (PyCFunction)DirectDrawSurface_Blt_YUV420_On_RGB8, METH_VARARGS, DirectDrawSurface_Blt_YUV420_On_RGB8__doc__},

	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DirectDrawSurface_dealloc(DirectDrawSurfaceObject *self)
{
	/* XXXX Add your own cleanup code here */
	Py_BEGIN_ALLOW_THREADS
	if(self->releaseI && self->pI)
		{
		try {
			self->pI->Release();
			}
		catch(...){}
		}
	Py_END_ALLOW_THREADS
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

static char DirectDrawPalette_GetEntries__doc__[] =
""
;
static PyObject *
DirectDrawPalette_GetEntries(DirectDrawPaletteObject *self, PyObject *args)
{
	DWORD start=0, count=256;
	if (!PyArg_ParseTuple(args, "|ii",&start,&count))
		return NULL;	
	HRESULT hr = S_OK;
	PALETTEENTRY colorTable[256];
	hr = self->pI->GetEntries(0, start, count, (PALETTEENTRY*)colorTable);
	if (FAILED(hr)){
		seterror("DirectDrawPalette_GetEntries", hr);
		return NULL;
	}
	// return colorTable
	Py_INCREF(Py_None);
	return Py_None;
}



static struct PyMethodDef DirectDrawPalette_methods[] = {
	{"GetEntries", (PyCFunction)DirectDrawPalette_GetEntries, METH_VARARGS, DirectDrawPalette_GetEntries__doc__},
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
static char DDSURFACEDESC_GetFlags__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_GetFlags(DDSURFACEDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i",self->sd.dwFlags);
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
static char DDSURFACEDESC_GetCaps__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_GetCaps(DDSURFACEDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i",self->sd.ddsCaps.dwCaps);
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

static char DDSURFACEDESC_GetSize__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_GetSize(DDSURFACEDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("(ii)",self->sd.dwWidth,self->sd.dwHeight);
}


static char DDSURFACEDESC_GetRGBBitCount__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_GetRGBBitCount(DDSURFACEDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if (!(self->sd.ddpfPixelFormat.dwFlags & DDPF_RGB)){
		seterror("GetRGBBitCount failed. Format is not RGB.");
		return NULL;
	}
	return Py_BuildValue("i",self->sd.ddpfPixelFormat.dwRGBBitCount);
}

static char DDSURFACEDESC_GetRGBMasks__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_GetRGBMasks(DDSURFACEDESCObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if (!(self->sd.ddpfPixelFormat.dwFlags & DDPF_RGB)){
		seterror("GetRGBMasks failed. Format is not RGB.");
		return NULL;
	}
	return Py_BuildValue("(iii)",self->sd.ddpfPixelFormat.dwRBitMask,
			self->sd.ddpfPixelFormat.dwGBitMask, 
			self->sd.ddpfPixelFormat.dwBBitMask);
}

static char DDSURFACEDESC_SetBackBufferCount__doc__[] =
""
;
static PyObject*
DDSURFACEDESC_SetBackBufferCount(DDSURFACEDESCObject *self, PyObject *args)
{
	DWORD count;
	if (!PyArg_ParseTuple(args, "i",&count))
		return NULL;
	self->sd.dwBackBufferCount = count;
	Py_INCREF(Py_None);
	return Py_None;
}

	
static struct PyMethodDef DDSURFACEDESC_methods[] = {
	{"Clear", (PyCFunction)DDSURFACEDESC_Clear, METH_VARARGS, DDSURFACEDESC_Clear__doc__},
	{"SetFlags", (PyCFunction)DDSURFACEDESC_SetFlags, METH_VARARGS, DDSURFACEDESC_SetFlags__doc__},
	{"GetFlags", (PyCFunction)DDSURFACEDESC_GetFlags, METH_VARARGS, DDSURFACEDESC_GetFlags__doc__},
	{"SetCaps", (PyCFunction)DDSURFACEDESC_SetCaps, METH_VARARGS, DDSURFACEDESC_SetCaps__doc__},
	{"GetCaps", (PyCFunction)DDSURFACEDESC_GetCaps, METH_VARARGS, DDSURFACEDESC_GetCaps__doc__},
	{"SetSize", (PyCFunction)DDSURFACEDESC_SetSize, METH_VARARGS, DDSURFACEDESC_SetSize__doc__},
	{"GetSize", (PyCFunction)DDSURFACEDESC_GetSize, METH_VARARGS, DDSURFACEDESC_GetSize__doc__},
	{"GetRGBBitCount", (PyCFunction)DDSURFACEDESC_GetRGBBitCount, METH_VARARGS, DDSURFACEDESC_GetRGBBitCount__doc__},
	{"GetRGBMasks", (PyCFunction)DDSURFACEDESC_GetRGBMasks, METH_VARARGS, DDSURFACEDESC_GetRGBMasks__doc__},
	{"SetBackBufferCount", (PyCFunction)DDSURFACEDESC_SetBackBufferCount, METH_VARARGS, DDSURFACEDESC_SetBackBufferCount__doc__},
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

////////////////////////////////////////////
// DDBLTFX struct object 

static char DDBLTFX_Clear__doc__[] =
"Clear DDBLTFX struct for reuse"
;
static PyObject *
DDBLTFX_Clear(DDBLTFXObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	memset(&self->bltfx, 0, sizeof(self->bltfx));
	self->bltfx.dwSize = sizeof(self->bltfx);
	Py_INCREF(Py_None);
	return Py_None;
}

static char DDBLTFX_SetDDFX__doc__[] =
""
;
static PyObject*
DDBLTFX_SetDDFX(DDBLTFXObject *self, PyObject *args)
{
	DWORD dwDDFX;
	if (!PyArg_ParseTuple(args, "i",&dwDDFX))
		return NULL;
	self->bltfx.dwDDFX = dwDDFX;
	Py_INCREF(Py_None);
	return Py_None;
}


static struct PyMethodDef DDBLTFX_methods[] = {
	{"Clear", (PyCFunction)DDBLTFX_Clear, METH_VARARGS, DDBLTFX_Clear__doc__},
	{"SetDDFX", (PyCFunction)DDBLTFX_SetDDFX, METH_VARARGS, DDBLTFX_SetDDFX__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static void
DDBLTFX_dealloc(DDBLTFXObject *self)
{
	/* XXXX Add your own cleanup code here */
	PyMem_DEL(self);
}

static PyObject *
DDBLTFX_getattr(DDBLTFXObject *self, char *name)
{
	/* XXXX Add your own getattr code here */
	return Py_FindMethod(DDBLTFX_methods, (PyObject *)self, name);
}

static char DDBLTFXType__doc__[] =
""
;

static PyTypeObject DDBLTFXType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"DDBLTFX",			/*tp_name*/
	sizeof(DDBLTFXObject),		/*tp_basicsize*/
	0,				/*tp_itemsize*/
	/* methods */
	(destructor)DDBLTFX_dealloc,	/*tp_dealloc*/
	(printfunc)0,		/*tp_print*/
	(getattrfunc)DDBLTFX_getattr,	/*tp_getattr*/
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
	DDBLTFXType__doc__ /* Documentation string */
};

// End of code for DDBLTFX object 
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

#ifdef USE_DDRAWEX
static char CreateDirectDraw2__doc__[] =
""
;
static PyObject *
CreateDirectDraw2(PyObject *self, PyObject *args)
{
	HWND hWnd;
	if (!PyArg_ParseTuple(args, "i",&hWnd))
		return NULL;	
	
	IDirectDrawFactory *lpDDF=NULL;
    HRESULT hr = CoCreateInstance(CLSID_DirectDrawFactory,
                              NULL,CLSCTX_INPROC_SERVER,
                              IID_IDirectDrawFactory,
                              (void **)&lpDDF);
	if (FAILED(hr)){
		seterror("CoCreateInstance DirectDrawFactory", hr);
		return NULL;
	}

	IDirectDraw  *lpDD1=NULL;
	hr = lpDDF->CreateDirectDraw(NULL,hWnd,DDSCL_NORMAL ,0,NULL,&lpDD1);
	lpDDF->Release();
	if (FAILED(hr)){
		seterror("CreateDirectDraw", hr);
		return NULL;
	}

	DirectDrawObject *obj = newDirectDrawObject();
	if (obj == NULL) return NULL;
	hr=lpDD1->QueryInterface(IID_IDirectDraw2,(void**)&obj->pI);
	if (FAILED(hr)){
		Py_DECREF(obj);
		seterror("CreateDirectDraw2", hr);
		return NULL;
	}
	return (PyObject*)obj;
}
#endif //USE_DDRAWEX



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


//
static char CreateDDBLTFX__doc__[] =
"create a DDBLTFX structure"
;
static PyObject *
CreateDDBLTFX(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	DDBLTFXObject *obj = newDDBLTFXObject();
	if (obj == NULL)
		return NULL;
	return (PyObject*)obj;
}

static char CreateSurfaceObject__doc__[] =
""
;
static PyObject *
CreateSurfaceObject(PyObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;	
	DirectDrawSurfaceObject *obj = newDirectDrawSurfaceObject();	
	return (PyObject*) obj;
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
#ifdef USE_DDRAWEX
	{"CreateDirectDraw2", (PyCFunction)CreateDirectDraw2, METH_VARARGS, CreateDirectDraw2__doc__},
#endif
	{"CreateDDSURFACEDESC", (PyCFunction)CreateDDSURFACEDESC, METH_VARARGS, CreateDDSURFACEDESC__doc__},
	{"CreateDDBLTFX", (PyCFunction)CreateDDBLTFX, METH_VARARGS, CreateDDBLTFX__doc__},
	{"CreateSurfaceObject", (PyCFunction)CreateSurfaceObject, METH_VARARGS, CreateSurfaceObject__doc__},
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

static struct constentry _ddckey[] ={
	{"DDCKEY_COLORSPACE",DDCKEY_COLORSPACE},
	{"DDCKEY_DESTBLT",DDCKEY_DESTBLT},
	{"DDCKEY_DESTOVERLAY",DDCKEY_DESTOVERLAY},
	{"DDCKEY_SRCBLT",DDCKEY_SRCBLT},
	{"DDCKEY_SRCOVERLAY",DDCKEY_SRCOVERLAY},
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

	buildYUV420Tables();
	
	// add 'error'
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("ddraw.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	// add symbolic constants
	FATAL_ERROR_IF(SetItemEnum(d,_ddscl)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddsd)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddscaps)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddblt)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddbltfast)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddflip)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddlock)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddgbs)<0)
	FATAL_ERROR_IF(SetItemEnum(d,_ddckey)<0)

	// Check for errors
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module ddraw");
}
