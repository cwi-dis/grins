
#include "htmlex.h"
#include "html.h"
#include "ContainerWnd.h"
#include "font.h"

static PyObject *HtmlExError;
static PyObject *CallbackExError;
PyObject *CallbackMap = NULL;


#define ARROW_CURSOR   0
#define WAIT_CURSOR	   1


char cmifClass[100]="";

COleFont ol1, ol2, ol3, ol4, ol5, ol6, olf, olg;
PyIMPORT CWnd *GetWndPtr(PyObject *);
PyIMPORT CFrameWnd *GetFramePtr(PyObject *self);




void SetProperties(CContainerWnd* pWnd)
{
	

	tagCY sy[7];
	for (UINT k=0; k<7; k++)
	{
		sy[k].Lo = 24 - 2*k;
		sy[k].Hi = 0;
	}


	olg = pWnd->m_html.GetFont();
	olg.SetCharset(GREEK_CHARSET);
	//olg.SetBold(TRUE);
	//olg.SetItalic(TRUE);
	olg.SetUnderline(FALSE);
	olg.SetStrikethrough(FALSE);
	olg.SetWeight(FW_BOLD);
	olg.SetSize(sy[0]);
	//olg.SetName("Hsarl");
	olg.m_bAutoRelease = FALSE;
	pWnd->m_html.SetFont((LPDISPATCH)olg.m_lpDispatch);
	
	
	ol1 = pWnd->m_html.GetHeading1Font();
	ol1.SetCharset(GREEK_CHARSET);
	//ol1.SetBold(TRUE);
	//ol1.SetItalic(TRUE);
	//ol1.SetUnderline(FALSE);
	//ol1.SetName("Hsarl");
	//ol1.SetStrikethrough(FALSE);
	//ol1.SetWeight(FW_BOLD);
	ol1.SetSize(sy[0]);
	ol1.m_bAutoRelease = FALSE;
	pWnd->m_html.SetHeading1Font((LPDISPATCH)ol1.m_lpDispatch);

	ol2 = pWnd->m_html.GetHeading2Font();
	ol2.SetCharset(GREEK_CHARSET);
	//ol2.SetBold(TRUE);
	//ol2.SetItalic(TRUE);
	//ol2.SetName("Hsarl");
	//ol2.SetUnderline(TRUE);
	//ol2.SetStrikethrough(FALSE);
	//ol2.SetWeight(FW_BOLD);
	//ol2.SetSize(sy[1]);
	ol2.m_bAutoRelease = FALSE;
	pWnd->m_html.SetHeading2Font((LPDISPATCH)ol2.m_lpDispatch);

	ol3 = pWnd->m_html.GetHeading3Font();
	ol3.SetCharset(GREEK_CHARSET);
	//ol3.SetBold(TRUE);
	//ol3.SetItalic(TRUE);
	//ol3.SetName("Hsarl");
	//ol3.SetUnderline(FALSE);
	//ol3.SetStrikethrough(FALSE);
	//ol3.SetWeight(FW_BOLD);
	ol3.SetSize(sy[2]);
	ol3.m_bAutoRelease = FALSE;
	pWnd->m_html.SetHeading3Font((LPDISPATCH)ol3.m_lpDispatch);

	ol4 = pWnd->m_html.GetHeading4Font();
	//ol4 = COleFont((LPDISPATCH)ol44.m_lpDispatch);
	ol4.SetCharset(GREEK_CHARSET);
	//ol4.SetBold(TRUE);
	//ol4.SetItalic(TRUE);
	//ol4.SetName("Hsarl");
	//ol4.SetUnderline(FALSE);
	//ol4.SetStrikethrough(FALSE);
	//ol4.SetWeight(FW_BOLD);
	ol4.SetSize(sy[3]);
	ol4.m_bAutoRelease = FALSE;
	pWnd->m_html.SetHeading4Font((LPDISPATCH)ol4.m_lpDispatch);

	ol5 = pWnd->m_html.GetHeading5Font();
	ol5.SetCharset(GREEK_CHARSET);
	ol5.SetSize(sy[4]);
	//ol5.SetBold(TRUE);
	//ol5.SetItalic(TRUE);
	//ol5.SetName("Hsarl");
	//ol5.SetUnderline(FALSE);
	//ol5.SetStrikethrough(FALSE);
	//ol5.SetWeight(FW_BOLD);
	ol5.m_bAutoRelease = FALSE;
	pWnd->m_html.SetHeading5Font((LPDISPATCH)ol5.m_lpDispatch);

	ol6 = pWnd->m_html.GetHeading6Font();
	ol6.SetCharset(GREEK_CHARSET);
	//ol6.SetBold(TRUE);
	//ol6.SetItalic(TRUE);
	//ol6.SetName("Courier New");
	//ol6.SetName("Hsarl");
	//ol6.SetUnderline(FALSE);
	//ol6.SetStrikethrough(FALSE);
	//ol6.SetWeight(FW_LIGHT);
	ol6.SetSize(sy[5]);
	ol6.m_bAutoRelease = FALSE;
	pWnd->m_html.SetHeading6Font((LPDISPATCH)ol6.m_lpDispatch);

	olf = pWnd->m_html.GetFixedFont();
	olf.SetCharset(GREEK_CHARSET);
	//olf.SetBold(TRUE);
	//olf.SetItalic(TRUE);
	//olf.SetName("Hsarl");
	//olf.SetUnderline(FALSE);
	//olf.SetStrikethrough(FALSE);
	//olf.SetWeight(FW_BOLD);
	olf.SetSize(sy[6]);
	olf.m_bAutoRelease = FALSE;
	pWnd->m_html.SetFixedFont((LPDISPATCH)olf.m_lpDispatch);
}
	


#ifdef __cplusplus
extern "C" {
#endif

static PyObject* py_Html_CreateHtmlCtrl(PyObject *self, PyObject *Wnd)
{
	CRect rc, OcxRect;
	CRect offset(0, 0, 0, 0);
	CRect border(0,0, 0, 0);
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

	if (Parent == AfxGetMainWnd())   
	// the window has its own status bar
	// because its parent is the main application window
	{
		GetClientRect(Container->m_hWnd, &rc);

		// to let status bar show itself
		OcxRect = rc - offset;

		OcxRect = OcxRect - border;
	
		//create the Html control
		CWaitCursor wait;

		BOOL bRet = Container->m_html.Create(NULL, WS_VISIBLE|WS_BORDER|WS_CLIPSIBLINGS,
						OcxRect, Container, IDC_HTMLCTRL);

		//SetProperties(Container);
		
		Container->m_Status = CreateStatusWindow(WS_CHILD|WS_VISIBLE, "Status Bar", 
						Container->m_hWnd, 31000); 

		
		TRACE("Status Handle: %X", Container->m_Status);


		SetWindowText(Container->m_Status, "Ready");

	
		return Py_BuildValue("i", bRet);
	}
	else  //the parent Container has the status Bar
	{
		GetClientRect(Container->m_hWnd, &rc);

			
		OcxRect = rc - border;

		CWaitCursor wait;
		//create the Html control
		BOOL bRet = Container->m_html.Create(NULL, WS_VISIBLE|WS_BORDER|WS_CLIPSIBLINGS ,
						OcxRect, Container, IDC_HTMLCTRL);

	
		SetProperties(Container);

		/*Parent->m_Status = CreateStatusWindow(WS_CHILD | WS_VISIBLE, "Status Bar", 
						Parent->m_hWnd, 31000); 

		TRACE("Status Handle: %X", Parent->m_Status);


		SetWindowText(Parent->m_Status, "Ready");*/

			
		return Py_BuildValue("i", bRet);
	} 
	 
	

}
	

static PyObject* py_Html_OpenUrl(PyObject *self, PyObject *args)
{
		
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	char *string;
	char url[256];
	
	if(!PyArg_ParseTuple(args, "Os", &Ob, &string))
	{
		Py_INCREF(Py_None);
		AfxMessageBox("Cannot parse arguments!");
		return Py_None;return NULL;
	}
	
	Container = (CContainerWnd*) GetWndPtr(Ob);

	
	CString str;
	str.GetBuffer(256);
	str.Format("%s", string);

	
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
		
		for (int j=0; j<k; j++)
		{
		
			if (str.GetAt(j)== (TCHAR)('/')) 
				str.SetAt(j, (TCHAR)c);
		}

		if ( (str.Find("C:") != -1) || (str.Find("c:") != -1)  )				
		{
			str = "file:///C|" + str.Right(str.GetLength()-2) ;  //append the file protocol beginning			
		}

		else if ( (str.Find("d:") !=  -1 ) || ( str.Find("D:") != -1 ) )
		{
			str = "file:///D|" + str.Right(str.GetLength()-2) ;  //append the file protocol beginning
		}
		else if ( ((str.GetAt(1) == (TCHAR)(":")) && (str.GetAt(2) == (TCHAR)c) ) )
			
		{
			str = "file:///" + str.Left(1) + "|" + str.Right(str.GetLength()-2) ;
		}
		else
		{
			str = "file:///C|" + str;   //C is the default disk for storage
		}
			
	}
		
		
	strcpy(url, str);

	Container->BeginWaitCursor();

	Container->m_html.RequestDoc(url);

	Container->EndWaitCursor();

	
	return Py_BuildValue("s", url);

}


static PyObject* py_Html_CancelUrl(PyObject *self, PyObject *args)
{

	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	VARIANT variant;
	char *url;

	if(!PyArg_ParseTuple(args, "Os", &Ob, &url))
	{
		Py_INCREF(Py_None);
		return Py_None;return NULL;
	}

	Container = (CContainerWnd*) GetWndPtr(Ob);
	
	Container->m_html.Cancel(variant);

	return Py_BuildValue("i", 1);

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
	strcpy(cmifClass, AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), LoadIcon(NULL, MAKEINTRESOURCE(IDR_PYTHON))));

	TRACE("Cmifclass is %s", cmifClass);
		
	if(newWnd->CreateEx(NULL,
						/*AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS),*/
						cmifClass,
						wndName,
						/*WS_POPUP| WS_VISIBLE | WS_SYSMENU | WS_CAPTION,*/
						ws_flags, 
						//WS_OVERLAPPEDWINDOW | WS_VISIBLE,
						left, top, right, bottom,
						mainWnd->m_hWnd /*NULL*/,
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

	if(newWnd->CreateEx(WS_EX_CONTROLPARENT|WS_EX_CLIENTEDGE,
						AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS),
						title,
						/*WS_CHILD | WS_VISIBLE,*/
						WS_CHILD|WS_CLIPSIBLINGS|WS_VISIBLE,
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
	{ "Stop", py_Html_CancelUrl, 1},
	{ "DestroyOcx", py_Html_DestroyOcx, 1},
	{ "UpdateOcx", py_Html_UpdateOcx, 1},
	{ "CreateWindow", py_CreateWindow, 1},
	{ "CreateChildWindow", py_CreateChildWindow, 1},
	{ "CreateCallback",	py_CreateCallback,	1},
	{ "BeginWaitCursor", py_Html_BeginWait, 1},
	{ "EndWaitCursor", py_Html_EndWait, 1},
#ifdef _DEBUG
	{ "_idMap",			py_CallbackMap,	1},
#endif
	{ NULL, NULL }
};


PyEXPORT 
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



















