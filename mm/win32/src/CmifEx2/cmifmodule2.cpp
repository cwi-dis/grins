
#include <string.h>
#include <math.h>
#include "cmifex.h"
#include "Ezfont.h"
#include "MultiFileSel.h"

static PyObject *CmifEx2Error;
static PyObject *CallbackMap = NULL;


PYW_EXPORT CWnd *GetWndPtr(PyObject *);
static char cmifClass[100]="";
static WNDPROC		orgProc;
static BOOL flag=FALSE;

static HFONT EzCreateFont (HDC hdc, char * szFaceName, int iDeciPtHeight,
                    int iDeciPtWidth, int iAttributes, BOOL fLogRes)
{
	FLOAT      cxDpi, cyDpi ;
	HFONT      hFont ;
	LOGFONT    lf ;
	POINT      pt ;
	TEXTMETRIC tm ;

	SaveDC (hdc) ;

	SetGraphicsMode (hdc, GM_ADVANCED) ;
	ModifyWorldTransform (hdc, NULL, MWT_IDENTITY) ;
	SetViewportOrgEx (hdc, 0, 0, NULL) ;
	SetWindowOrgEx   (hdc, 0, 0, NULL) ;

	if (fLogRes)
	{
		cxDpi = (FLOAT) GetDeviceCaps (hdc, LOGPIXELSX) ;
		cyDpi = (FLOAT) GetDeviceCaps (hdc, LOGPIXELSY) ;
	}
	else
	{
		cxDpi = (FLOAT) (25.4 * GetDeviceCaps (hdc, HORZRES) /
							GetDeviceCaps (hdc, HORZSIZE)) ;

		cyDpi = (FLOAT) (25.4 * GetDeviceCaps (hdc, VERTRES) /
							GetDeviceCaps (hdc, VERTSIZE)) ;
	}

	pt.x = (int) (iDeciPtWidth  * cxDpi / 72) ;
	pt.y = (int) (iDeciPtHeight * cyDpi / 72) ;

	DPtoLP (hdc, &pt, 1) ;

	lf.lfHeight         = - (int) (fabs ((double)pt.y) / 10.0 + 0.5) ;
	lf.lfWidth          = 0 ;
	lf.lfEscapement     = 0 ;
	lf.lfOrientation    = 0 ;
	lf.lfWeight         = iAttributes & EZ_ATTR_BOLD      ? 700 : 0 ;
	lf.lfItalic         = iAttributes & EZ_ATTR_ITALIC    ?   1 : 0 ;
	lf.lfUnderline      = iAttributes & EZ_ATTR_UNDERLINE ?   1 : 0 ;
	lf.lfStrikeOut      = iAttributes & EZ_ATTR_STRIKEOUT ?   1 : 0 ;
	lf.lfCharSet        = GREEK_CHARSET;
	lf.lfOutPrecision   = 0 ;
	lf.lfClipPrecision  = 0 ;
	lf.lfQuality        = 0 ;
	lf.lfPitchAndFamily = 0 ;

	strcpy (lf.lfFaceName, szFaceName) ;

	hFont = CreateFontIndirect (&lf) ;

	if (iDeciPtWidth != 0)
	{
		hFont = (HFONT) SelectObject (hdc, hFont) ;

		GetTextMetrics (hdc, &tm) ;

		DeleteObject (SelectObject (hdc, hFont)) ;

		lf.lfWidth = (int) (tm.tmAveCharWidth *
								fabs ((double)pt.x) / fabs ((double)pt.y) + 0.5) ;

		hFont = CreateFontIndirect (&lf) ;
	}

	RestoreDC (hdc, -1) ;

	return hFont ;
}



#ifdef __cplusplus
extern "C" {
#endif

void CmifEx2ErrorFunc(char *str);



static PyObject* py_example_CreateFileOpenDlg(PyObject *self, PyObject *args)
{
	PyObject *testOb = Py_None, *ob = Py_None;
	//PyCWnd *testWnd;
	char *title, *fname, *fltr;
	char filename[256];
	char filter[512];
	
	if(!PyArg_ParseTuple(args, "sss", &title, &fname, &fltr))
		return NULL;

	strcpy(filename, fname);
	strcpy(filter, fltr);
	CFileDialog Dlg(TRUE, NULL, filename, OFN_HIDEREADONLY|OFN_FILEMUSTEXIST, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = (LPCTSTR)title;
	GUI_BGN_SAVE;
	int ret = Dlg.DoModal();
	GUI_END_SAVE;

	if (ret == IDOK)
	{
		testOb = Py_BuildValue("iss", 1, (LPCTSTR)Dlg.m_ofn.lpstrFile, (LPCTSTR)Dlg.m_ofn.lpstrDefExt);
		return testOb;	
	}
	else
	{
		testOb = Py_BuildValue("iss", 0, " ", " ");
		return testOb;
	}
	
}


static PyObject* py_example_CreateFileSaveDlg(PyObject *self, PyObject *args)
{
	PyObject *testOb = Py_None, *ob = Py_None;
	//PyCWnd *testWnd;
	char *title, *fname, *fltr;
	char filename[256];
	char filter[512];
	
	if(!PyArg_ParseTuple(args, "sss", &title, &fname, &fltr))
		return NULL;

	strcpy(filename, fname);
	strcpy(filter, fltr);
	CFileDialog Dlg(FALSE, NULL, filename, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = (LPCTSTR)title;
	GUI_BGN_SAVE;
	int ret = Dlg.DoModal();
	GUI_END_SAVE;

	if (ret == IDOK)
	{
		if (Dlg.m_ofn.nFileExtension)
			testOb = Py_BuildValue("isl", 1, (LPCTSTR)Dlg.m_ofn.lpstrFile, (long)Dlg.m_ofn.nFileExtension);
		else
			testOb = Py_BuildValue("isl", 1, (LPCTSTR)Dlg.m_ofn.lpstrFile, (long)-1);
		return testOb;	
	}
	else
	{
		testOb = Py_BuildValue("isl", 0, " ", (long)-1);
		return testOb;
	}
	
}



static PyObject* py_example_MultiFileOpenDlg(PyObject *self, PyObject *args)
{
	PyObject *testOb = Py_None;
	char *title, *fname, *fltr;
	char filename[256];
	char filter[512];
	
	if(!PyArg_ParseTuple(args,"sss",&title,&fname,&fltr))
		return NULL;
	/*
	MultiFileSelector fs(title,fname,fltr);
	
	if(fs.Open())
		{
		testOb = Py_BuildValue("iss",1,fs.toString()," ");
		return testOb;	
		}
	else
		{
		testOb = Py_BuildValue("iss", 0, " ", " ");
		return testOb;
		}
	*/
	strcpy(filename, fname);
	strcpy(filter,fltr);
	CFileDialog Dlg(TRUE, NULL,filename, OFN_HIDEREADONLY|OFN_FILEMUSTEXIST|OFN_ALLOWMULTISELECT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = (LPCTSTR)title;
	GUI_BGN_SAVE;
	int ret = Dlg.DoModal();
	GUI_END_SAVE;

	if (ret == IDOK)
	{
		long count = 0;
		BOOL flag = TRUE;
        char temp[256];
		CString allfiles, dir, file;
        //while(flag)
		//{
		//   if (Dlg.m_ofn.lpstrFile[count]!=0)
		//	   temp[count] = Dlg.m_ofn.lpstrFile[count];
		//   else 
		//   {
		//	   temp[count] = Dlg.m_ofn.lpstrFile[count];
		//	   flag = FALSE;
		//   }
		//   count++;
		//}
        		
		count = Dlg.m_ofn.nFileOffset;
		strncpy(temp,(LPCTSTR)Dlg.m_ofn.lpstrFile,count); 
		temp[count] = 0;
		dir = temp;
		if (dir.ReverseFind('\\')== dir.GetLength()-1)
			dir = dir.Left(dir.GetLength()-1);
		//flag = TRUE;
		int count2 = 0;
		
		if (Dlg.m_ofn.lpstrFile[count] == 0)
		       flag = FALSE;
        
		while (flag)
		{
		   if (Dlg.m_ofn.lpstrFile[count]!=0)
			   temp[count2] = Dlg.m_ofn.lpstrFile[count];
		   else 
		   {
			   temp[count2] = '\0';
			   count2 = -1;
			   file = dir + "\\" + temp;
			   allfiles += file + ";";
			   if (Dlg.m_ofn.lpstrFile[count+1] == 0)
				   flag = FALSE;
		   }
		   count++;
		   count2++;
		}
		
		testOb = Py_BuildValue("iss", 1,(LPCTSTR) allfiles, (LPCTSTR)Dlg.m_ofn.lpstrDefExt);
		return testOb;	
	}
	else
	{
		testOb = Py_BuildValue("iss", 0, " ", " ");
		return testOb;
	}
	
}




static PyObject* py_example_CreateButton(PyObject *self, PyObject *args)
{
	char *wndName,*kind,*justify;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;
	
	
	if(!PyArg_ParseTuple(args, "sOiiii(ss)", &wndName, &ob, &x, &y, &nWidth, &nHeight, &kind, &justify))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	style = WS_CHILD | WS_CLIPSIBLINGS | WS_VISIBLE | BS_NOTIFY;

	if ((strcmp(kind,"b")==0)||(strcmp(kind,"p")==0))
			style = style | BS_PUSHBUTTON;

	if (strcmp(kind,"r")==0)
			style = style | BS_RADIOBUTTON;

	if (strcmp(kind,"t")==0)
			style = style | BS_AUTOCHECKBOX;

	if(strcmp(justify,"left")==0)
			style = style | BS_LEFTTEXT;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						"BUTTON", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}
			
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}





static PyObject* py_example_CreateStatic(PyObject *self, PyObject *args)
{
	char *wndName,*justify;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiiis", &wndName, &ob, &x, &y, &nWidth, &nHeight, &justify))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	style = WS_CHILD | WS_CLIPSIBLINGS|WS_VISIBLE;

	if(strcmp(justify,"left")==0)
			style = style | SS_LEFT;

	if(strcmp(justify,"right")==0)
			style = style | SS_RIGHT;

	if(strcmp(justify,"center")==0)
			style = style | SS_CENTER;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						"STATIC", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateStatic OK!\n");
	else
	{
		TRACE("CmifEx CreateStatic FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
			
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}


static PyObject* py_example_CreateRCheckbox(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	
	style = WS_CHILD | WS_CLIPSIBLINGS|WS_VISIBLE|BS_CHECKBOX|
			BS_NOTIFY;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						"BUTTON", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateLCheckbox(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	
	style = WS_CHILD | WS_CLIPSIBLINGS|WS_VISIBLE|BS_CHECKBOX|
			BS_LEFTTEXT|BS_RIGHT|BS_NOTIFY;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						"BUTTON", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateRRadioButton(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	
	style = WS_CHILD | WS_CLIPSIBLINGS|WS_VISIBLE|BS_RADIOBUTTON|
			BS_NOTIFY;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						"BUTTON", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateLRadioButton(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	
	style = WS_CHILD | WS_CLIPSIBLINGS|WS_VISIBLE|BS_RADIOBUTTON|
			BS_LEFTTEXT|BS_RIGHT|BS_NOTIFY;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						"BUTTON", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateGroup(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	
	style = WS_CHILD|WS_CLIPSIBLINGS|WS_VISIBLE|BS_GROUPBOX;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_TRANSPARENT,
						"BUTTON", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}






static PyObject* py_example_CreateSeparator(PyObject *self, PyObject *args)
{
	char *wndName = NULL;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100, vertical;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "Oiiiii", &ob, &x, &y, &nWidth, &nHeight, &vertical))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
	
	if(vertical)
		nWidth = 5;
	else nHeight = 5;
	
	style = WS_CHILD|WS_CLIPSIBLINGS|WS_VISIBLE|BS_GROUPBOX;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_TRANSPARENT,
						"BUTTON", NULL,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;

	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}






static PyObject* py_example_CreateSEdit(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100, editable;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight, &editable))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );

	style = WS_CHILD|WS_CLIPSIBLINGS|WS_VISIBLE|WS_BORDER|
			ES_AUTOHSCROLL;


	if (strcmp(wndName," ")==0) wndName = NULL;	
		
	
	if(editable==0)
		style = style | ES_READONLY;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_CLIENTEDGE,
						"EDIT", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateEdit OK!\n");
	else
	{
		TRACE("CmifEx CreateEdit FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateMEdit(PyObject *self, PyObject *args)
{
	char *wndName = NULL;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100, editable;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight, &editable))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
	
	style = WS_CHILD|WS_CLIPSIBLINGS|WS_VISIBLE|WS_BORDER|
				WS_VSCROLL|ES_AUTOVSCROLL|ES_MULTILINE|ES_WANTRETURN;

	if (strcmp(wndName," ")==0) wndName = NULL;	
	
	if(editable==0)
		style = style | ES_READONLY;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_CLIENTEDGE,
						"EDIT", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}



static PyObject* py_example_CreateListbox(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100,sort=0;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight, &sort))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	
	style = WS_CHILD|WS_CLIPSIBLINGS|WS_VISIBLE|WS_BORDER|
			WS_VSCROLL|WS_HSCROLL;

	if(sort==1)
		style = style | LBS_SORT;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_CLIENTEDGE,
						"LISTBOX", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateCombobox(PyObject *self, PyObject *args)
{
	char *wndName,*drop;
	PyObject *testOb = Py_None, *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100,sort=0, readonly=0;
	DWORD style;
	
	if(!PyArg_ParseTuple(args, "sOiiii(isi)", &wndName, &ob, &x, &y, &nWidth, &nHeight, &sort, &drop, &readonly))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	
	style = WS_CHILD |WS_CLIPSIBLINGS | WS_VISIBLE | WS_BORDER |
			WS_VSCROLL | WS_HSCROLL | CBS_AUTOHSCROLL;

	if(sort==1)
		style = style | CBS_SORT;

	if(strcmp(drop,"dr")==0)
		if(readonly==1)
			style = style | CBS_DROPDOWNLIST;
		else
			style = style | CBS_DROPDOWN;
	else
		style = style | CBS_SIMPLE;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_TRANSPARENT,
						"COMBOBOX", wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateButton OK!\n");
	else
	{
		TRACE("CmifEx CreateButton FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateSlider(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100,vertical;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight, &vertical))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	style = WS_CHILD | WS_CLIPSIBLINGS |WS_VISIBLE | 
			TBS_AUTOTICKS | TBS_ENABLESELRANGE;

	if (vertical)
		style = style | TBS_VERT | TBS_BOTH;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						TRACKBAR_CLASS, wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateSlider OK!\n");
	else
	{
		TRACE("CmifEx CreateSlider FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	SendMessage(newWnd->m_hWnd, TBM_SETRANGE, 
        (WPARAM) TRUE,                   
        (LPARAM) MAKELONG(0, 0));
	
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}



static PyObject* py_example_CreateVSlider(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	PyCWnd *testWnd;
	int x=150, y=150, nWidth=100, nHeight=100;
	DWORD style;

	
	if(!PyArg_ParseTuple(args, "sOiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s, X: %d, Y: %d, W: %d, H: %d\n", parentWnd->m_hWnd, wndName, x, y, nWidth, nHeight );
		
	style = WS_CHILD | WS_CLIPSIBLINGS|WS_VISIBLE |
			TBS_AUTOTICKS | TBS_ENABLESELRANGE |TBS_VERT | TBS_BOTH;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(WS_EX_CONTROLPARENT,
						TRACKBAR_CLASS, wndName,
						style,
						x, y, nWidth, nHeight,
						parentWnd->m_hWnd,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateSlider OK!\n");
	else
	{
		TRACE("CmifEx CreateSlider FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	
	SendMessage(newWnd->m_hWnd, TBM_SETRANGE, 
        (WPARAM) TRUE,                   
        (LPARAM) MAKELONG(0, 0));

	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}


static LRESULT CALLBACK MyWndProc (HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam)
{

	switch (iMsg)
	{
		case WM_CLOSE:
			if (!flag)
			{
				ShowWindow(hwnd, SW_HIDE);
			}
			//flag = FALSE;
			//MessageBox(hwnd, "Window Hidden", "Test", MB_OK);
			return 0;	
		case WM_DESTROY:
			if (!flag)
			{
				return CallWindowProc(orgProc, hwnd, iMsg, wParam, lParam) ;
			}
			//flag = FALSE;
			//MessageBox(hwnd, "Window Hidden", "Test", MB_OK);
			return 0;	
	}
	return CallWindowProc(orgProc, hwnd, iMsg, wParam, lParam) ;
}

static PyObject* py_example_CreateDialogbox(PyObject *self, PyObject *args)
{
	char *wndName = NULL;
	PyObject *ob = Py_None;
	CWnd *parentWnd = NULL,*newWnd = NULL;
	HWND parent = NULL;
	PyCWnd *testWnd;
	int x, y, nWidth, nHeight =0;
	int visible = 0, grab = 0;
	//int item;
	DWORD style = 0, stylex = WS_EX_DLGMODALFRAME;
	//HMENU menu;
	CString str;

	
	if(!PyArg_ParseTuple(args, "sOiiiiii", &wndName, &ob, &x, &y, &nWidth, &nHeight, &visible, &grab))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	if(parentWnd) 
	{
		parent = parentWnd->m_hWnd;
		style = WS_POPUP;
	}
	else parent = NULL;
		
	if (grab>0) stylex = stylex|WS_EX_TOPMOST;
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), GetSysColorBrush(COLOR_BTNFACE)));
	
	if(visible==1)
		style = style|WS_CLIPCHILDREN|WS_VISIBLE|WS_SYSMENU|
				WS_CAPTION|WS_OVERLAPPED;
	else
		style = style|WS_CLIPCHILDREN|WS_CAPTION|WS_SYSMENU|
				WS_OVERLAPPED;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(stylex,
						cmifClass, wndName,
						style,
						CW_USEDEFAULT, y, nWidth, nHeight,
						parent,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateDialog OK!\n");
	else
	{
		TRACE("CmifEx CreateDialog FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	
	orgProc = (WNDPROC)SetWindowLong(newWnd->m_hWnd, GWL_WNDPROC, (LONG)MyWndProc);
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	return testWnd->GetGoodRet();
}




static PyObject* py_example_CreateContainerbox(PyObject *self, PyObject *args)
{
	PyObject *testOb = Py_None, *ob = Py_None;
	CWnd *parentWnd,*newWnd;
	HWND parent;
	PyCWnd *testWnd;
	int x=0, y=0, nWidth=0, nHeight=0,item=0;
	DWORD style;
	
	//ASSERT(0);
	
	if(!PyArg_ParseTuple(args, "Oiiii", &ob, &x, &y, &nWidth, &nHeight))
		return NULL;

	newWnd = new CWnd;
	parentWnd = GetWndPtr( ob );

	if(!parentWnd) 
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	TRACE("hWnd: %p, X: %d, Y: %d, W: %d, H: %d\n", parent, x, y, nWidth, nHeight );
		
	parent = parentWnd->m_hWnd;
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), GetSysColorBrush(COLOR_BTNFACE)));
	
	style = WS_CHILD|WS_CLIPCHILDREN|WS_OVERLAPPED|WS_VISIBLE;

	GUI_BGN_SAVE;
	BOOL ok = newWnd->CreateEx(0,
						cmifClass, NULL,
						style,
						x, y, nWidth, nHeight,
						parent,
						NULL);
	GUI_END_SAVE;
	if(ok)
		TRACE("CmifEx CreateDialog OK!\n");
	else
	{
		TRACE("CmifEx CreateDialog FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}




static PyObject* py_example_SetWindowCaption(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	char *str;
		
	if(!PyArg_ParseTuple(args, "Os", &ob, &str))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Name: %s", controlWnd->m_hWnd, str);

	//if (strcmp(str," ")==0) *str='\0';
		
	GUI_BGN_SAVE;
	controlWnd->SetWindowText((LPCTSTR)str);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_CheckButton(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int check;
	
	if(!PyArg_ParseTuple(args, "Oi", &ob, &check))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, check: %d,", controlWnd->m_hWnd, check );
		
	GUI_BGN_SAVE;
	if(check == 0) controlWnd->SendMessage(BM_SETCHECK, 0, 0);
	else controlWnd->SendMessage(BM_SETCHECK, 1, 0);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_CheckState(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int check;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd );
		
	GUI_BGN_SAVE;
	check = (int) controlWnd->SendMessage(BM_GETCHECK, 0, 0);
	GUI_END_SAVE;
	
	//if(!(::GetClassName(controlWnd->m_hWnd,(LPTSTR)classname,20)))
	//{
	//	Py_INCREF(Py_None);
	//	CmifEx2ErrorFunc("Cannot take the class name");
	//	return Py_None;
	//}
  
	//style = ::GetWindowLong(controlWnd->m_hWnd,GWL_STYLE);

	//CString tmp = classname;
	//tmp.MakeLower();
	//if (tmp.Find("button")>=0) 
	//	{
	//		if(BS_CHECKBOX & style) strcpy(classname, "CheckBox");
	//		if(BS_RADIOBUTTON & style) strcpy(classname, "RadioButton");
	//}

	return Py_BuildValue("i", check);
}



static PyObject* py_example_GetText(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	char *str = NULL;
	int length;
	CString cname;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	length = controlWnd->GetWindowTextLength();
	str = new char[length+1];

	controlWnd->GetWindowText(str,length+1);
	GUI_END_SAVE;
			
	tmp = Py_BuildValue("s", str);
	delete str;
	
	return tmp;
}




static PyObject* py_example_GetTextSize(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	char *str = NULL;
	int length;
	CString cname;
	//SIZE sz;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	length = controlWnd->GetWindowTextLength();
	str = new char[length+1];

	controlWnd->GetWindowText(str,length+1);
	GUI_END_SAVE;
			
	tmp = Py_BuildValue("s", str);
	delete str;
	
	return tmp;
}



static PyObject* py_example_SetFont(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	char *facename;
	int size;
	HFONT hfont;
			
	if(!PyArg_ParseTuple(args, "Osi", &ob, &facename, &size))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, FaceName: %s, Size: %d", controlWnd->m_hWnd, facename, size);
		
	GUI_BGN_SAVE;
	HDC dc = ::GetDC(controlWnd->m_hWnd);
	hfont=EzCreateFont(dc, facename, size*10, 0, 0, TRUE);
	controlWnd->SendMessage(WM_SETFONT, (UINT)hfont, MAKELPARAM(TRUE, 0));
	::ReleaseDC(controlWnd->m_hWnd,dc);
	GUI_END_SAVE;

	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_Changed(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	BOOL result;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);
		
	GUI_BGN_SAVE;
	result = controlWnd->SendMessage(EM_GETMODIFY, 0, 0);
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("i", (int) result);
	return tmp;
}



static PyObject* py_example_Cut(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);
		
	GUI_BGN_SAVE;
	controlWnd->SendMessage(WM_CUT, 0, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_Copy(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);
		
	GUI_BGN_SAVE;
	controlWnd->SendMessage(WM_COPY, 0, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_Clear(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);
		
	GUI_BGN_SAVE;
	controlWnd->SendMessage(WM_CLEAR, 0, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_Paste(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);
		
	GUI_BGN_SAVE;
	controlWnd->SendMessage(WM_PASTE, 0, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_Select(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int start,end;
		
	if(!PyArg_ParseTuple(args, "Oii", &ob, &start, &end))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, Start: %d, End: %d", controlWnd->m_hWnd, start, end);
		
	GUI_BGN_SAVE;
	controlWnd->SendMessage(EM_SETSEL, start, end);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_Replace(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	char *str;
		
	if(!PyArg_ParseTuple(args, "Os", &ob, &str))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, String: %s", controlWnd->m_hWnd, str);
		
	GUI_BGN_SAVE;
	controlWnd->SendMessage(EM_REPLACESEL, 0, (LPARAM)str);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_AddString(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	char *str;
	int index;
	UINT message;
	char clss[30];

	//ASSERT(0);
		
	if(!PyArg_ParseTuple(args, "Os", &ob, &str))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, String: %s", controlWnd->m_hWnd, str);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_ADDSTRING;
	else
		message = LB_ADDSTRING;
		
	GUI_BGN_SAVE;
	index = controlWnd->SendMessage(message, 0, (LPARAM)str);
	GUI_END_SAVE;

	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_DeleteString(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int index;
	UINT message;
	char clss[30];
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_GETCURSEL;
	else
		message = LB_GETCURSEL;

	index = controlWnd->SendMessage(message, 0, 0);

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_DELETESTRING;
	else
		message = LB_DELETESTRING;
		
	GUI_BGN_SAVE;
	if (index>=0) controlWnd->SendMessage(message, index, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_DeleteToPos(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int index;
	UINT message;
	char clss[30];
		
	if(!PyArg_ParseTuple(args, "Oi", &ob, &index))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_DELETESTRING;
	else
		message = LB_DELETESTRING;
		
	GUI_BGN_SAVE;
	if (index>=0) controlWnd->SendMessage(message, (UINT)index, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_ReplaceToPos(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int index;
	UINT message;
	char clss[30];
	char* str;
		
	if(!PyArg_ParseTuple(args, "Ois", &ob, &index, &str))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_DELETESTRING;
	else
		message = LB_DELETESTRING;
		
	if (index>=0) controlWnd->SendMessage(message, (UINT)index, 0);

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_INSERTSTRING;
	else
		message = LB_INSERTSTRING;
	
	GUI_BGN_SAVE;
	controlWnd->SendMessage(message, (UINT)index, (LPARAM)str);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_InsertToPos(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int index;
	UINT message;
	char clss[30];
	char* str;
		
	if(!PyArg_ParseTuple(args, "Ois", &ob, &index, &str))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_INSERTSTRING;
	else
		message = LB_INSERTSTRING;
	
	GUI_BGN_SAVE;
	if (index>=0) 
		controlWnd->SendMessage(message, (UINT)index, (LPARAM)str);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_Reset(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	UINT message;
	char clss[30];
			
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_RESETCONTENT;
	else
		message = LB_RESETCONTENT;
		
	GUI_BGN_SAVE;
	controlWnd->SendMessage(message, 0, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_GetString(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	int index,length;
	char *selection = NULL;
	UINT message;
	char clss[30];
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_GETCURSEL;
	else
		message = LB_GETCURSEL;

	GUI_BGN_SAVE;
	index = controlWnd->SendMessage(message, 0, 0);
	
	if (index>=0)
	{
		if(strcmp(clss,"ComboBox")==0) 
			message = CB_GETLBTEXTLEN;
		else
			message = LB_GETTEXTLEN;
		length = (int) controlWnd->SendMessage(message, index, 0);
		selection = new char[length+1];
		if(strcmp(clss,"ComboBox")==0) 
			message = CB_GETLBTEXT;
		else
			message = LB_GETTEXT;
		controlWnd->SendMessage(message, index, (LPARAM)selection);
	}
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("s", selection);
	delete selection;
	return tmp;
}



static PyObject* py_example_GetPos(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	int index;
	UINT message;
	char clss[30];
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_GETCURSEL;
	else
		message = LB_GETCURSEL;

	index = controlWnd->SendMessage(message, 0, 0);
	GUI_END_SAVE;
	
	if (index>=0)
	{
		tmp = Py_BuildValue("i", index);
		return tmp;
	}
	else
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
}



static PyObject* py_example_SetSelect(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int index;
	UINT message;
	char clss[30];
		
	if(!PyArg_ParseTuple(args, "Oi", &ob, &index))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	if(GetClassName(controlWnd->m_hWnd,clss,30)==0)
		strcpy(clss,"");

	if(strcmp(clss,"ComboBox")==0) 
		message = CB_SETCURSEL;
	else
		message = LB_SETCURSEL;

	GUI_BGN_SAVE;
	if (index>=0)
		controlWnd->SendMessage(message, (UINT)index, 0);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_SetRange(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int iMin, iMax;
		
	if(!PyArg_ParseTuple(args, "Oii", &ob, &iMin, &iMax))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	SendMessage(controlWnd->m_hWnd, TBM_SETRANGE, 
        (WPARAM) TRUE,                   
        (LPARAM) MAKELONG(iMin, iMax));

	SendMessage(controlWnd->m_hWnd, TBM_SETPOS, 
        (WPARAM) TRUE,                   
        (LPARAM) iMin);
			
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_SetPosition(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int iPos;
		
	if(!PyArg_ParseTuple(args, "Oi", &ob, &iPos))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	SendMessage(controlWnd->m_hWnd, TBM_SETPOS, 
        (WPARAM) TRUE,                   
        (LPARAM) iPos);
	GUI_END_SAVE;
			
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_SetSelection(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int iMin, iMax;
		
	if(!PyArg_ParseTuple(args, "Oii", &ob, &iMin, &iMax))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	SendMessage(controlWnd->m_hWnd, TBM_SETSEL, 
        (WPARAM) TRUE,                   
        (LPARAM) MAKELONG(iMin, iMax));

	SendMessage(controlWnd->m_hWnd, TBM_SETPOS, 
        (WPARAM) TRUE,                   
        (LPARAM) iMin);
	GUI_END_SAVE;
			
	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_GetRange(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	int iMin, iMax;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	iMin = SendMessage(controlWnd->m_hWnd, TBM_GETRANGEMIN, 0, 0);

	iMax = SendMessage(controlWnd->m_hWnd, TBM_GETRANGEMAX, 0, 0);
	GUI_END_SAVE;
			
	tmp = Py_BuildValue("ii", iMin, iMax);
	return tmp;
}



static PyObject* py_example_GetPosition(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	int iPos;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	iPos = SendMessage(controlWnd->m_hWnd, TBM_GETPOS, 0, 0);
	GUI_END_SAVE;
			
	tmp = Py_BuildValue("i", iPos);
	return tmp;
}



static PyObject* py_example_GetSelection(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	int iMin, iMax;
		
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	
	GUI_BGN_SAVE;
	iMin = SendMessage(controlWnd->m_hWnd, TBM_GETSELSTART, 0, 0);

	iMax = SendMessage(controlWnd->m_hWnd, TBM_GETSELEND, 0, 0);
	GUI_END_SAVE;
			
	tmp = Py_BuildValue("ii", iMin, iMax);
	return tmp;
}



static PyObject* py_example_CreateMenu(PyObject *self, PyObject *args)
{
	PyObject *tmp = Py_None;
	//CWnd *parentWnd;
	HMENU menu;
			
	if(!PyArg_ParseTuple(args, ""))
		return NULL;

	//parentWnd = GetWndPtr( ob );

	//TRACE("hWnd: %p", parentWnd->m_hWnd);

	GUI_BGN_SAVE;
	menu = CreateMenu();
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("l", (long) menu);
	return tmp;
}


static PyObject* py_example_GetMenu(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *parentWnd;
	HMENU menu;
	int menuid;
				
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", parentWnd->m_hWnd);

	GUI_BGN_SAVE;
	menu = (HMENU) ::GetMenu(parentWnd->m_hWnd);
	if(menu) menuid = ::GetMenuItemCount(menu)-1;
	else menuid = 0;

	::SetMenu(parentWnd->m_hWnd, menu);
	::DrawMenuBar(parentWnd->m_hWnd);

	GUI_END_SAVE;

	tmp = Py_BuildValue("li", (long) menu, menuid);
	return tmp;
}



static PyObject* py_example_SetMenu(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *parentWnd;
	HMENU menu;
	long lmenu;
			
	if(!PyArg_ParseTuple(args, "Ol", &ob, &lmenu))
		return NULL;

	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", parentWnd->m_hWnd);

	menu = (HMENU) lmenu;

	GUI_BGN_SAVE;
	::SetMenu(parentWnd->m_hWnd, menu);
	::DrawMenuBar(parentWnd->m_hWnd);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_FloatMenu(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *parentWnd;
	HMENU menu;
	long lmenu;
	POINT point;
	int menuid;
			
	if(!PyArg_ParseTuple(args, "Olii", &ob, &lmenu, &point.x, &point.y))
		return NULL;

	parentWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", parentWnd->m_hWnd);

	menu = (HMENU) lmenu;

	GUI_BGN_SAVE;
	menu = ::GetSubMenu(menu, 0);

	::ClientToScreen(parentWnd->m_hWnd, &point);

	menuid = ::TrackPopupMenu(menu, TPM_RETURNCMD|TPM_RIGHTBUTTON|TPM_LEFTBUTTON, point.x, point.y, 
					 0, parentWnd->m_hWnd, NULL);
	
	GUI_END_SAVE;
	tmp = Py_BuildValue("i", menuid);
	return tmp;
}

static PyObject* py_example_CheckMenuItem(PyObject *self, PyObject *args)
{
	//PyObject *ob = Py_None;
	//CWnd *parentWnd;
	HMENU menu;
	long lmenu;
	int pos,check;
	UINT flags = MF_BYPOSITION;
			
	if(!PyArg_ParseTuple(args, "lii", &lmenu, &pos, &check))
		return NULL;

	menu = (HMENU) lmenu;

	if (check==0)
		flags = flags | MF_UNCHECKED;
	else
		flags = flags | MF_CHECKED;

	::CheckMenuItem(menu,(UINT)pos,flags);
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_AppendMenu(PyObject *self, PyObject *args)
{
	//PyObject *ob = Py_None;
	//CWnd *parentWnd;
	HMENU menu;
	long lmenu;
	char *str;
	int id;
			
	if(!PyArg_ParseTuple(args, "lsi", &lmenu, &str, &id))
		return NULL;

	//parentWnd = GetWndPtr( ob );

	//TRACE("hWnd: %p", parentWnd->m_hWnd);

	menu = (HMENU) lmenu;

	GUI_BGN_SAVE;
	if(strcmp(str,"")==0) ::AppendMenu(menu, MF_SEPARATOR, 0, NULL);
	else
	{
		int id2 = ::GetMenuItemCount(menu)+1;
		int idbreak = (id2-1) % 25;
		if ((idbreak==0)&&(id2)!=1)
			if(id!=-1)
			::AppendMenu(menu, MF_STRING|MF_MENUBARBREAK, id, (LPCTSTR)str);
			else
			::AppendMenu(menu, MF_STRING|MF_MENUBARBREAK, id2, (LPCTSTR)str);
		else
			if(id!=-1)
			::AppendMenu(menu, MF_STRING, id, (LPCTSTR)str);
			else
			::AppendMenu(menu, MF_STRING, id2, (LPCTSTR)str);
	}
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_PopupAppendMenu(PyObject *self, PyObject *args)
{
	//PyObject *ob = Py_None;
	//CWnd *parentWnd;
	HMENU menu,submenu;
	long lmenu,smenu;
	char *str;
				
	if(!PyArg_ParseTuple(args, "lls", &lmenu, &smenu, &str))
		return NULL;

	//parentWnd = GetWndPtr( ob );

	//TRACE("hWnd: %p", parentWnd->m_hWnd);

	menu = (HMENU) lmenu;
	submenu = (HMENU) smenu;

	GUI_BGN_SAVE;
	int id = ::GetMenuItemCount(menu)+1;
	int idbreak = (id-1) % 25;

	if ((idbreak==0)&&(id)!=1)
		::AppendMenu(menu, MF_POPUP|MF_MENUBARBREAK, (UINT) submenu, (LPCTSTR)str);
	else
		::AppendMenu(menu, MF_POPUP, (UINT) submenu, (LPCTSTR)str);
	GUI_END_SAVE;
	

	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_InsertMenu(PyObject *self, PyObject *args)
{
	//PyObject *ob = Py_None;
	//CWnd *parentWnd;
	HMENU menu;
	long lmenu;
	char *str;
	int pos;
			
	if(!PyArg_ParseTuple(args, "lis", &lmenu, &pos, &str))
		return NULL;

	//parentWnd = GetWndPtr( ob );

	//TRACE("hWnd: %p", parentWnd->m_hWnd);

	menu = (HMENU) lmenu;

	GUI_BGN_SAVE;
	if(strcmp(str,"")==0) ::InsertMenu(menu,(UINT) pos, MF_SEPARATOR|MF_BYPOSITION, 0, NULL);
	else
	::InsertMenu(menu, (UINT) pos, MF_STRING|MF_BYPOSITION, ::GetMenuItemCount(menu)+1, (LPCTSTR)str);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_PopupInsertMenu(PyObject *self, PyObject *args)
{
	//PyObject *ob = Py_None;
	//CWnd *parentWnd;
	HMENU menu,submenu;
	long lmenu,smenu;
	char *str;
	int pos;
				
	if(!PyArg_ParseTuple(args, "llis", &lmenu, &smenu, &pos, &str))
		return NULL;

	//parentWnd = GetWndPtr( ob );

	//TRACE("hWnd: %p", parentWnd->m_hWnd);

	menu = (HMENU) lmenu;
	submenu = (HMENU) smenu;

	GUI_BGN_SAVE;
	::InsertMenu(menu,(UINT) pos, MF_POPUP|MF_BYPOSITION, (UINT) submenu, (LPCTSTR)str);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_DestroyMenu(PyObject *self, PyObject *args)
{
	HMENU menu;
	long menuid;
					
	if(!PyArg_ParseTuple(args, "l", &menuid))
		return NULL;

	menu = (HMENU) menuid;

	GUI_BGN_SAVE;
	if(menu!=NULL) DestroyMenu(menu);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_DeleteMenu(PyObject *self, PyObject *args)
{
	//PyObject *ob = Py_None;
	//CWnd *parentWnd;
	HMENU menu;
	long lmenu;
	//char *str;
	int pos;
			
	if(!PyArg_ParseTuple(args, "li", &lmenu, &pos))
		return NULL;

	//parentWnd = GetWndPtr( ob );

	//TRACE("hWnd: %p", parentWnd->m_hWnd);

	menu = (HMENU) lmenu;

	GUI_BGN_SAVE;
	::DeleteMenu(menu, pos, MF_BYPOSITION);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_DestroyWindow(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
			
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);
	GUI_BGN_SAVE;

	while (controlWnd->GetWindow(GW_CHILD)!=NULL) controlWnd->GetWindow(GW_CHILD)->DestroyWindow();
	
	controlWnd->DestroyWindow();
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_SetFlag(PyObject *self, PyObject *args)
{
	int x;
			
	if(!PyArg_ParseTuple(args, "i", &x))
		return NULL;

	if (x==1)
		flag = TRUE;
	else flag = FALSE;

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* py_example_ResizeWindow(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int w,h;
	WINDOWPLACEMENT wplc;
	//UINT show;
			
	if(!PyArg_ParseTuple(args, "Oii", &ob, &w, &h))
		return NULL;

	controlWnd = GetWndPtr( ob );

	wplc.length = sizeof(WINDOWPLACEMENT);

	TRACE("hWnd: %p", controlWnd->m_hWnd);

	GUI_BGN_SAVE;
	controlWnd->GetWindowPlacement(&wplc);
	//controlWnd->ShowWindow(SW_HIDE);
	wplc.showCmd = SW_HIDE; 
	wplc.rcNormalPosition.right = wplc.rcNormalPosition.left + w;
	wplc.rcNormalPosition.bottom = wplc.rcNormalPosition.top + h;
	controlWnd->SetWindowPlacement(&wplc);
	//controlWnd->ShowWindow(SW_HIDE);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_ResizeAllWindows(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd,*nextwin;
	int x1,y1,x2,y2,width,height;
	WINDOWPLACEMENT wplc;
			
	if(!PyArg_ParseTuple(args, "Oiiiiii", &ob, &x1, &y1, &x2, &y2, &width, &height))
		return NULL;

	controlWnd = GetWndPtr( ob );

	wplc.length = sizeof(WINDOWPLACEMENT);

	GUI_BGN_SAVE;
	nextwin  = controlWnd->GetWindow(GW_CHILD);

	while (nextwin!=NULL)
	{
		nextwin->GetWindowPlacement(&wplc);
		nextwin->ShowWindow(SW_HIDE);
		if ((wplc.rcNormalPosition.left == x1)&&(x1!=x2)) 
		{
			if(wplc.rcNormalPosition.right-wplc.rcNormalPosition.left>x2-x1)
				wplc.rcNormalPosition.right = x1; 
		}
		//wplc.rcNormalPosition.top += y;
		//wplc.rcNormalPosition.right+= x;
		//wplc.rcNormalPosition.bottom += y;
		nextwin->SetWindowPlacement(&wplc);
		nextwin->ShowWindow(SW_SHOW);
		nextwin  = nextwin->GetNextWindow();
	}
	
	GUI_END_SAVE;
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_GetStringLength(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	int length;
	char* str;
	HDC dc;
	SIZE size;
			
	if(!PyArg_ParseTuple(args, "Os", &ob, &str))
		return NULL;

	controlWnd = GetWndPtr( ob );

	GUI_BGN_SAVE;
	dc = GetDC(controlWnd->m_hWnd);
	GetTextExtentPoint32(dc,str,strlen(str),&size);
	ReleaseDC(controlWnd->m_hWnd,dc);
	GUI_END_SAVE;
	length = size.cx;
	
	tmp = Py_BuildValue("i", length);
	return tmp;
}


static PyObject* py_example_GetStringLengthFromFont(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	char *facename,*str;
	int size, length;
	HFONT hfont,oldfont;
	TEXTMETRIC tm;
			
	if(!PyArg_ParseTuple(args, "Ossi", &ob, &str, &facename, &size))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p, FaceName: %s, Size: %d", controlWnd->m_hWnd, facename, size);
		
	GUI_BGN_SAVE;
	HDC dc = GetDC(controlWnd->m_hWnd);
	hfont=EzCreateFont(dc, facename, size*10, 0, 0, TRUE);
	oldfont = (HFONT)SelectObject(dc,hfont);
	GetTextMetrics(dc,&tm);
	DeleteObject(SelectObject(dc,oldfont));
	ReleaseDC(controlWnd->m_hWnd,dc);
	length = strlen(str)*tm.tmAveCharWidth;
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("i", length);
	return tmp;
}




static PyObject* py_example_SetScrollRange(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int min,max,h;
	
				
	if(!PyArg_ParseTuple(args, "Oiii", &ob, &min, &max, &h))
		return NULL;

	controlWnd = GetWndPtr(ob);
	
	GUI_BGN_SAVE;
	controlWnd->SetScrollRange(h,min,max,TRUE);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject* py_example_ShowScroll(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int h;
			
	if(!PyArg_ParseTuple(args, "Oi", &ob, &h))
		return NULL;

	controlWnd = GetWndPtr(ob);

	GUI_BGN_SAVE;
	controlWnd->ShowScrollBar(h,TRUE);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject* py_example_ScrollWin(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int width, height;
			
	if(!PyArg_ParseTuple(args, "Oii", &ob, &width, &height))
		return NULL;

	controlWnd = GetWndPtr(ob);

	GUI_BGN_SAVE;
	controlWnd->ScrollWindowEx(width, height,NULL,NULL,NULL,NULL,SW_INVALIDATE|SW_ERASE);
	GUI_END_SAVE;
	
	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_example_MesBox(PyObject *self, PyObject *args)
{
	PyObject *tmp = Py_None;
	int result;
	UINT style;
	char* mes,*title,*stl;
	CString st;
	char c;
			
	if(!PyArg_ParseTuple(args, "sss", &mes, &title, &stl))
		return NULL;

	style = MB_TASKMODAL|MB_TOPMOST;

	st = stl;
	c = st[1];

	switch (c)
	{
		case 'e':
			if (st.Find("c")!=-1) style = style|MB_OKCANCEL|MB_ICONERROR;
			else style = style|MB_OK|MB_ICONERROR;
			break;
		case 'w':
			if (st.Find("c")!=-1) style = style|MB_OKCANCEL|MB_ICONWARNING;
			else style = style|MB_OK|MB_ICONWARNING;
			break;
		case 'q':
			if (st.Find("c")!=-1) style = style|MB_YESNOCANCEL|MB_ICONQUESTION;
			else style = style|MB_YESNO|MB_ICONQUESTION;
			break;
		case 'i':
			if (st.Find("c")!=-1) style = style|MB_OKCANCEL|MB_ICONINFORMATION;
			else style = style|MB_OK|MB_ICONINFORMATION;
			break;
		case 'm':
			if (st.Find("c")!=-1) style = style|MB_OKCANCEL|MB_ICONINFORMATION;
			else style = style|MB_OK|MB_ICONINFORMATION;
			break;
		default:
			style = style|MB_OK;
	}
	
	GUI_BGN_SAVE;
	result = ::MessageBox(NULL,mes,title,style);
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("i", result);
	return tmp;
}



static PyObject* py_example_IsWin(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	long result;
			
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr(ob);

	GUI_BGN_SAVE;
	result = IsWindow(controlWnd->m_hWnd);
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("l", result);
	return tmp;
}


static PyObject* py_example_IsWinEnable(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None, *tmp = Py_None;
	CWnd *controlWnd;
	long result;
			
	if(!PyArg_ParseTuple(args, "O", &ob))
		return NULL;

	controlWnd = GetWndPtr(ob);

	GUI_BGN_SAVE;
	result = IsWindowEnabled(controlWnd->m_hWnd);
	GUI_END_SAVE;
	
	tmp = Py_BuildValue("l", result);
	return tmp;
}



static PyObject* py_example_DrawRect(PyObject *self, PyObject *args)
{
	PyObject *ob = Py_None;
	CWnd *controlWnd;
	int x1,y1,x2,y2,x3,y3,x4,y4,red,green,blue;
		
	if(!PyArg_ParseTuple(args, "O(iiiiiiii)iii", &ob, &x1, &y1, &x2, &y2, &x3, &y3, &x4, &y4, &red, &green, &blue))
		return NULL;

	controlWnd = GetWndPtr( ob );

	TRACE("hWnd: %p", controlWnd->m_hWnd);
	POINT p[4];
	p[0].x = x1;
	p[0].y = y1;
	p[1].x = x2;
	p[1].y = y2;
	p[2].x = x3;
	p[2].y = y3;
	p[3].x = x4;
	p[3].y = y4;

	GUI_BGN_SAVE;
	HDC dc = ::GetDC(controlWnd->m_hWnd);
	HBRUSH hbr = CreateSolidBrush(RGB(red,green,blue)),oldhbr; 
	
	oldhbr = (HBRUSH) ::SelectObject(dc,hbr);
	
	::Polygon(dc,(POINT*)p,4);
	::FloodFill(dc,x1,y1,RGB(0,0,0));
	
	::SelectObject(dc,oldhbr);

	::ReleaseDC(controlWnd->m_hWnd,dc);
	GUI_END_SAVE;

	Py_INCREF(Py_None);
	return Py_None;
}



#ifdef _DEBUG
static PyObject *
py_callbackex_CallbackMap (PyObject * self, PyObject * args)
{
	if (!PyArg_ParseTuple (args, ""))
		return NULL;
	
  Py_INCREF (CallbackMap);
  return (CallbackMap);
}
#endif


static PyMethodDef CmifEx2Methods[] = 
{
	{ "CreateFileOpenDlg", (PyCFunction)py_example_CreateFileOpenDlg, 1},
	{ "CreateFileSaveDlg", (PyCFunction)py_example_CreateFileSaveDlg, 1},
	{ "MultiFileOpenDlg", (PyCFunction)py_example_MultiFileOpenDlg, 1},
	{ "CreateButton", (PyCFunction)py_example_CreateButton, 1},
	{ "CreateStatic", (PyCFunction)py_example_CreateStatic, 1},
	{ "CreateEdit", (PyCFunction)py_example_CreateSEdit, 1},
	{ "CreateMultiEdit", (PyCFunction)py_example_CreateMEdit, 1},
	{ "CreateListbox", (PyCFunction)py_example_CreateListbox, 1},
	{ "CreateCombobox", (PyCFunction)py_example_CreateCombobox, 1},
	{ "CreateCheckBox", (PyCFunction)py_example_CreateRCheckbox, 1},
	{ "CreateLeftCheckBox", (PyCFunction)py_example_CreateLCheckbox, 1},
	{ "CreateRadioButton", (PyCFunction)py_example_CreateRRadioButton, 1},
	{ "CreateLeftRadioButton", (PyCFunction)py_example_CreateLRadioButton, 1},
	{ "CreateGroupBox", (PyCFunction)py_example_CreateGroup, 1},
	{ "CreateSeparator", (PyCFunction)py_example_CreateSeparator, 1},
	{ "CreateContainerbox", (PyCFunction)py_example_CreateContainerbox, 1},
	{ "CreateSlider", (PyCFunction)py_example_CreateSlider, 1},
	{ "CreateVerSlider", (PyCFunction)py_example_CreateVSlider, 1},
	{ "CreateDialogbox", (PyCFunction)py_example_CreateDialogbox, 1},
	{ "SetCaption", (PyCFunction)py_example_SetWindowCaption, 1},
	{ "GetText", (PyCFunction)py_example_GetText, 1},
	{ "CheckButton", (PyCFunction)py_example_CheckButton, 1},
	{ "CheckState", (PyCFunction)py_example_CheckState, 1},
	{ "SetFont", (PyCFunction)py_example_SetFont, 1},
	{ "Changed", (PyCFunction)py_example_Changed, 1},
	{ "Cut", (PyCFunction)py_example_Cut, 1},
	{ "Copy", (PyCFunction)py_example_Copy, 1},
	{ "Clear", (PyCFunction)py_example_Clear, 1},
	{ "Paste", (PyCFunction)py_example_Paste, 1},
	{ "Select", (PyCFunction)py_example_Select, 1},
	{ "Replace", (PyCFunction)py_example_Replace, 1},
	{ "Add", (PyCFunction)py_example_AddString, 1},
	{ "Delete", (PyCFunction)py_example_DeleteString, 1},
	{ "DeleteToPos", (PyCFunction)py_example_DeleteToPos, 1},
	{ "ReplaceToPos", (PyCFunction)py_example_ReplaceToPos, 1},
	{ "InsertToPos", (PyCFunction)py_example_InsertToPos, 1},
	{ "Reset", (PyCFunction)py_example_Reset, 1},
	{ "Get", (PyCFunction)py_example_GetString, 1},
	{ "GetPos", (PyCFunction)py_example_GetPos, 1},
	{ "Set", (PyCFunction)py_example_SetSelect, 1},
	{ "SetRange", (PyCFunction)py_example_SetRange, 1},
	{ "SetPosition", (PyCFunction)py_example_SetPosition, 1},
	{ "SetSelection", (PyCFunction)py_example_SetSelection, 1},
	{ "GetRange", (PyCFunction)py_example_GetRange, 1},
	{ "GetPosition", (PyCFunction)py_example_GetPosition, 1},
	{ "GetSelection", (PyCFunction)py_example_GetSelection, 1},
	{ "CreateMenu", (PyCFunction)py_example_CreateMenu, 1},
	{ "SetMenu", (PyCFunction)py_example_SetMenu, 1},
	{ "GetMenu", (PyCFunction)py_example_GetMenu, 1},
	{ "FloatMenu", (PyCFunction)py_example_FloatMenu, 1},
	{ "AppendMenu", (PyCFunction)py_example_AppendMenu, 1},
	{ "CheckMenuItem", (PyCFunction)py_example_CheckMenuItem, 1},
	{ "PopupAppendMenu", (PyCFunction)py_example_PopupAppendMenu, 1},
	{ "InsertMenu", (PyCFunction)py_example_InsertMenu, 1},
	{ "PopupInsertMenu", (PyCFunction)py_example_PopupInsertMenu, 1},
	{ "DestroyMenu", (PyCFunction)py_example_DestroyMenu, 1},
	{ "DeleteMenu", (PyCFunction)py_example_DeleteMenu, 1},
	{ "DrawRect", (PyCFunction)py_example_DrawRect, 1},
	{ "ResizeWindow", (PyCFunction)py_example_ResizeWindow, 1},
	{ "ResizeAllWindows", (PyCFunction)py_example_ResizeAllWindows, 1},
	{ "SetScrollRange", (PyCFunction)py_example_SetScrollRange, 1},
	{ "ShowScroll", (PyCFunction)py_example_ShowScroll, 1},
	{ "ScrollWin", (PyCFunction)py_example_ScrollWin, 1},
	{ "IsWin", (PyCFunction)py_example_IsWin, 1},
	{ "IsWinEnable", (PyCFunction)py_example_IsWinEnable, 1},
	{ "GetStringLength", (PyCFunction)py_example_GetStringLength, 1},
	{ "GetStringLengthFromFont", (PyCFunction)py_example_GetStringLengthFromFont, 1},
	{ "DestroyWindow", (PyCFunction)py_example_DestroyWindow, 1},
	{ "SetFlag", (PyCFunction)py_example_SetFlag, 1},
	{ "MesBox", (PyCFunction)py_example_MesBox, 1},
	#ifdef _DEBUG
	{ "_idMap",			py_callbackex_CallbackMap,		1 },
    #endif
	{ NULL, NULL }
};



PyEXPORT 
void initcmifex2()
{
	PyObject *m, *d;
	m = Py_InitModule("cmifex2", CmifEx2Methods);
	d = PyModule_GetDict(m);
	CmifEx2Error = PyString_FromString("cmifex2.error");
	PyDict_SetItemString(d, "error", CmifEx2Error);
	CallbackMap = PyDict_New();
}

void CmifEx2ErrorFunc(char *str)
{
	PyErr_SetString (CmifEx2Error, str);
	PyErr_Print();
}

#ifdef __cplusplus
}
#endif
