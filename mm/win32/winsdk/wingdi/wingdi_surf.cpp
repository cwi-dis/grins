
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

// static
HMODULE JpgDecoder::s_hDLL = LoadLibrary(TEXT("libjpeg.dll"));

struct PyDIBSurf
	{
	PyObject_HEAD
	HBITMAP m_hBmp;

	surface<le::trible> *m_psurf;

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyDIBSurf *createInstance(HBITMAP hBmp = NULL, surface<le::trible> *psurf = NULL)
		{
		PyDIBSurf *instance = PyObject_NEW(PyDIBSurf, &type);
		if (instance == NULL) return NULL;
		instance->m_hBmp = hBmp;
		instance->m_psurf = psurf;
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
	
	le::trible *pBits = NULL;
	BITMAPINFO *pbmpi = GetBmpInfo24(width, height);
	HBITMAP hBmp = CreateDIBSection(hDC, pbmpi, DIB_RGB_COLORS, (void**)&pBits, NULL, 0);
	if(hBmp==NULL || pBits==NULL)
		{
		seterror("CreateDIBSection", GetLastError());
		return NULL;
		}
	surface<le::trible> *psurf = new surface<le::trible>(width, height, 24, pBits);
	if(r != 0 || g != 0 || b!=0)
		{
		le::trible color(r, g, b);
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
	mf.open(TextPtr(filename));
	mf.fillBuffer(16);
	ImgDecoder *decoder = CreateImgDecoder(mf, hDC);
	if(decoder == NULL)
		{
		seterror("CreateDIBSurfaceFromFile", "cant find a decoder for image format");
		return NULL;
		}
	DIBSurf *pDIBSurf = decoder->decode();
	delete decoder;
	if(pDIBSurf == NULL)
		return NULL;
	HBITMAP hBmp = pDIBSurf->detach_handle();
	surface<le::trible>* psurf = pDIBSurf->detach_pixmap();
	delete pDIBSurf;
	return (PyObject*)PyDIBSurf::createInstance(hBmp, psurf);
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

	SelectObject(hdst, hsrcold);
	DeleteDC(hdst);

	SelectObject(hsrc, hdstold);
	DeleteDC(hsrc);

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
		return Py_BuildValue("i", 24);
	return Py_BuildValue("i", self->m_psurf->get_depth());
	}

static PyObject* PyDIBSurf_Fill(PyDIBSurf *self, PyObject *args)
	{ 
	int r, g, b;
	if(!PyArg_ParseTuple(args, "(iii)", &r, &g, &b))
		return NULL;
	if(self->m_psurf != NULL)
		{
		le::trible color(r, g, b);
		self->m_psurf->fill(color);
		}
	return none();
	}

PyMethodDef PyDIBSurf::methods[] = {
	{"DeleteObject", (PyCFunction)PyDIBSurf_DeleteObject, METH_VARARGS, ""},
	{"Detach", (PyCFunction)PyDIBSurf_Detach, METH_VARARGS, ""},
	{"GetSafeHandle", (PyCFunction)PyDIBSurf_GetSafeHandle, METH_VARARGS, ""},
	{"GetSize", (PyCFunction)PyDIBSurf_GetSize, METH_VARARGS, ""},
	{"GetDepth", (PyCFunction)PyDIBSurf_GetDepth, METH_VARARGS, ""},

	{"Fill", (PyCFunction)PyDIBSurf_Fill, METH_VARARGS, ""},
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

