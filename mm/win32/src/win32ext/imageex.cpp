#include "stdafx.h"

#define AM_STANDARD

#include "..\\..\\Accusoft\\Gear\\gear.h" // Accusoft DLL header.

#pragma comment (lib,"Gear32sd.lib")


#include "moddef.h"
DECLARE_PYMODULECLASS(Imageex);
IMPLEMENT_PYMODULECLASS(Imageex,GetImageex,"Imageex Module Wrapper Object");

DEFINE_MODULEERROR(Imageex);

PYW_EXPORT CWnd *GetWndPtr(PyObject *);

static HIGEAR hIGear=NULL;
static BOOL fl;

long reader(HWND hWND,LPSTR fname, float scale, RECT& rect, int center, int transp)
{
   AT_ERRCOUNT nError;
   //IG_image_delete(hIGear);
   nError=IG_load_file(fname,&hIGear);
   RECT r;
   
   ::GetClientRect(hWND,&r);
   
   if(nError!=0)
   {
	   TRACE("Error in Loading image %s - The AccuSoft error code was %ld\n", fname, nError);
	   TRACE("  Gear reports last error as %ld\n", IG_error_check() );
	   AT_ERRCODE code;
	   IG_error_get(nError, NULL, 0, NULL, &code, NULL, NULL);
	   TRACE("  IG_error_get reports last error as %ld\n", code );
	   return 0;
   }

    //long x,y;
	AT_RECT rcImageRect;
	HIGEAR hBitmap =hIGear;
	AT_DIMENSION Width,Height;
	UINT BitsPerPixel;
	
	rcImageRect.top = r.top;
	rcImageRect.bottom = r.bottom;
	rcImageRect.left = r.left;
	rcImageRect.right = r.right;

	IG_image_dimensions_get (hBitmap, &Width, &Height,&BitsPerPixel);

	if(scale>0)
		{
			if (center==1)
			{
				rcImageRect.top = (long)((rcImageRect.bottom-scale*Height)/2);
				rcImageRect.bottom = (long)(rcImageRect.top + scale*Height);
				rcImageRect.left = (long)((rcImageRect.right-scale*Width)/2);
				rcImageRect.right = (long)(rcImageRect.left + scale*Width);
			}
			else
			{
				rcImageRect.top = 0;
				rcImageRect.bottom = (long)(rcImageRect.top + scale*Height);
				rcImageRect.left = 0;
				rcImageRect.right = (long)(rcImageRect.left + scale*Width);
			}
		}
	else
	{
		IG_display_adjust_aspect(hBitmap,&rcImageRect,IG_ASPECT_DEFAULT);
		if (center!=1)
		{
			rcImageRect.right = rcImageRect.right-rcImageRect.left;
			rcImageRect.bottom = rcImageRect.bottom-rcImageRect.top;
			rcImageRect.left = rcImageRect.top = 0;
		}
	}

	if(transp!=-1)
	{
		AT_RGB			rgbPaletteColor;
		IG_palette_entry_get ( hIGear, &rgbPaletteColor,  transp);
		IG_display_transparent_set ( hBitmap, &rgbPaletteColor, TRUE );
	}
	IG_device_rect_set(hBitmap,&rcImageRect);
	
	rect.top = rcImageRect.top;
	rect.bottom = rcImageRect.bottom;
	rect.left = rcImageRect.left;
	rect.right = rcImageRect.right;
	
   return((long)hBitmap);

}



void paintdll(HWND hWND,HDC dc,long bit,int r,int g,int b,float scale, int center)
{
	bool bRelease=false;
	if(dc==0)
		{
		dc=GetDC(hWND);
		bRelease=true;
		}
	
	CString str = "No file currently selected";
   
    RECT rect;
    
    AT_RECT rcRefRect;
	AT_RGB bcolor;//,fcolor;

	bcolor.r = r;
	bcolor.g = g;
	bcolor.b = b;
	
	//fcolor.r = 0;
	//fcolor.g = 0;
	//fcolor.b = 0;

    if (bit != 0)
     {
	  HIGEAR hBitmap =(HIGEAR) bit;

	  IG_display_desktop_pattern_set(hBitmap,NULL,NULL,NULL,FALSE);

	  GetClientRect(hWND,&rect);

      rcRefRect.right=rect.right;
	  rcRefRect.bottom=rect.bottom;
	  rcRefRect.top=rect.top;
	  rcRefRect.left=rect.left;

	  AT_DIMENSION Width,Height;
	  UINT BitsPerPixel;
	
	  IG_image_dimensions_get (hBitmap, &Width, &Height,&BitsPerPixel);

	  if(scale>0)
		{
			if (center==1)
			{
				rcRefRect.top = (long)((rcRefRect.bottom-scale*Height)/2);
				rcRefRect.bottom = (long)(rcRefRect.top + scale*Height);
				rcRefRect.left = (long)((rcRefRect.right-scale*Width)/2);
				rcRefRect.right = (long)(rcRefRect.left + scale*Width);
			}
			else
			{
				rcRefRect.top = 0;
				rcRefRect.bottom = (long)(rcRefRect.top + scale*Height);
				rcRefRect.left = 0;
				rcRefRect.right = (long)(rcRefRect.left + scale*Width);
			}
		}
	  else
		{
			IG_display_adjust_aspect(hBitmap,&rcRefRect,IG_ASPECT_DEFAULT);
			if (center!=1)
			{
				rcRefRect.right = rcRefRect.right-rcRefRect.left;
				rcRefRect.bottom = rcRefRect.bottom-rcRefRect.top;
				rcRefRect.left = rcRefRect.top = 0;
			}
		}
	  //IG_display_stretch_set(hBitmap,TRUE);
     //IG_display_fit_method(hBitmap,hWND,&rcRefRect,&nZoomLevel,IG_DISPLAY_FIT_TO_WINDOW);
	  IG_device_rect_set(hBitmap,&rcRefRect);
	  IG_display_image(hBitmap,dc);
	 
     }
   else 
   {
     DrawText(dc,str, -1, &rect, DT_SINGLELINE | DT_CENTER | DT_VCENTER);
	 fl=FALSE;
     
   }
   
   if(bRelease)
	   ReleaseDC(hWND,dc);
   
}

/* not used
void paintdll2(HDC dc,long bit)
{
	if (bit != 0)
     {
	  HIGEAR hBitmap =(HIGEAR) bit;

	  IG_display_desktop_pattern_set(hBitmap,NULL,NULL,NULL,FALSE);

	  IG_display_image(hBitmap,dc); 
     }
}*/

void destroyimage(long bit)
{
	if (bit != 0)
     {
	  HIGEAR hBitmap =(HIGEAR) bit;
	  if(IG_image_is_valid(hBitmap))
		  IG_image_delete(hBitmap);
     }
}



//-----------------------------------------------------

static PyObject* py_ImageEx_PutImage(PyObject *self, PyObject *args)
{
	long bit;
	PyObject *pPyWnd;
	int r,g,b,center=0;
	float scale;
	HDC hdc;

	if(!PyArg_ParseTuple(args, "Olliiifi", &pPyWnd,&hdc, &bit, &r, &g, &b, &scale, &center))
		return NULL;
	
	CWnd *pWnd = GetWndPtr(pPyWnd);
		if(!pWnd) RETURN_ERR("First arg must be a PyCWnd object");
	
	GUI_BGN_SAVE;
	paintdll(pWnd->m_hWnd,hdc,bit,r,g,b,scale,center);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;

}




static PyObject* py_ImageEx_Prepare(PyObject *self, PyObject *args)
{
	char *filename;
	HWND hW;
	CWnd *obWnd;
	long bit;
	PyObject *testOb = Py_None,*tmp;
	RECT rect;
	float scale;
	int center;
	int transp;

	//ASSERT(0);
	
	if(!PyArg_ParseTuple(args, "Osfii", &testOb, &filename, &scale, &center, &transp))
		return NULL;

	obWnd = GetWndPtr(testOb);
	hW = obWnd->m_hWnd;
	GUI_BGN_SAVE;
	bit=reader(hW,filename,scale,rect,center, transp);
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("lllll",bit,rect.left,rect.top,rect.right,rect.bottom);

	return tmp;
}



static PyObject* py_ImageEx_Destroy(PyObject *self, PyObject *args)
{
	long bit;
		
	if(!PyArg_ParseTuple(args, "l", &bit))
		return NULL;

	GUI_BGN_SAVE;
	destroyimage(bit);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_ImageEx_SizeOfImage(PyObject *self, PyObject *args)
{
	char *filename;
	PyObject *tmp = Py_None;
	HIGEAR bit=NULL;
	AT_ERRCOUNT nError;
    
	if(!PyArg_ParseTuple(args, "s", &filename))
		return NULL;

	BOOL ok = FALSE;
	AT_DIMENSION Width=0,Height=0;
	GUI_BGN_SAVE;
	nError=IG_load_file(filename,&bit);
  
    if(nError==0)
    {
		UINT BitsPerPixel;
	
		IG_image_dimensions_get (bit, &Width, &Height,&BitsPerPixel);
	
		if(IG_image_is_valid(bit))
			  IG_image_delete(bit);

	}
	GUI_END_SAVE;
	tmp = Py_BuildValue("ii", Width, Height);

	return tmp;
}


static PyObject* py_ImageEx_ImageRect(PyObject *self, PyObject *args)
{
	long k;
	PyObject *tmp = Py_None;
	HIGEAR bit=NULL;
	AT_RECT rcImageRect;
    
	if(!PyArg_ParseTuple(args, "l", &k))
		return NULL;

	bit = (HIGEAR)k;

	if(!IG_image_is_valid(bit))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	GUI_BGN_SAVE;
	IG_device_rect_get(bit,&rcImageRect);	
	GUI_END_SAVE;

	tmp = Py_BuildValue("llll", rcImageRect.left, rcImageRect.top, rcImageRect.right, rcImageRect.bottom);

	return tmp;
}

/* not used yet
static PyObject* py_ImageEx_CreateBitmap(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *hCWnd;
	RECT rc, cl;
	long im;
	
	if(!PyArg_ParseTuple(args, "Oliiii", &ob, &im, &rc.left, &rc.top, &rc.right, &rc.bottom))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	hCWnd = GetWndPtr( ob );

	GUI_BGN_SAVE;
	hCWnd->GetClientRect(&cl);
	
	HDC dc = GetDC(hCWnd->m_hWnd), cdc;
	HBITMAP comp_bitmap;

	cdc = CreateCompatibleDC(dc);

	comp_bitmap = CreateCompatibleBitmap(dc, cl.right, cl.bottom);
	
	HBITMAP pOld1 = (HBITMAP)SelectObject(cdc,comp_bitmap);
	
	paintdll2(cdc,im);
	
	BitBlt(dc,rc.left, rc.top, rc.right-rc.left, rc.bottom-rc.top, 
				cdc, rc.left, rc.top, SRCCOPY);

	ReleaseDC(hCWnd->m_hWnd,dc);
	DeleteDC(cdc);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}
*/


#ifdef __cplusplus
extern "C" {
#endif

BEGIN_PYMETHODDEF(Imageex)
	{ "PutImage", (PyCFunction)py_ImageEx_PutImage, 1},
    { "PrepareImage", (PyCFunction)py_ImageEx_Prepare, 1},
	{ "Destroy", (PyCFunction)py_ImageEx_Destroy, 1},
	{ "SizeOfImage", (PyCFunction)py_ImageEx_SizeOfImage, 1}, // original
	{ "ImageRect", (PyCFunction)py_ImageEx_ImageRect, 1}, // current
	//{ "CreateClip", (PyCFunction)py_ImageEx_CreateBitmap, 1},
END_PYMETHODDEF()


PY_INITMODULE(Imageex);


#ifdef __cplusplus
	}
#endif

DEFINE_PYMODULETYPE("PyImageex",Imageex);

