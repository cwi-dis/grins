
#include "afxdisp.h"
#include "htmlex.h"
#include "ContainerWnd.h"
#include "GRiNSRes.h"


static PyObject *HtmlExError;
static PyObject *CallbackExError;
PyObject *CallbackMap = NULL;


#define ARROW_CURSOR		0
#define WAIT_CURSOR			1
#define CROSS_CURSOR		2
#define NORTH_SOUTH_CURSOR	3
#define EAST_WEST_CURSOR    4
#define ALL_CURSOR		    5


static char cmifClass[100]="";

static WNDPROC	orgProc;
static BOOL flag=FALSE;

PYW_EXPORT CWnd *GetWndPtr(PyObject *);
PYW_EXPORT CFrameWnd *GetFramePtr(PyObject *self);




	


#ifdef __cplusplus
extern "C" {
#endif



static LRESULT CALLBACK MyWndProc (HWND hwnd, UINT iMsg, WPARAM wParam, LPARAM lParam)
{

	//HWND parent;
	//HWND grandparent;
			
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



static PyObject* py_example_SetFlag(PyObject *self, PyObject *args)
{
	int x;
			
	if(!PyArg_ParseTuple(args, "i", &x))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	if (x==1)
		flag = TRUE;
	else flag = FALSE;

	Py_INCREF(Py_None);
	return Py_None;
}




static PyObject* py_Html_CreateHtmlCtrl(PyObject *self, PyObject *Wnd)
{
	CRect rc;
	int st_bar_h;
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	
	AfxEnableControlContainer();
	

	if(!PyArg_ParseTuple(Wnd, "O", &Ob))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}    
	
	Container = (CContainerWnd*) GetWndPtr(Ob);

	if (Container->m_ctrl_cr)		// OCX exists, no need to be created again
		return Py_BuildValue("i", 2);
		

	CContainerWnd* Parent = (CContainerWnd*) Container->GetParent();

	Container->m_ctrl_cr = TRUE;

	if (Parent == NULL)
	{
		GetClientRect(Container->m_hWnd, &rc);

		
		CWaitCursor wait;

		st_bar_h = GetSystemMetrics(SM_CYCAPTION)+1;

		rc.DeflateRect(0,0,0,st_bar_h);
		
		BOOL bRet = Container->m_html.Create(NULL, WS_VISIBLE|WS_BORDER|WS_CLIPSIBLINGS,
						rc, Container, 3000); // NOTE: Magic number for thisID!!!!

		Container->m_Status = CreateStatusWindow(WS_CHILD|WS_VISIBLE, "Status Bar", 
						Container->m_hWnd, 31000);  // And this!

		
		SetWindowText(Container->m_Status, "Ready");

		return Py_BuildValue("i", bRet);
	}
	else  //the parent Container has the status Bar
	{
		GetClientRect(Container->m_hWnd, &rc);
			
		CWaitCursor wait;
		//create the Html control
		BOOL bRet = Container->m_html.Create(NULL, WS_VISIBLE|WS_CLIPSIBLINGS ,
						rc, Container, 3000);
		
		Container->m_Status = NULL;

		return Py_BuildValue("i", bRet);
	} 
}
	

static PyObject* py_Html_OpenUrl(PyObject *self, PyObject *args)
{
		
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	char *string;
	char url[256];
	CString str;
	
	if(!PyArg_ParseTuple(args, "Os", &Ob, &string))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Cannot parse arguments!");
		return Py_None;return NULL;
	}


	static char filter[] = "HTM Files (*.HTM)|*.HTM|All Files (*.*)|*.*||";
	CFileDialog Dlg(TRUE, NULL, NULL, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = "Open File URL";
	
	strcpy(Dlg.m_ofn.lpstrFile, string);
	
	str = Dlg.GetPathName();

	
	Container = (CContainerWnd*) GetWndPtr(Ob);

	
	
	
	/*CString temp2;
	temp2.Format("str is %s\n", str);
	AfxMessageBox(temp2, MB_OK);*/   //has been used for debugging purposes
	
	//check if the given string is a file or other protocol's url 
	if ((str.Find("www.") == -1) && (str.Find("http:")==-1))
	{
		//file protocol- format the string to a 
		//proper form to be used for retrieval
		int k = str.GetLength();

		CString help = CString("\\");
		char c = help.GetAt(0);     // c is the newline character
		
		/*for (int j=0; j<k; j++)
		{
		
			if (str.GetAt(j)== (TCHAR)('/')) 
				str.SetAt(j, (TCHAR)c);
		}*/

		for (int j=0; j<k; j++)
		{
		
			if (str.GetAt(j)== (TCHAR)c) 
				str.SetAt(j, (TCHAR)('/'));
		}


		if ( (str.Find("C:") != -1) || (str.Find("c:") != -1)  )				
		{
			str = "file:///C|" + str.Right(str.GetLength()-2) ;  //append the file protocol beginning			
		}

		else if ( (str.Find("d:") !=  -1 ) || ( str.Find("D:") != -1 ) )
		{
			str = "file:///D|" + str.Right(str.GetLength()-2) ;  //append the file protocol beginning
		}
		else //if ( ((str.GetAt(1) == (TCHAR)(":")) && (str.GetAt(2) == (TCHAR)c) ) )
			
		{
			str = "file:///" + str.Left(1) + "|" + str.Right(str.GetLength()-2) ;
		}
		
			
	}
		
		
	strcpy(url, str);

	//Container->BeginWaitCursor();

	Container->m_html.Navigate(url,NULL,NULL,NULL,NULL);

	//Container->EndWaitCursor();

	
	return Py_BuildValue("s", url);

}



static PyObject* py_Html_virtual_FileDialog(PyObject *self,PyObject *args)
{
		
	char res[256];
	CString strPath, strurl;
	char* FileName;
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	


	if(!PyArg_ParseTuple(args, "Os", &Ob, &FileName))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Error Receiving CMIF presentation String", MB_OK);
		return Py_None;
		return NULL;
	
	}

	Container = (CContainerWnd*) GetWndPtr(Ob);

	static char filter[] = "HTM Files (*.HTM)|*.HTM|All Files (*.*)|*.*||";
	CFileDialog Dlg(TRUE, NULL, NULL, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = "Open File URL";
	
	strcpy(Dlg.m_ofn.lpstrFile, FileName);
	
	strPath = Dlg.GetPathName();

	char c = strPath.GetAt(2);
	UINT length = strPath.GetLength();
	for (UINT i=0; i<length; i++)
	{
		if (strPath.GetAt(i) == ((TCHAR)'\\'))
			strPath.SetAt(i, '/');
	}
	strPath.SetAt(1, '|');
	TRACE("Path variable is now %s\n", strPath);
	CString temp("file:///");
	strurl = temp + strPath;
	TRACE("URL is: %s \n", strurl);

	strcpy(res, strurl);

	Container->m_html.Navigate(res,NULL,NULL,NULL,NULL);

	return Py_BuildValue("s", res);
}



static PyObject* py_Html_CancelUrl(PyObject *self, PyObject *args)
{

	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	char res[256];
	char *url;

	if(!PyArg_ParseTuple(args, "Os", &Ob, &url))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	Container = (CContainerWnd*) GetWndPtr(Ob);
	CString str = url;
	//COleVariant vr((LPCTSTR)str);
	Container->m_html.Stop();
	
	//Container->m_html.Cancel(variant);
	strcpy(res, str);
	//AfxMessageBox(str, MB_OK);

	return Py_BuildValue("s", res);

}

static PyObject* py_Html_DestroyOcx(PyObject *self, PyObject *args)
{
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 

	if(!PyArg_ParseTuple(args, "O", &Ob))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	Container = (CContainerWnd*) GetWndPtr(Ob);

	Container->m_html.DestroyWindow();

	Container->m_ctrl_cr = FALSE;

	return Py_BuildValue("i", 1);
}	

static PyObject* py_Html_UpdateOcx(PyObject *self, PyObject *args)
{
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 

	if(!PyArg_ParseTuple(args, "O", &Ob))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	Container = (CContainerWnd*) GetWndPtr(Ob);

	Container->m_html.UpdateWindow();

	return Py_BuildValue("i", 1);
}	


static PyObject* py_CreateWindow(PyObject *self, PyObject *args)
{
	char *wndName;
	PyObject *testOb = Py_None;
	CWnd  *mainWnd;
	CContainerWnd *newWnd;
	PyCWnd *testWnd;
	int left, top, right, bottom;
	int visible, ws_flags;
	
	newWnd = new CContainerWnd;

	if(!PyArg_ParseTuple(args, "siiiii", &wndName, &top, &left, &right, &bottom, &visible))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	mainWnd = AfxGetMainWnd();

	if(!visible)
		ws_flags = WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN;
	else
		ws_flags = 	WS_OVERLAPPEDWINDOW | WS_VISIBLE | WS_CLIPCHILDREN;

	TRACE("Window Handle %X\n", mainWnd->m_hWnd);
	
	if(cmifClass[0]==0)
	strcpy(cmifClass, AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), AfxGetApp()->LoadIcon(MAKEINTRESOURCE(IDR_PYTHON))));

	TRACE("Cmifclass is %s", cmifClass);
		
	if(newWnd->CreateEx(NULL,
						/*AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS),*/
						cmifClass,
						wndName,
						/*WS_POPUP| WS_VISIBLE | WS_SYSMENU | WS_CAPTION,*/
						ws_flags, 
						//WS_OVERLAPPEDWINDOW | WS_VISIBLE,
						left, top, right, bottom,
						/*mainWnd->m_hWnd*/ NULL,
						NULL))
		TRACE("CmifEx CreateWindow OK!\n");
	else
	{
		TRACE("CmifEx CreateWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	

	CString title(wndName);
	newWnd->m_title = title;	//update the window's title variable
								//displayed in the status bar
								//to serve as an identifier of the owner
								//of the displayed messages 


	orgProc = (WNDPROC)SetWindowLong(newWnd->m_hWnd, GWL_WNDPROC, (LONG)MyWndProc);

	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}


static PyObject* py_CreateChildWindow(PyObject *self, PyObject *args)
{
	PyObject *testOb = Py_None, *ob = Py_None;
	CContainerWnd *newWnd;
	CWnd *parentWnd;
	PyCWnd *testWnd;
	int left, top, right, bottom;
	char *title;
		
	if(!PyArg_ParseTuple(args, "sOiiii", &title, &ob, &left, &top, &right, &bottom))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	newWnd = new CContainerWnd;
	parentWnd = GetWndPtr(ob);

	if(newWnd->CreateEx(WS_EX_CONTROLPARENT,
						AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS),
						title,
						/*WS_CHILD | WS_VISIBLE,*/
						WS_CHILD|WS_CLIPSIBLINGS|WS_VISIBLE|WS_CLIPCHILDREN,
						/*WS_CHILD |WS_POPUP| WS_VISIBLE | WS_SYSMENU | WS_CAPTION,*/
						/*WS_CHILD | WS_VISIBLE,*/
						left, top, right, bottom,
						parentWnd->m_hWnd,
						NULL))
		TRACE("CmifEx CreateChildWindow OK!\n");
	else
	{
		TRACE("CmifEx CreateChildWindow FALSE!\n");
		Py_INCREF(Py_None);
		return Py_None;
	}	
  
	CString wndtitle(title);
	newWnd->m_title = wndtitle;	//update the window's title variable
								//displayed in the status bar
								//to serve as an identifier of the owner
								//of the displayed messages 

	testWnd = testWnd->make(testWnd->type,(CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}

static PyObject* py_Html_BeginWait(PyObject *self, PyObject *args)
{
		
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	
	if(!PyArg_ParseTuple(args, "O", &Ob))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Cannot parse arguments!");
		return Py_None;return NULL;
	}
	
	Container = (CContainerWnd*) GetWndPtr(Ob);

	Container->BeginWaitCursor();
	Container->m_html.BeginWaitCursor();
	Container->m_cursor_type = WAIT_CURSOR;

	return Py_BuildValue("i", 1);
}

static PyObject* py_Html_EndWait(PyObject *self, PyObject *args)
{
		
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	
	if(!PyArg_ParseTuple(args, "O", &Ob))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Cannot parse arguments!");
		return Py_None;return NULL;
	}
	
	Container = (CContainerWnd*) GetWndPtr(Ob);

	Container->EndWaitCursor();
	Container->m_html.EndWaitCursor();
	Container->m_cursor_type = ARROW_CURSOR;

	return Py_BuildValue("i", 1);
}


static PyObject* py_CreateCallback(PyObject *self, PyObject *args)
{
	PyObject *callback, *callbackID;
	PyObject  *ob = Py_None;
	BOOL status=FALSE;
	CContainerWnd* pContainer;
	static int ID=0;
	
	if(!PyArg_ParseTuple(args, "OO",  &callback, &ob))
	{
		CallbackExErrorFunc("CreateCallback(Callable Function, Window Handle)");
		return Py_BuildValue("i", status);
	}

	pContainer = (CContainerWnd*) GetWndPtr(ob);   //get Wnd pointer


	// make sure the callback is a valid callable object
	if (!PyCallable_Check (callback))
	{
		CallbackExErrorFunc("argument must be a callable object");
		return Py_BuildValue("i", status);
	}

	callbackID = Py_BuildValue ("i", (int)ID);

	// associate the timer id with the given callback function
	if (PyObject_SetItem (CallbackMap, callbackID, callback) == -1)
	{
		CallbackExErrorFunc("internal error, couldn't set timer id callback item");
		return Py_BuildValue("i", status);
	}

	//CallableFunction(i, ID);
	pContainer->m_id = ID;

	status = TRUE;
	ID++;
	return Py_BuildValue("i", status);
}



// assistant function used independently of Html channels

static PyObject* py_Html_SetCur(PyObject *self, PyObject *args)
{
		
	PyObject *Ob = Py_None;
	CWnd *Wind; 
	int cur_type;

	
	if(!PyArg_ParseTuple(args, "Oi", &Ob, &cur_type))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Htmlex.SetCursor(window hwnd, cursor_type)", MB_OK);
		return Py_None;return NULL;
	}
	
	Wind = (CWnd*) GetWndPtr(Ob);

	switch (cur_type)
	{
	  case WAIT_CURSOR:
	 		SetCursor(LoadCursor(NULL, IDC_WAIT));
			break;
	  case ARROW_CURSOR:
			SetCursor(LoadCursor(NULL, IDC_ARROW));
			break;
	  case CROSS_CURSOR:
			SetCursor(LoadCursor(NULL, IDC_CROSS));
			break;
	  case NORTH_SOUTH_CURSOR:
			SetCursor(LoadCursor(NULL, IDC_SIZENS));	
			break;
	  case EAST_WEST_CURSOR:
			SetCursor(LoadCursor(NULL, IDC_SIZEWE));
			break;
	  case ALL_CURSOR:
			SetCursor(LoadCursor(NULL, IDC_SIZEALL));
			break;
	  default:
			break;
	}
		
	return Py_BuildValue("i", cur_type);
}


static PyObject* py_FDlg(PyObject *self, PyObject *args)
{
	PyObject *testOb = Py_None, *ob = Py_None;
	//PyCWnd *testWnd;
	char *title, *fname, *fltr;
	char filename[256];
	char filter[512];
	
	if(!PyArg_ParseTuple(args, "sss", &title, &fname, &fltr))
	{
		AfxMessageBox("Cannot parse arguments!", MB_OK);
		Py_INCREF(Py_None);
		return Py_None;
	}

	strcpy(filename, fname);
	strcpy(filter, fltr);
	CFileDialog Dlg(TRUE, NULL, filename, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = (LPCTSTR)title;
	int ret = Dlg.DoModal();

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



static PyObject* py_Html_SetBkColor(PyObject *self, PyObject *args)
{
	PyObject *Ob = Py_None;
	CContainerWnd *Container;
	int r,g,b;
	COLORREF color;

	if(!PyArg_ParseTuple(args, "O(iii)", &Ob, &r, &g, &b))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	Container = (CContainerWnd*) GetWndPtr(Ob);

	color = RGB(r,g,b);

	//Container->m_html.SetBackColor((unsigned long) color);

	Py_INCREF(Py_None);
	return Py_None;
}	



static PyObject* py_Html_SetFgColor(PyObject *self, PyObject *args)
{
	PyObject *Ob = Py_None;
	CContainerWnd *Container;
	int r,g,b;
	COLORREF color;

	if(!PyArg_ParseTuple(args, "O(iii)", &Ob, &r, &g, &b))
	{
		Py_INCREF(Py_None);
		return Py_None;
	}

	Container = (CContainerWnd*) GetWndPtr(Ob);

	color = RGB(r,g,b);

	//Container->m_html.SetForeColor((unsigned long) color);

	Py_INCREF(Py_None);
	return Py_None;
}	




#ifdef _DEBUG
static PyObject *
py_CallbackMap (PyObject * self, PyObject * args)
{
	if (!PyArg_ParseTuple (args, ""))
		return NULL;
	
  Py_INCREF (CallbackMap);
  return (CallbackMap);
}
#endif



static PyMethodDef HtmlExMethods[] = 
{
	{ "CreateViewer", py_Html_CreateHtmlCtrl, 1},
	{ "RetrieveUrl", py_Html_OpenUrl, 1},
	{ "RetrieveFileUrl",py_Html_virtual_FileDialog, 1},
	{ "Stop", py_Html_CancelUrl, 1},
	{ "DestroyOcx", py_Html_DestroyOcx, 1},
	{ "UpdateOcx", py_Html_UpdateOcx, 1},
	{ "CreateWindow", py_CreateWindow, 1},
	{ "CreateChildWindow", py_CreateChildWindow, 1},
	{ "CreateCallback",	py_CreateCallback,	1},
	{ "BeginWaitCursor", py_Html_BeginWait, 1},
	{ "EndWaitCursor", py_Html_EndWait, 1},
	{ "SetCursor", py_Html_SetCur, 1},
	{ "FDlg", py_FDlg, 1},
	{ "SetFlag", (PyCFunction)py_example_SetFlag, 1},
	{ "SetBkColor", (PyCFunction)py_Html_SetBkColor, 1},
	{ "SetFgColor", (PyCFunction)py_Html_SetFgColor, 1},
#ifdef _DEBUG
	{ "_idMap",			py_CallbackMap,	1},
#endif
	{ NULL, NULL }
};


__declspec(dllexport) 
void initHtmlex()
{
	PyObject *m, *d;
	m = Py_InitModule("Htmlex", HtmlExMethods);
	d = PyModule_GetDict(m);
	HtmlExError = PyString_FromString("htmlex.error");
	PyDict_SetItemString(d, "error", HtmlExError);
	CallbackMap = PyDict_New();
}


void CallbackExErrorFunc(char *str)
{
	PyErr_SetString (CallbackExError, str);
	PyErr_Print();
}



#ifdef __cplusplus
}
#endif
