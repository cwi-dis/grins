#include "stdafx.h"

#include "ContainerWnd.h"
#include "..\GRiNSRes\GRiNSRes.h" // Resources defines in the GRiNS resource DLL.

#include "win32ui.h"
#include "win32win.h"


#include "moddef.h"
DECLARE_PYMODULECLASS(Htmlex);
IMPLEMENT_PYMODULECLASS(Htmlex,GetHtmlex,"Htmlex Module Wrapper Object");



// global
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


static PyObject* py_example_SetFlag(PyObject *self, PyObject *args)
{
	int x;
			
	if(!PyArg_ParseTuple(args, "i", &x))
		return NULL;

	if (x==1)
		flag = TRUE;
	else flag = FALSE;

	RETURN_NONE;
	}


static PyObject* py_Html_CreateHtmlCtrl(PyObject *self, PyObject *Wnd)
{
	CRect rc;
	int st_bar_h;
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	
	AfxEnableControlContainer();
	

	if(!PyArg_ParseTuple(Wnd, "O", &Ob))
		return NULL;
	
	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL)
		RETURN_ERR("Container not created");

	if (Container->m_ctrl_cr)		// OCX exists, no need to be created again
		return Py_BuildValue("i", 2);
		

	CContainerWnd* Parent = (CContainerWnd*) Container->GetParent();

	

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

		Container->m_ctrl_cr = TRUE;
		return Py_BuildValue("i", bRet);
	}
	else  //the parent Container has the status Bar
	{
		GetClientRect(Container->m_hWnd, &rc);
			
		CWaitCursor wait;
		//create the Html control
		BOOL bRet = Container->m_html.Create(NULL, WS_VISIBLE|WS_CLIPSIBLINGS ,
						rc, Container, 3000);
		
		Container->m_ctrl_cr = TRUE;
		Container->m_Status = NULL;

		return Py_BuildValue("i", bRet);
	} 
}
	

static PyObject* py_retrieve_url(PyObject *self, PyObject *args)
{
	PyObject *Ob;
	char *url;
	if(!PyArg_ParseTuple(args, "Os", &Ob, &url))
		return NULL;

	CContainerWnd *Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");
	
	Container->m_html.Navigate(url,NULL,NULL,NULL,NULL);
	
	return Py_BuildValue("s", url);
	

	/*
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	char *string;
	char url[256];
	CString str;
	
	if(!PyArg_ParseTuple(args, "Os", &Ob, &string))
		return NULL;


	static char filter[] = "HTM Files (*.HTM)|*.HTM|All Files (*.*)|*.*||";
	CFileDialog Dlg(TRUE, NULL, NULL, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = "Open File URL";
	
	strcpy(Dlg.m_ofn.lpstrFile, string);
	
	str = Dlg.GetPathName();

	
	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

	
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
	Container->m_html.Navigate(url,NULL,NULL,NULL,NULL);
	return Py_BuildValue("s", url);
	*/
}



static PyObject* py_Html_virtual_FileDialog(PyObject *self,PyObject *args)
{
		

	char res[256];
	CString strPath, strurl;
	char* FileName;
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 
	


	if(!PyArg_ParseTuple(args, "Os", &Ob, &FileName))
		return NULL;


	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

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
	//strPath.SetAt(1, '|');
	TRACE("Path variable is now %s\n", strPath);
	CString temp("file://");
	strurl = temp + strPath;


	lstrcpy(res, strurl);

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
		return NULL;

	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

	CString str = url;
	Container->m_html.Stop();
	
	strcpy(res, str);
	return Py_BuildValue("s", res);

}

static PyObject* py_Html_DestroyOcx(PyObject *self, PyObject *args)
{
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 

	if(!PyArg_ParseTuple(args, "O", &Ob))
		return NULL;

	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

	Container->m_html.DestroyWindow();

	Container->m_ctrl_cr = FALSE;

	return Py_BuildValue("i", 1);
}	

static PyObject* py_Html_UpdateOcx(PyObject *self, PyObject *args)
{
	PyObject *Ob = Py_None;
	CContainerWnd *Container; 

	if(!PyArg_ParseTuple(args, "O", &Ob))
		return NULL;

	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

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
		return NULL;

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
		return NULL;
	}	

	CString title(wndName);
	newWnd->m_title = title;	//update the window's title variable
								//displayed in the status bar
								//to serve as an identifier of the owner
								//of the displayed messages 

	// We will revisit module
	//orgProc = (WNDPROC)SetWindowLong(newWnd->m_hWnd, GWL_WNDPROC, (LONG)MyWndProc);

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
		return NULL;

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
		return NULL;
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
		RETURN_ERR("Cannot parse arguments!");
	
	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

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
		RETURN_ERR("DevMsg: py_Html_EndWait");

	
	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

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
			RETURN_ERR("DevMsg: py_CreateCallback");


	pContainer = (CContainerWnd*) GetWndPtr(ob);   //get Wnd pointer
	if(pContainer==NULL) RETURN_ERR("Container not created");


	// make sure the callback is a valid callable object
	if (!PyCallable_Check (callback))
		RETURN_ERR("DevMsg: argument must be a callable object");

	callbackID = Py_BuildValue ("i", (int)ID);

	// associate the timer id with the given callback function
	if(CallbackMap==NULL)
		CallbackMap = PyDict_New();

	if (PyObject_SetItem (CallbackMap, callbackID, callback) == -1)
			RETURN_ERR("DevMsg: PyObject_SetItem");

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
	int cur_type=0;

	
	if(!PyArg_ParseTuple(args, "Oi", &Ob, &cur_type))
		RETURN_ERR("DevMsg: py_Html_SetCur");

	
	Wind = (CWnd*) GetWndPtr(Ob);
	if(Wind==NULL) RETURN_ERR("Wind not created");

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
	char *title, *fname, *fltr;
	char filename[256];
	char filter[512];
	
	if(!PyArg_ParseTuple(args, "sss", &title, &fname, &fltr))
		RETURN_ERR("DevMsg: py_FDlg");

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
		RETURN_ERR("DevMsg: py_Html_SetBkColor");

	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

	color = RGB(r,g,b);

	//Container->m_html.SetBackColor((unsigned long) color);

	RETURN_NONE;
}	



static PyObject* py_Html_SetFgColor(PyObject *self, PyObject *args)
{
	PyObject *Ob = Py_None;
	CContainerWnd *Container;
	int r,g,b;
	COLORREF color;

	if(!PyArg_ParseTuple(args, "O(iii)", &Ob, &r, &g, &b))
		RETURN_ERR("DevMsg: py_Html_SetFgColor");

	Container = (CContainerWnd*) GetWndPtr(Ob);
	if(Container==NULL) RETURN_ERR("Container not created");

	color = RGB(r,g,b);

	//Container->m_html.SetForeColor((unsigned long) color);

	RETURN_NONE;
}	


BEGIN_PYMETHODDEF(Htmlex)
	{ "CreateViewer", py_Html_CreateHtmlCtrl, 1},
	{ "RetrieveUrl", py_retrieve_url, 1},
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
	{ "SetFlag", py_example_SetFlag, 1},
	{ "SetBkColor", py_Html_SetBkColor, 1},
	{ "SetFgColor", py_Html_SetFgColor, 1},
END_PYMETHODDEF()


DEFINE_PYMODULETYPE("PyHtmlex",Htmlex);
