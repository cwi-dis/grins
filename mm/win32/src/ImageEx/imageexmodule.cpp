#define AM_STANDARD

#include <windowsx.h>
#include <afxwin.h>
#include <afxext.h>
#include "gear.h" // Accusoft DLL header.
#include "Python.h"
#include "win32ui.h"

#define WIDTHBYTES(i)   ((i+31)/32*4)
#define BFT_BITMAP 0x4d42   /* 'BM' */
#define SIZEOF_BITMAPFILEHEADER_PACKED  (   \
    sizeof(WORD) +      /* bfType      */   \
    sizeof(DWORD) +     /* bfSize      */   \
    sizeof(WORD) +      /* bfReserved1 */   \
    sizeof(WORD) +      /* bfReserved2 */   \
    sizeof(DWORD))      /* bfOffBits   */
#define MAXREAD  32768

static PyObject *ImageExError;

PYW_EXPORT CWnd *GetWndPtr(PyObject *);

static HIGEAR hIGear=NULL;
//static HWND hWND;
static BOOL fl;

long reader(HWND hWND,LPSTR fname, float scale, RECT& rect, int center)
{
   AT_ERRCOUNT nError;
   //IG_image_delete(hIGear);
   nError=IG_load_file(fname,&hIGear);
   RECT r;
   
   ::GetClientRect(hWND,&r);
   
   if(nError!=0)
   {
	   TRACE("Error in Loading image %s\n", fname);
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

	IG_device_rect_set(hBitmap,&rcImageRect);
	
	rect.top = rcImageRect.top;
	rect.bottom = rcImageRect.bottom;
	rect.left = rcImageRect.left;
	rect.right = rcImageRect.right;
	
   return((long)hBitmap);

}



void paintdll(HWND hWND,long bit,int r,int g,int b,float scale, int center)
{
	//PAINTSTRUCT ps;
	HDC dc=GetDC(hWND);
	
	//dc=BeginPaint(hWND, &ps); 
       
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
   
   ReleaseDC(hWND,dc);
   
   //EndPaint(hWND, &ps); 
    
   //return 0L;
}


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
	HWND hW;
	CWnd *obWnd;
	long bit;
	PyObject *testOb = Py_None;
	int r,g,b,center=0;
	float scale;
	
	if(!PyArg_ParseTuple(args, "Oliiifi", &testOb, &bit, &r, &g, &b, &scale, &center))
		return NULL;
	
	obWnd = GetWndPtr(testOb);
	hW = obWnd->m_hWnd;

	paintdll(hW,bit,r,g,b,scale,center);
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
	bit=reader(hW,filename,scale,rect,center);
	
	tmp = Py_BuildValue("lllll",bit,rect.left,rect.top,rect.right,rect.bottom);

	return tmp;
}



static PyObject* py_ImageEx_Destroy(PyObject *self, PyObject *args)
{
	long bit;
		
	if(!PyArg_ParseTuple(args, "l", &bit))
		return NULL;

	destroyimage(bit);
	
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

	nError=IG_load_file(filename,&bit);
   
    if(nError!=0)
    {
	    Py_INCREF(Py_None);
		return Py_None;
    }
	
	AT_DIMENSION Width,Height;
	UINT BitsPerPixel;
	
	IG_image_dimensions_get (bit, &Width, &Height,&BitsPerPixel);
	
	if(IG_image_is_valid(bit))
		  IG_image_delete(bit);

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
	
	IG_device_rect_get(bit,&rcImageRect);	

	tmp = Py_BuildValue("llll", rcImageRect.left, rcImageRect.top, rcImageRect.right, rcImageRect.bottom);

	return tmp;
}


static PyMethodDef ImageExMethods[] = 
{
	{ "PutImage", (PyCFunction)py_ImageEx_PutImage, 1},
    { "PrepareImage", (PyCFunction)py_ImageEx_Prepare, 1},
	{ "Destroy", (PyCFunction)py_ImageEx_Destroy, 1},
	{ "SizeOfImage", (PyCFunction)py_ImageEx_SizeOfImage, 1},
	{ "ImageRect", (PyCFunction)py_ImageEx_ImageRect, 1},
	{ NULL, NULL }
};

extern "C" __declspec(dllexport) 
void initimageex()
{
	PyObject *m, *d;
	m = Py_InitModule("imageex", ImageExMethods);
	d = PyModule_GetDict(m);
	ImageExError = PyString_FromString("ImageEx.error");
	PyDict_SetItemString(d, "error", ImageExError);
}

