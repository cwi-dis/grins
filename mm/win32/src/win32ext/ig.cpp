// CMIF_ADD
//
// kk@epsilon.com.gr
//

// Define this for GIF support
#define INCLUDE_GIF

#include "stdafx.h"


#include "..\..\..\cmif\win32\Accusoft\Gear\gear.h" // Accusoft DLL header.

#pragma comment (lib,"d:\\ufs\\mm\\cmif\\win32\\Accusoft\\Gear\\Gear32sd.lib")

// Gif convertion
#include "igif.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(ig);
IMPLEMENT_PYMODULECLASS(ig,Getig,"Accusoft IGear Module Wrapper Object");


static PyObject* ig_load_file(PyObject *self, PyObject *args)
	{
	char *filename;
	if(!PyArg_ParseTuple(args,"s",&filename))
		return NULL;
	HIGEAR img;
	GUI_BGN_SAVE;
	AT_ERRCOUNT nError=IG_load_file(filename,&img);
	GUI_END_SAVE;
	if(nError!=0) img=-1;
	return Py_BuildValue("l",img);
	}

static PyObject* ig_error_check(PyObject *self, PyObject *args)
	{
	if(!PyArg_ParseTuple(args,""))
		return NULL;
	GUI_BGN_SAVE;
	AT_ERRCOUNT nError=IG_error_check();
	GUI_END_SAVE;
	return Py_BuildValue("l",(long)nError);
	}

static PyObject* ig_error_get(PyObject *self, PyObject *args)
	{
	  INT index;
	  AT_ERRCODE code;
	if(!PyArg_ParseTuple(args,"i", &index))
		return NULL;
	GUI_BGN_SAVE;
	IG_error_get(index,NULL,0,NULL,&code,NULL,NULL);
	GUI_END_SAVE;
	return Py_BuildValue("l",(long)code);
	}

#ifdef INCLUDE_GIF
static PyObject* ig_load_gif(PyObject *self, PyObject *args)
	{
	char *filename;
	if(!PyArg_ParseTuple(args,"s",&filename))
		return NULL;
	HIGEAR img=-1;
	int transp=-1,rgb[3]={255,255,255};
	GifConverter gc;
	GUI_BGN_SAVE;
	if(gc.LoadGif(filename))
		{
		transp=gc.m_transparent;
		for(int i=0;i<3;i++)rgb[i]=gc.m_tc[i];
		AT_ERRCOUNT nError=IG_load_mem(gc.m_pBmpBuffer,gc.m_dwSize,1,1,&img);
		if(nError!=0) img=-1;
		}
	GUI_END_SAVE;
	return Py_BuildValue("li(iii)",img,transp,rgb[0],rgb[1],rgb[2]);
	}
#endif

static PyObject* ig_load_mem(PyObject *self, PyObject *args)
	{
	char *pImage;
	int dwSize;
	int nPageNum=1;
	int nTileNum=1;
	if(!PyArg_ParseTuple(args,"s#|ll",&pImage,&dwSize,&nPageNum,&nTileNum))
		return NULL;
	if(pImage==0)
		RETURN_ERR("Invalid pointer to image");
	
	HIGEAR img;
	AT_ERRCOUNT nError=IG_load_mem((LPVOID)pImage,(DWORD)dwSize,(UINT)nPageNum,(UINT)nTileNum,&img);
	if(nError!=0) img=-1;
	return Py_BuildValue("l",img);
	}

static PyObject* ig_image_dimensions_get(PyObject *self, PyObject *args)
	{
	HIGEAR img;
	if(!PyArg_ParseTuple(args, "l", &img))
		return NULL;

	if(!IG_image_is_valid(img))
		RETURN_ERR("Invalid image");

	AT_DIMENSION Width=0,Height=0;
	UINT BitsPerPixel;
	IG_image_dimensions_get(img,&Width,&Height,&BitsPerPixel);

	return Py_BuildValue("lll",Width,Height,BitsPerPixel);
	}

static PyObject* ig_display_transparent_set(PyObject *self, PyObject *args)
	{
	HIGEAR img;
	int r,g,b;	
	BOOL enable;
	if(!PyArg_ParseTuple(args, "l(iii)i", &img,&r,&g,&b,&enable))
		return NULL;

	if(!IG_image_is_valid(img))
		RETURN_ERR("Invalid image");

	AT_RGB rgb={r,g,b};
	AT_ERRCOUNT nError=IG_display_transparent_set(img,&rgb,enable);
	if(nError!=0)
		RETURN_ERR("IG_display_transparent_set failed");

	RETURN_NONE;
	}

static PyObject* ig_palette_entry_get(PyObject *self,PyObject *args)
	{
	HIGEAR img;
	UINT ix;	
	if(!PyArg_ParseTuple(args, "li", &img,&ix))
		return NULL;

	if(!IG_image_is_valid(img))
		RETURN_ERR("Invalid image");

	AT_RGB rgb;
	AT_ERRCOUNT nError=IG_palette_entry_get(img,&rgb,ix);
	if(nError!=0)
		RETURN_ERR("IG_display_transparent_set failed");

	return Py_BuildValue("iii",rgb.r,rgb.g,rgb.b);
	}



static PyObject* ig_device_rect_set(PyObject *self, PyObject *args)
	{
	HIGEAR img;
	AT_RECT rect;
	if (!PyArg_ParseTuple(args,"l(iiii)",&img,
						&rect.left, &rect.top,
						&rect.right, &rect.bottom))
		return NULL;

	if(!IG_image_is_valid(img))
		RETURN_ERR("Invalid image");

	IG_display_adjust_aspect(img,&rect,IG_ASPECT_DEFAULT);
	IG_device_rect_set(img,&rect);

	RETURN_NONE;
	}


static PyObject* ig_display_desktop_pattern_set(PyObject *self, PyObject *args)
	{
	HIGEAR img;
	BOOL bEnabled;
	AT_RGB fg={-1,-1,-1};
	AT_RGB bg={-1,-1,-1};
	if(!PyArg_ParseTuple(args, "ii|(iii)(iii)",&img,&bEnabled,&fg.r,&fg.g,&fg.b,&bg.r,&bg.g,&bg.b))
		return NULL;

	if(!IG_image_is_valid(img))
		RETURN_ERR("Invalid image");

	GUI_BGN_SAVE;
	IG_display_desktop_pattern_set(img,NULL,(fg.r>=0)?&fg:NULL,(bg.r>=0)?&bg:NULL,bEnabled!=0?TRUE:FALSE);
	GUI_END_SAVE;

	RETURN_NONE;
	}

static PyObject* ig_ip_crop(PyObject *self, PyObject *args)
	{
	HIGEAR img;
	AT_RECT rect;
	if (!PyArg_ParseTuple(args,"l(iiii)",&img,
						&rect.left, &rect.top,
						&rect.right, &rect.bottom))
		return NULL;

	if(!IG_image_is_valid(img))
		RETURN_ERR("Invalid image");

	AT_ERRCOUNT nError=IG_IP_crop(img,&rect);

	if(nError!=0)
		RETURN_ERR("IG_IP_crop failed");

	RETURN_NONE;
	}



static PyObject* ig_display_image(PyObject *self, PyObject *args)
	{
	HIGEAR img;
	HDC hdc;
	if(!PyArg_ParseTuple(args, "ll", &img,&hdc))
		return NULL;

	if(!IG_image_is_valid(img))
		RETURN_ERR("Invalid image");

	GUI_BGN_SAVE;
	IG_display_image(img,hdc);
	GUI_END_SAVE;

	RETURN_NONE;
	}


static PyObject* ig_image_delete(PyObject *self, PyObject *args)
	{
	HIGEAR img;
	if(!PyArg_ParseTuple(args, "l", &img))
		return NULL;

	if(IG_image_is_valid(img))
		IG_image_delete(img);

	RETURN_NONE;
	}
	

static PyObject *ig_area_get(PyObject *self, PyObject *args)
{
	long img;
	AT_RECT rect;
	AT_DIMENSION width, height;
	UINT bpp;
	PyObject *v;
	int len;

	if (!PyArg_ParseTuple(args, "l(llll)", &img, &rect.left, &rect.top, &rect.right, &rect.bottom))
		return NULL;
	if (IG_image_dimensions_get((HIGEAR) img, &width, &height, &bpp)) {
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
	if (IG_DIB_area_get((HIGEAR) img, &rect, (AT_PIXEL *) PyString_AS_STRING(v), IG_DIB_AREA_UNPACKED)) {
		PyErr_SetString(PyExc_RuntimeError, "area get failed");
		Py_DECREF(v);
		return NULL;
	}
	return v;
}
	

BEGIN_PYMETHODDEF(ig)
	{ "load_file", ig_load_file, 1},
#ifdef INCLUDE_GIF
	{ "load_gif", ig_load_gif, 1},
#endif
	{ "load_mem", ig_load_mem, 1},
	{ "area_get", ig_area_get, 1},
	{ "image_dimensions_get",ig_image_dimensions_get, 1},
	{ "display_transparent_set",ig_display_transparent_set,1},
	{ "device_rect_set",ig_device_rect_set,1},
	{ "display_desktop_pattern_set",ig_display_desktop_pattern_set,1},
	{ "ip_crop", ig_ip_crop,1},
	{ "display_image", ig_display_image,1},
	{ "image_delete",ig_image_delete,1},
	{ "palette_entry_get",ig_palette_entry_get,1},
	{"error_check",ig_error_check,1},
	{"error_get",ig_error_get,1},
END_PYMETHODDEF()



DEFINE_PYMODULETYPE("Pyig",ig);



