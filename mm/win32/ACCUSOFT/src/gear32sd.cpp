/***********************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

******************************************************************/

#include "Python.h"
#include "windows.h"

// Define this for GIF support
#define INCLUDE_GIF

#include "..\Gear\gear.h" // Accusoft DLL header.
#pragma comment (lib,"..\\Gear\\Gear32sd.lib")

// Gif convertion
#include "igif.h"

static PyObject *ErrorObject;

static void
seterror(const char *funcname, char *pszmsg)
{
	PyErr_Format(ErrorObject, "%s failed, error = %s", funcname, pszmsg);
}

struct PyImage
	{
	PyObject_HEAD
	HIGEAR m_hIGear;
	int m_transparent_index;
	BYTE m_rgb[3];

	static PyTypeObject type;
	static PyMethodDef methods[];

	static PyImage *createInstance(HIGEAR hIGear = -1)
		{
		PyImage *instance = PyObject_NEW(PyImage, &PyImage::type);
		if (instance == NULL) return NULL;
		instance->m_hIGear = hIGear;
		instance->m_transparent_index = -1;
		return instance;
		}

	static void dealloc(PyImage *instance) 
		{ 
		if(instance->m_hIGear != -1)
			{
			if(IG_image_is_valid(instance->m_hIGear))
				IG_image_delete(instance->m_hIGear);
			}
		PyMem_DEL(instance);
		}

	static PyObject *getattr(PyImage *instance, char *name)
		{ 
		return Py_FindMethod(methods, (PyObject*)instance, name);
		}
	};


/////////////////////
// module

static char ig_load__doc__[] =
""
;
static PyObject* ig_load(PyObject *self, PyObject *args)
	{
	char *filename;
	if(!PyArg_ParseTuple(args,"s",&filename))
		return NULL;

	AT_ERRCOUNT nError = 0;
	HIGEAR img = -1;
	if(true)
		{
		GifConverter gc;
		if(gc.LoadGif(filename))
			{
			Py_BEGIN_ALLOW_THREADS
			nError = IG_load_mem(gc.m_pBmpBuffer, gc.m_dwSize, 1, 1, &img);
			Py_END_ALLOW_THREADS
			if(nError != 0)
				{
				seterror("IG_load_mem", "unknown");
				return NULL;
				}
			PyImage *obj = PyImage::createInstance(img);
			obj->m_transparent_index = gc.m_transparent;
			for(int i=0;i<3;i++) obj->m_rgb[i] = BYTE(gc.m_tc[i]);
			return (PyObject*)obj;
			}
		}

	Py_BEGIN_ALLOW_THREADS
	nError = IG_load_file(filename,&img);
	Py_END_ALLOW_THREADS
	if(nError != 0)
		{
		seterror("IG_load_file", "unknown");
		return NULL;
		}
	return (PyObject*)PyImage::createInstance(img);
	}

static char ig_load_file__doc__[] =
""
;
static PyObject* ig_load_file(PyObject *self, PyObject *args)
	{
	char *filename;
	if(!PyArg_ParseTuple(args,"s",&filename))
		return NULL;

	HIGEAR img;
	AT_ERRCOUNT nError;
	Py_BEGIN_ALLOW_THREADS
	nError = IG_load_file(filename, &img);
	Py_END_ALLOW_THREADS
	if(nError != 0)
		{
		seterror("IG_load_file", "unknown");
		return NULL;
		}
	return (PyObject*)PyImage::createInstance(img);
	}


#ifdef INCLUDE_GIF
static char ig_load_gif__doc__[] =
""
;
static PyObject* ig_load_gif(PyObject *self, PyObject *args)
	{
	char *filename;
	if(!PyArg_ParseTuple(args,"s",&filename))
		return NULL;
	GifConverter gc;
	if(!gc.LoadGif(filename))
		{
		seterror("LoadGif", (char*)(const char*)gc.m_errorMsg);
		return NULL;
		}

	AT_ERRCOUNT nError = 0;
	HIGEAR img = -1;
	Py_BEGIN_ALLOW_THREADS
	nError = IG_load_mem(gc.m_pBmpBuffer, gc.m_dwSize, 1, 1, &img);
	Py_END_ALLOW_THREADS
	if(nError != 0)
		{
		seterror("IG_load_mem", "unknown");
		return NULL;
		}
	PyImage *obj = PyImage::createInstance(img);
	obj->m_transparent_index = gc.m_transparent;
	for(int i=0;i<3;i++) obj->m_rgb[i] = BYTE(gc.m_tc[i]);
	return (PyObject*)obj;
	}
#endif

static char ig_load_mem__doc__[] =
""
;
static PyObject* ig_load_mem(PyObject *self, PyObject *args)
	{
	char *pImage;
	int dwSize;
	int nPageNum=1;
	int nTileNum=1;
	if(!PyArg_ParseTuple(args,"s#|ll",&pImage,&dwSize,&nPageNum,&nTileNum))
		return NULL;
	if(pImage==0)
		{
		seterror("ig_load_mem","Invalid pointer to image");
		return NULL;
		}
	HIGEAR img;
	AT_ERRCOUNT nError = IG_load_mem((LPVOID)pImage,(DWORD)dwSize,(UINT)nPageNum,(UINT)nTileNum,&img);
	if(nError != 0)
		{
		seterror("IG_load_mem", "unknown");
		return NULL;
		}
	return (PyObject*)PyImage::createInstance(img);
	}

static char ig_error_check__doc__[] =
""
;
static PyObject* ig_error_check(PyObject *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args,""))
		return NULL;
	AT_ERRCOUNT nError = IG_error_check();
	return Py_BuildValue("l",(long)nError);
	}

static char ig_error_get__doc__[] =
""
;
static PyObject* ig_error_get(PyObject *self, PyObject *args)
	{
	  INT index;
	  AT_ERRCODE code;
	if(!PyArg_ParseTuple(args,"i", &index))
		return NULL;
	IG_error_get(index,NULL,0,NULL,&code,NULL,NULL);
	return Py_BuildValue("l",(long)code);
	}


/////////////////////////////
// PyImage

static char ig_save_file__doc__[] =
""
;
static PyObject* ig_save_file(PyImage *self, PyObject *args)
	{
	char *filename;
	AT_LMODE lFormatType = IG_SAVE_UNKNOWN; // use filename extension
	if(!PyArg_ParseTuple(args,"s|l",&filename, &lFormatType))
		return NULL;
	AT_ERRCOUNT nError;
	Py_BEGIN_ALLOW_THREADS
	nError = IG_save_file(self->m_hIGear, filename, lFormatType);
	Py_END_ALLOW_THREADS
	if(nError != 0)
		{
		seterror("ig_save_file","IG_save_file failed");
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char ig_image_dimensions_get__doc__[] =
""
;
static PyObject* ig_image_dimensions_get(PyImage *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args, ""))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_image_dimensions_get","Invalid image");
		return NULL;
		}
		

	AT_DIMENSION Width=0,Height=0;
	UINT BitsPerPixel;
	AT_ERRCOUNT nError = IG_image_dimensions_get(self->m_hIGear,&Width,&Height,&BitsPerPixel);
	if(nError != 0)
		{
		seterror("ig_image_dimensions_get","IG_image_dimensions_get failed");
		return NULL;
		}

	return Py_BuildValue("lll",Width,Height,BitsPerPixel);
	}

static char ig_display_transparent_set__doc__[] =
""
;
static PyObject* ig_display_transparent_set(PyImage *self, PyObject *args)
	{
	int r,g,b;	
	BOOL enable;
	if(!PyArg_ParseTuple(args, "(iii)i", &r,&g,&b,&enable))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_display_transparent_set","Invalid image");
		return NULL;
		}
		

	AT_RGB rgb={r,g,b};
	AT_ERRCOUNT nError=IG_display_transparent_set(self->m_hIGear,&rgb,enable);
	if(nError != 0)
		{
		seterror("ig_display_transparent_set","IG_display_transparent_set failed");
		return NULL;
		}
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char ig_palette_entry_get__doc__[] =
""
;
static PyObject* ig_palette_entry_get(PyImage *self,PyObject *args)
	{
	UINT ix;	
	if(!PyArg_ParseTuple(args, "i", &ix))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_palette_entry_get","Invalid image");
		return NULL;
		}

	AT_RGB rgb;
	AT_ERRCOUNT nError=IG_palette_entry_get(self->m_hIGear,&rgb,ix);
	if(nError != 0)
		{
		seterror("ig_palette_entry_get","IG_display_transparent_set failed");
		return NULL;
		}

	return Py_BuildValue("iii",rgb.r,rgb.g,rgb.b);
	}


static char ig_device_rect_set__doc__[] =
""
;
static PyObject* ig_device_rect_set(PyImage *self, PyObject *args)
	{
	AT_RECT rect;
	if (!PyArg_ParseTuple(args,"(iiii)",
						&rect.left, &rect.top,
						&rect.right, &rect.bottom))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_device_rect_set","Invalid image");
		return NULL;
		}

	AT_ERRCOUNT nError = IG_device_rect_set(self->m_hIGear,&rect);
	if(nError != 0)
		{
		seterror("IG_device_rect_set","");
		return NULL;		
		}

	Py_INCREF(Py_None);
	return Py_None;	
	}


static char ig_display_adjust_aspect__doc__[] =
""
;
static PyObject* ig_display_adjust_aspect(PyImage *self, PyObject *args)
	{
	AT_RECT rect;
	int aspect;
	if (!PyArg_ParseTuple(args,"(iiii)i",
						&rect.left, &rect.top,
						&rect.right, &rect.bottom,
						&aspect))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_device_rect_set","Invalid image");
		return NULL;
		}

	AT_ERRCOUNT nError = IG_display_adjust_aspect(self->m_hIGear,&rect,aspect);
	if(nError != 0)
		{
		seterror("IG_display_adjust_aspect","");
		return NULL;		
		}
	
	return Py_BuildValue("(iiii)", rect.left, rect.top,
			     rect.right, rect.bottom);	
	}


static char ig_display_desktop_pattern_set__doc__[] =
""
;
static PyObject* ig_display_desktop_pattern_set(PyImage *self, PyObject *args)
	{
	BOOL bEnabled;
	AT_RGB fg={-1,-1,-1};
	AT_RGB bg={-1,-1,-1};
	if(!PyArg_ParseTuple(args, "i|(iii)(iii)",&bEnabled, &fg.r,&fg.g, &fg.b, &bg.r,&bg.g,&bg.b))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_display_desktop_pattern_set","Invalid image");
		return NULL;
		}

	AT_ERRCOUNT nError = 0;
	Py_BEGIN_ALLOW_THREADS
	nError = IG_display_desktop_pattern_set(self->m_hIGear,NULL,(fg.r>=0)?&fg:NULL,(bg.r>=0)?&bg:NULL,bEnabled!=0?TRUE:FALSE);
	Py_END_ALLOW_THREADS
	if(nError != 0)
		{
		seterror("ig_display_desktop_pattern_set","");
		return NULL;		
		}
		
	Py_INCREF(Py_None);
	return Py_None;	
	}

static char ig_ip_crop__doc__[] =
""
;
static PyObject* ig_ip_crop(PyImage *self, PyObject *args)
	{
	RECT rect;
	if (!PyArg_ParseTuple(args,"(iiii)",
						&rect.left, &rect.top,
						&rect.right, &rect.bottom))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_ip_crop","Invalid image");
		return NULL;
		}

	if(IsRectEmpty(&rect)){
		seterror("ig_ip_crop","crop rect is empty");
		return NULL;		
		}
	
	AT_DIMENSION width=0, height=0;
	UINT bitsPerPixel;
	AT_ERRCOUNT nError = IG_image_dimensions_get(self->m_hIGear,&width,&height,&bitsPerPixel);
	if(nError != 0)
		{
		seterror("ig_ip_crop::IG_image_dimensions_get","failure");
		return NULL;		
		}
	RECT rcImg = {0, 0, width, height};

	RECT rcInImg;
	if(!IntersectRect(&rcInImg, &rcImg, &rect)){
		seterror("ig_ip_crop","crop rect out of img");
		return NULL;		
		}

	AT_RECT atrect = {rcInImg.left, rcInImg.top, rcInImg.right, rcInImg.bottom};
	nError = IG_IP_crop(self->m_hIGear,&atrect);
	if(nError != 0)
		{
		seterror("ig_ip_crop","IG_IP_crop failed");
		return NULL;		
		}

	Py_INCREF(Py_None);
	return Py_None;	
	}



static char ig_display_image__doc__[] =
""
;
static PyObject* ig_display_image(PyImage *self, PyObject *args)
	{
	HDC hdc;
	if(!PyArg_ParseTuple(args, "l", &hdc))
		return NULL;

	if(!IG_image_is_valid(self->m_hIGear))
		{
		seterror("ig_display_image","Invalid image");
		return NULL;
		}

	AT_ERRCOUNT nError = 0;
	Py_BEGIN_ALLOW_THREADS
	nError = IG_display_image(self->m_hIGear,hdc);
	Py_END_ALLOW_THREADS
		
	if(nError != 0)
		{
		seterror("IG_display_image","failed");
		return NULL;		
		}

	Py_INCREF(Py_None);
	return Py_None;	
	}


// static char ig_image_delete__doc__[] =
// ""
// ;
// static PyObject* ig_image_delete(PyImage *self, PyObject *args)
// 	{
// 	if(!PyArg_ParseTuple(args, ""))
// 		return NULL;

// 	if(IG_image_is_valid(self->m_hIGear))
// 		{
// 		IG_image_delete(self->m_hIGear);
// 		self->m_hIGear = -1;
// 		}

// 	Py_INCREF(Py_None);
// 	return Py_None;	
// 	}
	

static char ig_color_promote__doc__[] =
""
;
static PyObject *ig_color_promote(PyImage *self, PyObject *args)
{
	int mode;
	if (!PyArg_ParseTuple(args, "i", &mode))
		return NULL;
	if (IG_IP_color_promote(self->m_hIGear, (AT_MODE) mode)) {
		PyErr_SetString(PyExc_ValueError, "bad image handle");
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static char ig_area_get__doc__[] =
""
;
static PyObject *ig_area_get(PyImage *self, PyObject *args)
{
	AT_RECT rect;
	AT_DIMENSION width, height;
	UINT bpp;
	PyObject *v;
	int len;

	rect.left = rect.top = rect.right = rect.bottom = 0;
	if (!PyArg_ParseTuple(args, "|(llll)", &rect.left, &rect.top, &rect.right, &rect.bottom))
		return NULL;
	if (IG_image_dimensions_get(self->m_hIGear, &width, &height, &bpp)) {
		PyErr_SetString(PyExc_ValueError, "bad image handle");
		return NULL;
	}
	if (rect.right > width || rect.right == 0)
		rect.right = width;
	if (rect.bottom > height || rect.bottom == 0)
		rect.bottom = height;
	if (rect.left >= rect.right)
		rect.left = rect.right - 1;
	if (rect.top >= rect.bottom)
		rect.top = rect.bottom - 1;
	len = (rect.right-rect.left)*(rect.bottom-rect.top);
	if (bpp > 8)
		len *= 3;
	v = PyString_FromStringAndSize(NULL, len);
	if (v == NULL)
		return NULL;
	if (IG_DIB_area_get(self->m_hIGear, &rect, (AT_PIXEL *) PyString_AS_STRING(v), IG_DIB_AREA_UNPACKED)) {
		PyErr_SetString(PyExc_RuntimeError, "area get failed");
		Py_DECREF(v);
		return NULL;
	}
	return v;
}

static char ig_image_export_ddb__doc__[] =
""
;
static PyObject *ig_image_export_ddb(PyImage *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	HBITMAP hBitmap;
	HPALETTE hPalette;
	if (IG_image_export_DDB(self->m_hIGear, &hBitmap, &hPalette)) {
		PyErr_SetString(PyExc_ValueError, "bad image handle");
		return NULL;
	}
	return Py_BuildValue("ii", hBitmap, hPalette);
}

static char ig_image_create_ddb__doc__[] =
""
;
static PyObject *ig_image_create_ddb(PyImage *self, PyObject *args)
{
	int nWidth, nHeight;
	if (!PyArg_ParseTuple(args, "(ii)", &nWidth,&nHeight))
		return NULL;
	HBITMAP hBitmap;
	HPALETTE hPalette;
	if (IG_image_create_DDB(self->m_hIGear, nWidth, nHeight, &hBitmap, &hPalette)) {
		PyErr_SetString(PyExc_ValueError, "bad image handle");
		return NULL;
	}
	return Py_BuildValue("ii", hBitmap, hPalette);
}


static char ig_ip_resize__doc__[] =
""
;
static PyObject *ig_ip_resize(PyImage *self, PyObject *args)
{
	int nWidth, nHeight;
	if (!PyArg_ParseTuple(args, "(ii)", &nWidth, &nHeight))
		return NULL;
	if (IG_IP_resize(self->m_hIGear, nWidth, nHeight, IG_INTERPOLATION_NONE)) {
		PyErr_SetString(PyExc_ValueError, "bad image handle");
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static char ig_ip_rotate_multiple_90__doc__[] =
""
;
static PyObject *ig_ip_rotate_multiple_90(PyImage *self, PyObject *args)
{
	int angle = 90; //counterclockwise
	if (!PyArg_ParseTuple(args, "|i", &angle))
		return NULL;
	AT_MODE nMult_90_Mode = IG_ROTATE_0;
	if(angle==90)
		nMult_90_Mode = IG_ROTATE_90;
	else if(angle==180)
		nMult_90_Mode = IG_ROTATE_180;
	else if(angle==270)
		nMult_90_Mode = IG_ROTATE_270;

	if (IG_IP_rotate_multiple_90(self->m_hIGear, nMult_90_Mode)) {
		PyErr_SetString(PyExc_ValueError, "bad image handle");
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;	
}

static char ig_is_transparent__doc__[] =
""
;
static PyObject *ig_is_transparent(PyImage *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	return Py_BuildValue("i", (self->m_transparent_index>=0?1:0));
}

static char ig_get_transparent_color__doc__[] =
""
;
static PyObject *ig_get_transparent_color(PyImage *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if(self->m_transparent_index<0)
		{
		PyErr_SetString(PyExc_ValueError, "image is not transparent");
		return NULL;
		}
	return Py_BuildValue("iii", int(self->m_rgb[0]), int(self->m_rgb[1]), int(self->m_rgb[2]));
}


PyMethodDef PyImage::methods[] = {
	{ "save_file", (PyCFunction)ig_save_file, METH_VARARGS, ig_save_file__doc__},
	{ "color_promote", (PyCFunction)ig_color_promote, METH_VARARGS,ig_color_promote__doc__},
	{ "area_get", (PyCFunction)ig_area_get, METH_VARARGS,ig_area_get__doc__},
	{ "image_dimensions_get",(PyCFunction)ig_image_dimensions_get, METH_VARARGS,ig_image_dimensions_get__doc__},
	{ "dimensions_get",(PyCFunction)ig_image_dimensions_get, METH_VARARGS,ig_image_dimensions_get__doc__},
	{ "display_transparent_set",(PyCFunction)ig_display_transparent_set,METH_VARARGS,ig_display_transparent_set__doc__},
	{ "device_rect_set",(PyCFunction)ig_device_rect_set,METH_VARARGS,ig_device_rect_set__doc__},
	{ "display_adjust_aspect",(PyCFunction)ig_display_adjust_aspect,METH_VARARGS,ig_display_adjust_aspect__doc__},
	{ "display_desktop_pattern_set",(PyCFunction)ig_display_desktop_pattern_set,METH_VARARGS,ig_display_desktop_pattern_set__doc__},
	{ "ip_crop", (PyCFunction)ig_ip_crop,METH_VARARGS,ig_ip_crop__doc__},
	{ "display_image", (PyCFunction)ig_display_image,METH_VARARGS,ig_display_image__doc__},
	{ "display", (PyCFunction)ig_display_image,METH_VARARGS,ig_display_image__doc__},
// 	{ "image_delete",(PyCFunction)ig_image_delete,METH_VARARGS,ig_image_delete__doc__},
// 	{ "delete",(PyCFunction)ig_image_delete,METH_VARARGS,ig_image_delete__doc__},
	{ "palette_entry_get",(PyCFunction)ig_palette_entry_get,METH_VARARGS,ig_palette_entry_get__doc__},
	{ "image_export_ddb",(PyCFunction)ig_image_export_ddb,METH_VARARGS,ig_image_export_ddb__doc__},
	{ "image_create_ddb",(PyCFunction)ig_image_create_ddb,METH_VARARGS,ig_image_create_ddb__doc__},
	{ "resize",(PyCFunction)ig_ip_resize,METH_VARARGS,ig_ip_resize__doc__},
	{ "rotate_multiple_90",(PyCFunction)ig_ip_rotate_multiple_90,METH_VARARGS,ig_ip_rotate_multiple_90__doc__},
	{ "is_transparent",(PyCFunction)ig_is_transparent,METH_VARARGS,ig_is_transparent__doc__},
	{ "get_transparent_color",(PyCFunction)ig_get_transparent_color,METH_VARARGS,ig_get_transparent_color__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		// sentinel
};

PyTypeObject PyImage::type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,					// ob_size
	"PyImage",			// tp_name
	sizeof(PyImage),		// tp_basicsize
	0,					// tp_itemsize
	// methods
	(destructor)PyImage::dealloc,	// tp_dealloc
	(printfunc)0,				// tp_print
	(getattrfunc)PyImage::getattr,// tp_getattr
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
	"PyImage Type" // Documentation string
	};


/////////////////////
// module

static struct PyMethodDef gear32sd_methods[] = {
	{"load", (PyCFunction)ig_load, METH_VARARGS, ig_load__doc__},
	{"load_file", (PyCFunction)ig_load_file, METH_VARARGS, ig_load_file__doc__},
#ifdef INCLUDE_GIF
	{ "load_gif", ig_load_gif, METH_VARARGS,ig_load_gif__doc__},
#endif
	{ "load_mem", (PyCFunction)ig_load_mem, METH_VARARGS,ig_load_mem__doc__},
	{ "error_check",(PyCFunction)ig_error_check,METH_VARARGS,ig_error_check__doc__},
	{ "error_get",(PyCFunction)ig_error_get,METH_VARARGS,ig_error_get__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};

static char gear32sd_module_documentation[] =
""
;

extern "C" __declspec(dllexport)
void initgear32sd()
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("gear32sd", gear32sd_methods,
		gear32sd_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("gear32sd.error");
	PyDict_SetItemString(d, "error", ErrorObject);
	PyDict_SetItemString(d, "IG_ASPECT_DEFAULT", PyInt_FromLong(IG_ASPECT_DEFAULT));
	PyDict_SetItemString(d, "IG_ASPECT_NONE", PyInt_FromLong(IG_ASPECT_NONE));


	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module gear32sd");
}
