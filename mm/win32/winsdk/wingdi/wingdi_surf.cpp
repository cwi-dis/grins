
#include "wingdi_surf.h"

#include "utils.h"

#include "surface.h"

#include "../common/memfile.h"

// native image decoders
#include "decode_bmp.h"
#include "decode_gif.h"

// interface to native image decoders
#include "decode_jpg.h"
#include "decode_png.h"

struct PyDIBSurf
	{
	PyObject_HEAD
	HBITMAP m_hBmp;

	surface<color_repr_t> *m_psurf;
	bool m_is_transparent;
	BYTE m_rgb[3];

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyDIBSurf *createInstance(HBITMAP hBmp = NULL, surface<color_repr_t> *psurf = NULL, bool istransp = false, BYTE *rgb = NULL)
		{
		PyDIBSurf *instance = PyObject_NEW(PyDIBSurf, &type);
		if (instance == NULL) return NULL;
		instance->m_hBmp = hBmp;
		instance->m_psurf = psurf;
		instance->m_is_transparent = istransp;
		if(istransp)
			{
			instance->m_rgb[0] = rgb[0];
			instance->m_rgb[1] = rgb[1];
			instance->m_rgb[2] = rgb[2];
			}
		return instance;
		}

	static void dealloc(PyDIBSurf *instance) 
		{ 
		if(instance->m_hBmp != NULL)
			DeleteObject((HGDIOBJ)instance->m_hBmp);
		if(instance->m_psurf != NULL)
			delete instance->m_psurf;
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyDIBSurf *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};

PyObject* Wingdi_CreateDIBSurface(PyObject *self, PyObject *args)
	{
	PyObject *obj;
	int width, height;
	int r=0, g=0, b=0;
	if (!PyArg_ParseTuple(args, "Oii|(iii)", &obj, &width, &height, &r, &g, &b))
		return NULL;
	HDC hDC = (HDC)GetGdiObjHandle(obj);
	
	color_repr_t *pBits = NULL;
	BITMAPINFO *pbmpi = GetBmpInfo(width, height, color_repr_t::get_bits_size());
	HBITMAP hBmp = CreateDIBSection(hDC, pbmpi, DIB_RGB_COLORS, (void**)&pBits, NULL, 0);
	if(hBmp==NULL || pBits==NULL)
		{
		seterror("CreateDIBSection", GetLastError());
		return NULL;
		}
	surface<color_repr_t> *psurf = new surface<color_repr_t>(width, height, color_repr_t::get_bits_size(), pBits);
	if(r != 0 || g != 0 || b!=0)
		{
		color_repr_t color(r, g, b);
		psurf->fill(color);
		}
	return (PyObject*)PyDIBSurf::createInstance(hBmp, psurf);
	}

static ImgDecoder* CreateImgDecoder(memfile& mf, HDC hDC)
	{
	ImgDecoder *decoder = NULL;

	// jpg
	decoder = new JpgDecoder(mf, hDC, seterror);
	if(decoder->can_decode())
		return decoder;
	delete decoder;
	
	// gif
	decoder = new GifDecoder(mf, hDC, seterror);
	if(decoder->can_decode())
		return decoder;
	delete decoder;

	// png
	decoder = new PngDecoder(mf, hDC, seterror);
	if(decoder->can_decode())
		return decoder;
	delete decoder;

	// bmp
	decoder= new BmpDecoder(mf, hDC, seterror);
	if(decoder->can_decode())
		return decoder;
	delete decoder;

	return NULL;
	}

PyObject* Wingdi_CreateDIBSurfaceFromFile(PyObject *self, PyObject *args)
	{
	PyObject *obj;
	char *filename;
	if (!PyArg_ParseTuple(args, "Os", &obj, &filename))
		return NULL;
	HDC hDC = (HDC)GetGdiObjHandle(obj);
	
	memfile mf;
	if(!mf.open(TextPtr(filename)))
		{
		seterror("CreateDIBSurfaceFromFile", "failed to read file");
		return NULL;
		}

	ImgDecoder *decoder = CreateImgDecoder(mf, hDC);
	if(decoder == NULL)
		{
		seterror("CreateDIBSurfaceFromFile", "cant find a decoder for image format");
		return NULL;
		}
	DIBSurf *pDIBSurf = decoder->decode();
	bool istransp = decoder->is_transparent();
	BYTE rgb[3];
	if(istransp) 
		decoder->get_transparent_color(rgb);
	delete decoder;
	if(pDIBSurf == NULL)
		return NULL;
	HBITMAP hBmp = pDIBSurf->detach_handle();
	surface<color_repr_t>* psurf = pDIBSurf->detach_pixmap();
	delete pDIBSurf;
	return (PyObject*)PyDIBSurf::createInstance(hBmp, psurf, istransp, rgb);
	}

PyObject* Wingdi_BitBltDIBSurface(PyObject *self, PyObject *args)
	{
	PyDIBSurf *srcobj, *dstobj;
	PyObject *srcrcobj, *dstrcobj;
	PyObject *rgnobj = NULL;
	if(!PyArg_ParseTuple(args, "O!O!OO|O", &PyDIBSurf::type, &srcobj, 
		&PyDIBSurf::type, &dstobj,
		&srcrcobj, &dstrcobj, &rgnobj))
		return NULL;
	
	int ls, ts, rs, bs;
	if(!PyArg_ParseTuple(srcrcobj, "iiii", &ls,  &ts,  &rs, &bs)) 
		{
		PyErr_Clear();
		seterror("BitBltDIBSurface", "Argument not a rectangle");
		return NULL;
		}
	int swidth = srcobj->m_psurf->get_width();
	int sheight = srcobj->m_psurf->get_height();
	ls = ls<0?0:ls;
	ts = ts<0?0:ts;
	rs = rs<0?0:(rs>swidth?swidth:rs);
	bs = bs<0?0:(bs>sheight?sheight:bs);

	int ld, td, rd, bd;
	if(!PyArg_ParseTuple(dstrcobj, "iiii", &ld,  &td,  &rd, &bd)) 
		{
		PyErr_Clear();
		seterror("BitBltDIBSurface", "Argument not a rectangle");
		return NULL;
		}
	int dwidth = dstobj->m_psurf->get_width();
	int dheight = dstobj->m_psurf->get_height();
	ld = ld<0?0:ld;
	td = td<0?0:td;
	rd = rd<0?0:(rd>dwidth?dwidth:rd);
	bd = bd<0?0:(bd>dheight?dheight:bd);

	if(rd-ld != rs-ls || bd-td != bs-ts)
		{
		seterror("BitBltDIBSurface", "Rectangles not of equal size");
		return NULL;
		}

	HDC hdc = GetDC(NULL);

	HDC hdst = CreateCompatibleDC(hdc);
	HBITMAP hdstold = (HBITMAP)SelectObject(hdst, dstobj->m_hBmp);
	if(rgnobj != NULL)
		SelectClipRgn(hdst, (HRGN)GetGdiObjHandle(rgnobj));

	HDC hsrc = CreateCompatibleDC(hdst);
	HBITMAP hsrcold = (HBITMAP)SelectObject(hsrc, srcobj->m_hBmp);

	//StretchBlt(hdst, ld, td, rd-ld, bd-td, hsrc, ls, ts, rs-ls, bs-ts, SRCCOPY);
	BitBlt(hdst, ld, td, rd-ld, bd-td, hsrc, ls, ts, SRCCOPY);

	SelectObject(hsrc, hsrcold);
	DeleteDC(hsrc);

	SelectObject(hdst, hdstold);
	DeleteDC(hdst);

	DeleteDC(hdc);
	return none();
	}

PyObject* Wingdi_BltBlendDIBSurface(PyObject *self, PyObject *args)
	{
	PyDIBSurf *srcobj1, *srcobj2, *dstobj;
	double value;
	if(!PyArg_ParseTuple(args, "O!O!O!d", &PyDIBSurf::type, &srcobj1, 
		&PyDIBSurf::type, &srcobj2,
		&PyDIBSurf::type, &dstobj,
		&value))
		return NULL;
	
	dstobj->m_psurf->blend(*srcobj1->m_psurf, *srcobj2->m_psurf, value);

	return none();
	}

//////////////////////////////////
// StretchBltTransparent helpers
inline PyDIBSurf* CreateDIBSurface(HDC hDC, int width, int height)
	{
	color_repr_t *pBits = NULL;
	BITMAPINFO *pbmpi = GetBmpInfo(width, height, color_repr_t::get_bits_size());
	HBITMAP hBmp = CreateDIBSection(hDC, pbmpi, DIB_RGB_COLORS, (void**)&pBits, NULL, 0);
	if(hBmp==NULL || pBits==NULL)
		return NULL;
	surface<color_repr_t> *psurf = new surface<color_repr_t>(width, height, color_repr_t::get_bits_size(), pBits);
	return PyDIBSurf::createInstance(hBmp, psurf);
	}

inline BOOL CopyDCToSurf(HDC hDC, int x, int y, int width, int height, PyDIBSurf *surf)
	{
	HDC hdst = CreateCompatibleDC(hDC);
	HBITMAP hdstold = (HBITMAP)SelectObject(hdst, surf->m_hBmp);
	BOOL res = BitBlt(hdst, 0, 0, width, height, hDC, x, y, SRCCOPY);
	SelectObject(hdst, hdstold);
	DeleteDC(hdst);
	return res;
	}

inline BOOL StretchBltSurf(HDC hDC, PyDIBSurf *surf1, int x1, int y1, int w1, int h1, 
						   PyDIBSurf *surf2, int x2, int y2, int w2, int h2)
	{
	HDC hdst = CreateCompatibleDC(hDC);
	HBITMAP hdstold = (HBITMAP)SelectObject(hdst, surf1->m_hBmp);

	HDC hsrc = CreateCompatibleDC(hdst);
	HBITMAP hsrcold = (HBITMAP)SelectObject(hsrc, surf2->m_hBmp);

	BOOL res = StretchBlt(hdst, x1, y1, w1, h1, hsrc, x2, y2, w2, h2, SRCCOPY);

	SelectObject(hsrc, hsrcold);
	DeleteDC(hsrc);

	SelectObject(hdst, hdstold);
	DeleteDC(hdst);

	return res;
	}

inline BOOL BlitToDC(HDC hDC, int x, int y, int width, int height, PyDIBSurf *surf)
	{
	HDC hSrcDC = CreateCompatibleDC(hDC);
	HBITMAP hsrcold = (HBITMAP)SelectObject(hSrcDC, surf->m_hBmp);
	BOOL res = BitBlt(hDC, x, y, width, height, hSrcDC, 0, 0, SRCCOPY);
	SelectObject(hSrcDC, hsrcold);
	DeleteDC(hSrcDC);
	return res;
	}

PyObject* Wingdi_StretchBltTransparent(PyObject *self, PyObject *args)
	{
	PyObject *dcobj;
	int nXDest, nYDest, nWidthDest, nHeightDest;

	PyDIBSurf *surfobj;
	int nXSrc, nYSrc, nWidthSrc, nHeightSrc;

	if(!PyArg_ParseTuple(args, "O(iiii)O!(iiii)", &dcobj, 
		&nXDest, &nYDest, &nWidthDest,&nHeightDest,
		&PyDIBSurf::type, &surfobj,
		&nXSrc,&nYSrc,&nWidthSrc,&nHeightSrc))
		return NULL;

	HDC hDC = (HDC)GetGdiObjHandle(dcobj);

	// 1. preserve bg step
	// make a copy of dest (surf1)
	PyDIBSurf *surf1 = CreateDIBSurface(hDC, nWidthDest, nHeightDest);
	if(surf1 == NULL)
		{
		seterror("StretchBltTransparent", GetLastError());
		return NULL;
		}
	if(!CopyDCToSurf(hDC, nXDest, nYDest, nWidthDest, nHeightDest, surf1))
		{
		seterror("StretchBltTransparent:CopyDCToSurf", GetLastError());
		return NULL;
		}

	// 2. scaling step
	// stretch blit bmp to a temp surf (surf2)
	PyDIBSurf *surf2 = CreateDIBSurface(hDC, nWidthDest, nHeightDest);
	if(surf2 == NULL)
		{
		Py_XDECREF(surf1);
		seterror("StretchBltTransparent", GetLastError());
		return NULL;
		}
	if(!StretchBltSurf(hDC, surf2, 0, 0, nWidthDest, nHeightDest, surfobj, nXSrc, nYSrc, nWidthSrc, nHeightSrc))
		{
		Py_XDECREF(surf1);
		Py_XDECREF(surf2);
		seterror("StretchBltTransparent:StretchBltSurf", GetLastError());
		return NULL;
		}

	// 3. transfer not transparent bits of surf2 -> surf1
	surf1->m_psurf->copy_transparent(surf2->m_psurf, surfobj->m_rgb);

	// 4. blit surf1 to dc
	if(!BlitToDC(hDC, nXDest, nYDest, nWidthDest, nHeightDest, surf1))
		{
		Py_XDECREF(surf1);
		Py_XDECREF(surf2);
		seterror("StretchBltTransparent:BlitToDC", GetLastError());
		return NULL;
		}

	// 5. cleanup temporaries
	Py_XDECREF(surf1);
	Py_XDECREF(surf2);
	return none();

	/*
	//  ignoring transparency the above is equivalent to:

	HDC hSrcDC = CreateCompatibleDC(hDC);
	HBITMAP hsrcold = (HBITMAP)SelectObject(hSrcDC, surfobj->m_hBmp);

	BOOL res = StretchBlt(hDC, nXDest, nYDest, nWidthDest, nHeightDest, 
		hSrcDC, nXSrc, nYSrc, nWidthSrc, nHeightSrc, SRCCOPY);

	SelectObject(hSrcDC, hsrcold);
	DeleteDC(hSrcDC);

	if(!res){
		seterror("StretchBltTransparent:StretchBlt()", GetLastError());
		return NULL;
		}
	return none();
	*/

	}


////////////////////////////
// module

static PyObject* PyDIBSurf_DeleteObject(PyDIBSurf *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_hBmp != NULL)
		{
		DeleteObject((HGDIOBJ)self->m_hBmp);
		self->m_hBmp = NULL;
		}
	if(self->m_psurf != NULL)
		{
		delete self->m_psurf;
		self->m_psurf = NULL;
		}
	return none();
	}

static PyObject* PyDIBSurf_Detach(PyDIBSurf *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	HBITMAP hBmp = self->m_hBmp;
	self->m_hBmp = NULL;
	if(self->m_psurf != NULL)
		{
		delete self->m_psurf;
		self->m_psurf = NULL;
		}
	return Py_BuildValue("i", hBmp);
	}

static PyObject* PyDIBSurf_GetSafeHandle(PyDIBSurf *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i", self->m_hBmp);
	}

static PyObject* PyDIBSurf_GetSize(PyDIBSurf *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_psurf == NULL)
		return Py_BuildValue("ii", 0, 0);
	return Py_BuildValue("ii", self->m_psurf->get_width(), self->m_psurf->get_height());
	}

static PyObject* PyDIBSurf_GetDepth(PyDIBSurf *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_psurf == NULL)
		return Py_BuildValue("i", color_repr_t::get_bits_size());
	return Py_BuildValue("i", self->m_psurf->get_depth());
	}

static PyObject* PyDIBSurf_Fill(PyDIBSurf *self, PyObject *args)
	{ 
	int r, g, b;
	if(!PyArg_ParseTuple(args, "(iii)", &r, &g, &b))
		return NULL;
	if(self->m_psurf != NULL)
		{
		color_repr_t color(r, g, b);
		self->m_psurf->fill(color);
		}
	return none();
	}

static PyObject* PyDIBSurf_IsTransparent(PyDIBSurf *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i", (self->m_is_transparent?1:0));
	}

static PyObject* PyDIBSurf_GetTransparentColor(PyDIBSurf *self, PyObject *args)
	{ 
	if(!PyArg_ParseTuple(args, ""))
		return NULL;

	if(!self->m_is_transparent)
		{
		seterror("BitBltDIBSurface", "Surface not transparent");
		return NULL;
		}
	return Py_BuildValue("iii", int(self->m_rgb[0]), int(self->m_rgb[1]), int(self->m_rgb[2]));
	}

PyMethodDef PyDIBSurf::methods[] = {
	{"DeleteObject", (PyCFunction)PyDIBSurf_DeleteObject, METH_VARARGS, ""},
	{"Detach", (PyCFunction)PyDIBSurf_Detach, METH_VARARGS, ""},
	{"GetSafeHandle", (PyCFunction)PyDIBSurf_GetSafeHandle, METH_VARARGS, ""},
	{"GetSize", (PyCFunction)PyDIBSurf_GetSize, METH_VARARGS, ""},
	{"GetDepth", (PyCFunction)PyDIBSurf_GetDepth, METH_VARARGS, ""},

	{"Fill", (PyCFunction)PyDIBSurf_Fill, METH_VARARGS, ""},

	{"IsTransparent", (PyCFunction)PyDIBSurf_IsTransparent, METH_VARARGS, ""},
	{"GetTransparentColor", (PyCFunction)PyDIBSurf_GetTransparentColor, METH_VARARGS, ""},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyDIBSurf::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyDIBSurf",			// tp_name
	sizeof(PyDIBSurf),		// tp_basicsize
	0,					// tp_itemsize
	
	// methods
	(destructor)PyDIBSurf::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyDIBSurf::getattr,// tp_getattr
	(setattrfunc)0,	// tp_setattr
	(cmpfunc)0,		// tp_compare
	(reprfunc)0,	// tp_repr
	0,				// tp_as_number
	0,				// tp_as_sequence
	0,				// tp_as_mapping
	(hashfunc)0,	// tp_hash
	(ternaryfunc)0,	// tp_call
	(reprfunc)0,	// tp_str

	// Space for future expansion
	0L,0L,0L,0L,

	"PyDIBSurf Type" // Documentation string
	};

