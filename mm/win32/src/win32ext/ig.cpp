// CMIF_ADD
//
// kk@epsilon.com.gr
//

#include "stdafx.h"


#include "..\..\..\cmif\win32\\Accusoft\\Gear\\gear.h" // Accusoft DLL header.

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

static PyObject* ig_load_mem(PyObject *self, PyObject *args)
	{
	LPVOID pImage;
	DWORD dwSize;
	UINT nPageNum=1;
	UINT nTileNum=1;
	if(!PyArg_ParseTuple(args,"ll",&pImage,&dwSize))
		return NULL;
	if(pImage==0)
		RETURN_ERR("Invalid pointer to image");
	
	HIGEAR img;
	AT_ERRCOUNT nError=IG_load_mem(pImage,dwSize,nPageNum,nTileNum,&img);
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
	

BEGIN_PYMETHODDEF(ig)
	{ "load_file", ig_load_file, 1},
	{ "load_gif", ig_load_gif, 1},
	{ "load_mem", ig_load_mem, 1},
    { "image_dimensions_get",ig_image_dimensions_get, 1},
	{ "display_transparent_set",ig_display_transparent_set,1},
	{ "device_rect_set",ig_device_rect_set,1},
	{ "display_desktop_pattern_set",ig_display_desktop_pattern_set,1},
	{ "ip_crop", ig_ip_crop,1},
	{ "display_image", ig_display_image,1},
	{ "image_delete",ig_image_delete,1},
	{ "palette_entry_get",ig_palette_entry_get,1},
END_PYMETHODDEF()



DEFINE_PYMODULETYPE("Pyig",ig);



