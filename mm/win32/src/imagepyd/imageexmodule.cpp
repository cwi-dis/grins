#define AM_STANDARD

#include <windowsx.h>
//#include <mmsystem.h>
#include <afxwin.h>
#include "gear.h"
#include "cmifex.h"
//#include "img.h"


static PyObject *ImageExError;

PyIMPORT CWnd *GetWndPtr(PyObject *);


static HIGEAR hIGear=NULL;
//static HWND hWND;
static BOOL fl;




#ifdef __cplusplus
extern "C" {
#endif
//***************************
//Things to do:
//	- built a LinkList with the used windows so as to preserve MemoryManagement
//	- use in a more clever way to cover every case
//***************************


long reader(HWND hWND,LPSTR fname, float scale, RECT& rect)
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
		if((rcImageRect.bottom<scale*Height)||(rcImageRect.right<scale*Width))
			{
				rcImageRect.top = (rcImageRect.bottom-scale*Height)/2;
				rcImageRect.bottom = rcImageRect.top + scale*Height;
				rcImageRect.left = (rcImageRect.right-scale*Width)/2;
				rcImageRect.right = rcImageRect.left + scale*Width;
			}
	}
	
	IG_display_adjust_aspect(hBitmap,&rcImageRect,IG_ASPECT_DEFAULT);

	rect.top = rcImageRect.top;
	rect.bottom = rcImageRect.bottom;
	rect.left = rcImageRect.left;
	rect.right = rcImageRect.right;
	
   return((long)hBitmap);

}



void paintdll(HWND hWND,long bit,int r,int g,int b,float scale)
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

	  IG_display_desktop_pattern_set(hBitmap,NULL,NULL,&bcolor,TRUE);

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
			if((rcRefRect.bottom<scale*Height)||(rcRefRect.right<scale*Width))
			{
				rcRefRect.top = (rcRefRect.bottom-scale*Height)/2;
				rcRefRect.bottom = rcRefRect.top + scale*Height;
				rcRefRect.left = (rcRefRect.right-scale*Width)/2;
				rcRefRect.right = rcRefRect.left + scale*Width;
			}
		}
	  //IG_display_stretch_set(hBitmap,TRUE);
     //IG_display_fit_method(hBitmap,hWND,&rcRefRect,&nZoomLevel,IG_DISPLAY_FIT_TO_WINDOW);
	  IG_display_adjust_aspect(hBitmap,&rcRefRect,IG_ASPECT_DEFAULT);
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



//-----------------------------------------------------

static PyObject* py_ImageEx_PutImage(PyObject *self, PyObject *args)
{
	HWND hW;
	CWnd *obWnd;
	long bit;
	PyObject *testOb = Py_None;
	int r,g,b;
	float scale;
	
	if(!PyArg_ParseTuple(args, "Oliiif", &testOb, &bit, &r, &g, &b, &scale))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	obWnd = GetWndPtr(testOb);
	hW = obWnd->m_hWnd;

	paintdll(hW,bit,r,g,b,scale);
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

	//ASSERT(0);
	
	if(!PyArg_ParseTuple(args, "Osf", &testOb, &filename, &scale))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	obWnd = GetWndPtr(testOb);
	hW = obWnd->m_hWnd;
	bit=reader(hW,filename,scale,rect);
	
	tmp = Py_BuildValue("lllll",bit,rect.left,rect.top,rect.right,rect.bottom);

	return tmp;
}



static PyMethodDef ImageExMethods[] = 
{
	{ "PutImage", (PyCFunction)py_ImageEx_PutImage, 1},
    { "PrepareImage", (PyCFunction)py_ImageEx_Prepare, 1},
	{ NULL, NULL }
};

PyEXPORT 
void initimageex()
{
	PyObject *m, *d;
	m = Py_InitModule("imageex", ImageExMethods);
	d = PyModule_GetDict(m);
	ImageExError = PyString_FromString("ImageEx.error");
	PyDict_SetItemString(d, "error", ImageExError);
}

#ifdef __cplusplus
}
#endif
