// CMIF_ADD
//
//
//
// Note that this source file contains embedded documentation.
// This documentation consists of marked up text inside the
// C comments, and is prefixed with an '@' symbol.  The source
// files are processed by a tool called "autoduck" which
// generates Windows .hlp files.
// @doc

// Purpose: Enhancements to the PyCWnd, PyCFrameWnd, PyCMDIFrameWnd and PyCMDIChildWnd class

#include "win32rgn.h"
// already by including #include "win32dc.h"

// @pymethod int|PyCWnd|GetWindowLong|The function retrieves the 32-bit (long) value at the specified offset into the extra window memory of a window. 
// Return Values: the long  
static PyObject *
ui_window_get_window_long(PyObject *self, PyObject *args)
{
	int index;
	if (!PyArg_ParseTuple(args, "i:GetWindowLong",&index))
		return NULL;
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	// @pyseemfc CWnd|GetWindowLong
	GUI_BGN_SAVE;
	long r = ::GetWindowLong(pWnd->m_hWnd,index);
	GUI_END_SAVE;
	return Py_BuildValue("l", (long)r);
}


// @pymethod int|PyCWnd|SetWindowLong|The function sets a 32-bit (long) value at the specified offset into the extra window memory of a window.
static PyObject *
ui_window_set_window_long(PyObject *self, PyObject *args)
{
	int index;
	long lnew;
	if (!PyArg_ParseTuple(args, "il:GetWindowLong",&index,&lnew))
		return NULL;
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	// @pyseemfc CWnd|SetWindowLong
	GUI_BGN_SAVE;
	long r = ::SetWindowLong(pWnd->m_hWnd,index,lnew);
	GUI_END_SAVE;
	return Py_BuildValue("l", (long)r);
}


// @pymethod (left, top, right, bottom)|PyCWnd|ScreenToClientRect|Converts the screen coordinates of a given rectangle on the display to client coordinates. 
static PyObject *
ui_window_screen_to_client_rect(PyObject *self, PyObject *args)
{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	CRect rect;
    // @pyparm (left, top, right, bottom) or (x,y)|rect||The coordinates to convert.
	if (!PyArg_ParseTuple(args,"(iiii):ScreenToClient",
		&rect.left, &rect.top, &rect.right, &rect.bottom))
		return NULL;

	// @pyseemfc CWnd|ScreenToClientRect
	GUI_BGN_SAVE;
	pWnd->ScreenToClient( &rect );
	GUI_END_SAVE;
	// @rdesc The result is the same size as the input argument.
	return Py_BuildValue("(iiii)",rect.left, rect.top, rect.right, rect.bottom);
}

// @pymethod (left, top, right, bottom)|PyCWnd|ClientToScreenRect|Converts the client coordinates of a given rectangle on the display to screen coordinates.
// The new screen coordinates are relative to the upper-left corner of the system display. 
// This function assumes that the given rectangle is in client coordinates.
static PyObject *
ui_window_client_to_screen_rect(PyObject *self, PyObject *args)
{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	CRect rect;
	// @pyparm (left, top, right, bottom)|rect||The client coordinates.
	if (!PyArg_ParseTuple(args,"(iiii):ClientToScreenRect", &rect.left, &rect.top, &rect.right, &rect.bottom))
		return NULL;
	// @pyseemfc CWnd|ClientToScreenRect
	GUI_BGN_SAVE;
	pWnd->ClientToScreen( &rect );
	GUI_END_SAVE;
	return Py_BuildValue("(iiii)",rect.left, rect.top, rect.right, rect.bottom);
}

// @pymethod (x, y)|PyCWnd|ChildWindowFromPoint|Returns the child window that contains the point and if not found the window asked for
static PyObject *
ui_window_child_window_from_point(PyObject *self, PyObject *args)
{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd) return NULL;
	CPoint point;
	// @pyparm (x, y)|point||The point.
	if (!PyArg_ParseTuple(args,"(ii):ChildWindowFromPoint", &point.x, &point.y))
		return NULL;
	// @pyseemfc CWnd|ChildWindowFromPoint
	GUI_BGN_SAVE;
	CWnd* pChild=pWnd->ChildWindowFromPoint(point);
	GUI_END_SAVE;
	if(!pChild || !pChild->GetSafeHwnd())
		RETURN_NONE;
	return PyCWnd::make( UITypeFromCObject(pChild), pChild )->GetGoodRet();
}

static PyObject *
ui_window_validate_rect(PyObject *self, PyObject *args)
{
	CWnd *pWnd = GetWndPtr(self);
	BOOL erase=TRUE;

	if (!pWnd)
		return NULL;
	CRect rect(CFrameWnd::rectDefault), *r;
	// @pyparm (left, top, right, bottom)|rect|(0,0,0,0)|Rectangle to be
	// updated.  If default param is used, the entire window is validated.
	if (!PyArg_ParseTuple (args,
	                      "(iiii):ValidateRect",
	                      &rect.left, &rect.top,
	                      &rect.right, &rect.bottom)) {
		return NULL;
	}
	if (rect==CFrameWnd::rectDefault)
		r = NULL;
	else
		r = &rect;
	GUI_BGN_SAVE;
	pWnd->ValidateRect(r);
	// @pyseemfc CWnd|ValidateRect
	GUI_END_SAVE;
	RETURN_NONE;
}


/* 
// @pymethod |PyCWnd|LockWindowUpdate|Disables drawing in the given window
static PyObject *
ui_lock_window_update(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS(args);
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	GUI_BGN_SAVE;
	pWnd->LockWindowUpdate(); // @pyseemfc CWnd|LockWindowUpdate
	GUI_END_SAVE;
	RETURN_NONE;
}
*/

/*
// @pymethod |PyCWnd|UnlockWindowUpdate|Unlocks a window that was locked with LockWindowUpdate
static PyObject *
ui_unlock_window_update(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS(args);
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;

	GUI_BGN_SAVE;
	pWnd->UnlockWindowUpdate(); // @pyseemfc CWnd|UnLockWindowUpdate
	GUI_END_SAVE;
	RETURN_NONE;
}
*/

/*
// @pymethod <o PyCDC>|PyCWnd|GetWindowDC|Gets the windows current DC object.
static PyObject *
ui_window_get_window_dc (PyObject *self, PyObject *args)
{
  CHECK_NO_ARGS(args);
  CWnd *pWnd = (CWnd *) GetWndPtr (self);
  if (pWnd == NULL)
    return NULL;

  // create MFC device context
  CDC *pDC = pWnd->GetWindowDC();
  if (pDC==NULL)
    RETURN_ERR ("Could not get the DC for the window.");

  // create Python device context
  ui_dc_object *dc =
    (ui_dc_object *) ui_assoc_object::make (ui_dc_object::type, pDC)->GetGoodRet();
    return dc;
}*/

/*
// @mfcproto CDC* GetDCEx( CRgn* prgnClip, DWORD flags );
// @pymethod <o PyCDC>|PyCWnd|GetDCEx|Gets the windows current DC object with extended caps.
static PyObject *
ui_window_get_dc_ex(PyObject *self, PyObject *args)
	{
	CWnd *pWnd = (CWnd *) GetWndPtr (self);
	if (pWnd == NULL)return NULL;

	PyObject *objRgn;
	DWORD flags;
	if (!PyArg_ParseTuple(args,"Oi:InvalidateRgn",&objRgn,&flags)) 
		return NULL;

	CRgn *prgnClip = PyCRgn::GetRgn(objRgn);
	if (!prgnClip) return NULL;

	// create MFC device context
	CDC *pDC = pWnd->GetDCEx(prgnClip,flags);
	if (pDC==NULL)
		RETURN_ERR ("Could not get the DC for the window.");

	// create Python device context
	ui_dc_object *dc =
		(ui_dc_object *) ui_assoc_object::make (ui_dc_object::type, pDC)->GetGoodRet();
	return dc;
	}
*/

/*
// @pymethod |PyCWnd|IsWindow|determines whether the specified window handle identifies an existing window
static PyObject *
ui_window_is_window(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS(args);
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;

	BOOL bAns=::IsWindow(pWnd->m_hWnd);   
	return Py_BuildValue("i",bAns);
	}
*/

/*
// @pymethod |PyCWnd|MapWindowPoints|Converts (maps) a set of points from the coordinate space of a window to the coordinate space of another window.
static PyObject *
ui_window_map_window_points(PyObject *self, PyObject *args)
	{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;
  
	PyObject *pPyCWnd;
	PyObject *point_list;

	if (!PyArg_ParseTuple(args,"OO:MapWindowPoints",&pPyCWnd,&point_list)) 
		return NULL;

	CWnd *pWndTo;
	if (pPyCWnd==Py_None)
		pWndTo = NULL; // i.e screen coordinates conversion
	else if (ui_base_class::is_uiobject(pPyCWnd, &PyCWnd::type))
		pWndTo = GetWndPtr(pPyCWnd);
	else
		RETURN_TYPE_ERR("1st argument must be a window object, or None");

	if(!PyList_Check(point_list)) 
		return NULL;

	// Convert the list of point tuples into an array of POINT structs
	int num = PyList_Size (point_list);
	POINT * point_array = new POINT[num];
	for (int i=0; i < num; i++) 
		{
		PyObject * point_tuple = PyList_GetItem (point_list, i);
		if (!PyTuple_Check (point_tuple) || PyTuple_Size (point_tuple) != 2) 
			{
			PyErr_SetString (PyExc_ValueError,
					 "point list must be a list of (x,y) tuples");
			delete[] point_array;
			return NULL;
			} 
		else 
			{
			long x, y;
			PyObject *px, *py;
			px = PyTuple_GetItem (point_tuple, 0);
			py = PyTuple_GetItem (point_tuple, 1);
			if ((!PyInt_Check(px)) || (!PyInt_Check(py))) 
				{
				PyErr_SetString (PyExc_ValueError,
					   "point list must be a list of (x,y) tuples");
				delete[] point_array;
				return NULL;
				} 
			else 
				{
				x = PyInt_AsLong (px);
				y = PyInt_AsLong (py);
				point_array[i].x = x;
				point_array[i].y = y;
				}
			}
		}
	// we have an array of POINT structs, now we
	// can finally call the mfc function.
	GUI_BGN_SAVE;
	pWnd->MapWindowPoints(pWndTo,point_array, num);
	GUI_END_SAVE;

	// create a list
	// copy mapped points
	// return list of points
	PyObject *list = PyList_New(num);
	for (i=0;i<num;i++) 
		PyList_SetItem(list,i,Py_BuildValue("(ii)",point_array[i].x,point_array[i].y));

	delete[] point_array;

	return list;
	// @rdesc A list of the mapped points from the coordinate space of the CWnd to the coordinate space of another window.
	}
*/

/*
// @pymethod <o PyCWnd>|PyCWnd|GetParentOwner|Returns the most immediate parent or owner window that is not a child window .
static PyObject *
ui_window_get_parent_owner(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS(args);
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	// @pyseemfc CWnd|GetParentOwner
	if (pWnd->m_hWnd==NULL)
		RETURN_ERR("The window object does not have a Windows window attached");
	GUI_BGN_SAVE;
	CWnd *pParentOwner = pWnd->GetParentOwner();
	GUI_END_SAVE;
	if (!pParentOwner)
		RETURN_NONE;

	return PyCWnd::make( UITypeFromCObject(pParentOwner), pParentOwner )->GetGoodRet();
}
*/

/*
// @pymethod int|PyCWnd|SetTimer|Installs a system timer
static PyObject *
ui_window_set_timer(PyObject *self, PyObject *args)
	{
	UINT nIDEvent, nElapse;
	if (!PyArg_ParseTuple(args, "ii:SetTimer",&nIDEvent,&nElapse))
		return NULL;
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;

	// @pyseemfc CWnd|SetTimer
	GUI_BGN_SAVE;
	UINT id = pWnd->SetTimer(nIDEvent,nElapse,NULL);
	GUI_END_SAVE;
	return Py_BuildValue("i", id);
	}
*/

/*
// @pymethod int|PyCWnd|KillTimer|Kills a system timer
static PyObject *
ui_window_kill_timer(PyObject *self, PyObject *args)
	{
	UINT nID;
	if (!PyArg_ParseTuple(args, "i:KillTimer",&nID))
		return NULL;
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;

	// @pyseemfc CWnd|KillTimer
	GUI_BGN_SAVE;
	BOOL br = pWnd->KillTimer(nID);
	GUI_END_SAVE;
	return Py_BuildValue("i", br);
	}
*/

// kk: the general mechanism of IsKindOf must be implemented instead of this
// @pymethod |PyCWnd|IsKindOfMDIChildWnd|Returns true if the window is a kind of MDIChildWnd
PyObject *
ui_window_is_kind_of_mdi_child_wnd(PyObject *self, PyObject *args)
	{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;
	CHECK_NO_ARGS2(args,IsMDIChildWnd);
	BOOL it_is=pWnd->IsKindOf(RUNTIME_CLASS(CMDIChildWnd));
	return Py_BuildValue("i", it_is);
	}

/*
// @mfcproto void InvalidateRgn(CRgn* pRgn, BOOL bErase = TRUE );
PyObject *
ui_window_invalidate_rgn(PyObject *self, PyObject *args)
	{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;
	PyObject *objRgn;
	BOOL bErase = TRUE;
	if (!PyArg_ParseTuple(args,"O|i:InvalidateRgn",&objRgn,&bErase)) 
		return NULL;
	CRgn *pRgn = PyCRgn::GetRgn(objRgn);
	if (!pRgn) return NULL;
	GUI_BGN_SAVE;
	pWnd->InvalidateRgn(pRgn,bErase);
	GUI_END_SAVE;
	RETURN_NONE;
	}
	*/

/*
// @mfcproto int RunModalLoop(DWORD dwFlags);
PyObject *
ui_window_run_modal_loop(PyObject *self, PyObject *args)
	{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;
	DWORD dwFlags;
	if (!PyArg_ParseTuple(args,"i:RunModalLoop",&dwFlags)) 
		return NULL;
	GUI_BGN_SAVE;
	int nResult=pWnd->RunModalLoop(dwFlags);
	GUI_END_SAVE;
	return Py_BuildValue("i",nResult);
	}
*/

/*
// @mfcproto void EndModalLoop( int nResult );
PyObject *
ui_window_end_modal_loop(PyObject *self, PyObject *args)
	{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;
	int nResult;
	if (!PyArg_ParseTuple(args,"i:EndModalLoop",&nResult)) 
		return NULL;
	GUI_BGN_SAVE;
	pWnd->EndModalLoop(nResult);
	GUI_END_SAVE;
	RETURN_NONE;
	}
*/

/*
// @mfcproto void RepositionBars( UINT nIDFirst, UINT nIDLast, UINT nIDLeftOver, UINT nFlag = CWnd::reposDefault, LPRECT lpRectParam = NULL, LPCRECT lpRectClient = NULL, BOOL bStretch = TRUE );
PyObject *
ui_window_reposition_bars(PyObject *self, PyObject *args)
	{
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)return NULL;
	UINT nIDFirst,nIDLast, nIDLeftOver;
	if (!PyArg_ParseTuple(args,"iii:RepositionBars",&nIDFirst,&nIDLast,&nIDLeftOver)) 
		return NULL;
	GUI_BGN_SAVE;
	pWnd->RepositionBars(nIDFirst,nIDLast,nIDLeftOver);
	GUI_END_SAVE;
	RETURN_NONE;
	}
*/

///////////////////////////////////////////////////
typedef CPythonFrameFramework<CFrameWnd> CPyFrame;

/*
// @pymethod <o PyFrameWnd>|win32ui|CreateFrame|Creates a Frame window.
PyObject *
ui_create_frame(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS2(args,CreateFrame);
	GUI_BGN_SAVE;
	CPyFrame* pFrame = new CPyFrame;
	GUI_END_SAVE;
	return ui_assoc_object::make(PyCFrameWnd::type, pFrame)->GetGoodRet();
	// @rdesc The window object (not the OS window) created.  An exception is raised if an error occurs.
}
*/

// @pymethod tuple|PyCFrameWnd|Create|Creates the actual window for the PyCFrameWnd object.
static PyObject *
PyCFrameWnd_create(PyObject *self, PyObject *args)
	{
	CFrameWnd *pFrame=GetFramePtr(self);
	if (!pFrame)return NULL;

	PythonCreateContext cc;
	RECT rect = CFrameWnd::rectDefault;
	PyObject *obRect = Py_None;
	PyObject *obParent = Py_None;
	PyObject *obContext = Py_None;
	char *szClass=NULL, *szTitle=NULL,*szMenuName=NULL;
	DWORD styleEx=0;
	DWORD style = WS_VISIBLE | WS_OVERLAPPEDWINDOW;
	if(!PyArg_ParseTuple(args, "zs|lOOOzl:Create",
		&szClass, // @pyparm string|wndClass||The window class name, or None
		&szTitle, // @pyparm string|title||The window title
		&style, // @pyparm int|style| WS_VISIBLE \| WS_OVERLAPPEDWINDOW|The window style
		&obRect, // @pyparm int, int, int, int|rect|None|The default rectangle
		&obParent, // @pyparm parent|<o PyCWnd>|None|The parent window
		&obContext,// @pyparm tuple|createContext|None|A tuple representing a CREATECONTEXT structure.
		&szMenuName,// @pyparm string|pszMenuName||The string id for the menu.
        &styleEx)) // @pyparm int|styleEx||The extended style of the window being created.
		return NULL;

	CCreateContext* pContext = NULL;
	if (obContext != Py_None) 
		{
		cc.SetPythonObject(obContext);
		pContext = &cc;
		}
	if (obRect != Py_None) 
		{
		if (!PyArg_ParseTuple(obRect, "iiii", &rect.left,  &rect.top,  &rect.right,&rect.bottom)) 
			{
			PyErr_Clear();
			RETURN_TYPE_ERR("Rect must be None or a tuple of (iiii)");
			}
		}
	CFrameWnd *pParent = NULL;
	if (obParent != Py_None) 
		{
		pParent = GetFramePtr(obParent);
		if (pParent==NULL)
			RETURN_TYPE_ERR("The parent window is not a valid PyFrameWnd");
		}

	GUI_BGN_SAVE;
	// @pyseemfc CFrameWnd|Create
	BOOL ok = pFrame->Create(szClass, szTitle, style, rect,pParent,szMenuName,styleEx,pContext);
	GUI_END_SAVE;
	if (!ok)
		RETURN_ERR("CFrameWnd::Create failed");
	RETURN_NONE;
}

// @pymethod tuple|PyCFrameWnd|LoadFrame2|Creates the actual window for the PyCFrameWnd object and loads its resources.
static PyObject *
PyCFrameWnd_load_frame2(PyObject *self, PyObject *args)
	{
	CFrameWnd *pFrame=GetFramePtr(self);
	if (!pFrame)return NULL;

	int idResource;
	PyObject *obParent = Py_None;
	PyObject *obContext = Py_None;
	DWORD styleEx=0;
	DWORD style = WS_VISIBLE | WS_OVERLAPPEDWINDOW;
	if (!PyArg_ParseTuple(args, "i|lOO:LoadFrame", 
	                      &idResource, // @pyparm int|idResource|IDR_APPLICATION|The Id of the resources (menu, icon, etc) for this window
	                      &style,	   // @pyparm long|style|-1|The window style.  Note -1 implies win32con.WS_OVERLAPPEDWINDOW\|win32con.FWS_ADDTOTITLE
						  &obParent,  // @pyparm <o PyCWnd>|wndParent|None|The parent of the window, or None.
						  &obContext)) // @pyparm object|context|None|An object passed to the OnCreateClient for the frame,
		return NULL;

	PythonCreateContext cc;
	CCreateContext* pContext = NULL;
	if (obContext != Py_None) 
		{
		cc.SetPythonObject(obContext);
		pContext = &cc;
		}
	CFrameWnd *pParent = NULL;
	if (obParent != Py_None) 
		{
		pParent = GetFramePtr(obParent);
		if (pParent==NULL)
			RETURN_TYPE_ERR("The parent window is not a valid PyFrameWnd");
		}

	GUI_BGN_SAVE;
	BOOL ok = pFrame->LoadFrame(idResource,style,pParent,pContext); // @pyseemfc CFrameWnd|LoadFrame
	GUI_END_SAVE;
	if (!ok)
		RETURN_ERR("LoadFrame failed\n");
		// frame will be deleted in PostNcDestroy cleanup
	RETURN_NONE;
	}

/*
// @pymethod tuple|PyCFrameWnd|PreCreateWindow|Calls the underlying MFC PreCreateWindow method.
static PyObject *
PyCFrameWnd_pre_create_window(PyObject *self, PyObject *args)
{
	CPyFrame *pFrame=(CPyFrame *)GetFramePtr(self);
	if (!pFrame)return NULL;

	CREATESTRUCT cs;
	//@pyparm tuple|createStruct||A tuple representing a CREATESTRUCT structure.
	if (!CreateStructFromPyObject( &cs, args, "PreCreateWindow", TRUE))
		return NULL;

	GUI_BGN_SAVE;
	BOOL ok = pFrame->PreCreateWindowBase(cs);
	GUI_END_SAVE;
	if (!ok)RETURN_ERR("CFrameWnd::PreCreateWindow failed");
	return PyObjectFromCreateStruct(&cs);
}
*/

/*
// @pymethod <o PyCMDIFrameWnd>|PyCMDIFrameWnd|GetMDIClient|Returns the MDI client window
static PyObject *
ui_mdi_frame_get_mdi_client( PyObject *self, PyObject *args)
{
	CMDIFrameWnd *pFrame = GetMDIFrame(self);
	if (!pFrame)return NULL;
	CHECK_NO_ARGS2(args, GetMDIClient);

	if(!pFrame->m_hWndMDIClient)
		RETURN_ERR("MDIGetClient call but MDIFrameWnd has not been created");

	CWnd *pWnd = CWnd::FromHandle(pFrame->m_hWndMDIClient);
	if (pWnd==NULL)
		RETURN_ERR("The window handle is invalid.");
	return PyCWnd::make( UITypeFromCObject(pWnd), pWnd)->GetGoodRet();
}
*/
/*
// @pymethod <o PyCMDIFrameWnd>|PyCMDIFrameWnd|MDIActivate|activate an MDI child window
static PyObject *
ui_mdi_frame_mdi_activate( PyObject *self, PyObject *args)
{
	CMDIFrameWnd *pFrame = GetMDIFrame(self);
	if (!pFrame)return NULL;

	PyObject *ob;
	if (!PyArg_ParseTuple(args,"O:MDIActivate", 
		       &ob)) // @pyparm <o PyCWnd>
		return NULL;

	CWnd* pWndActivate = GetWndPtr(ob);
	if(!pWndActivate)
		RETURN_ERR("Argument is not a valid PyCWnd");

	GUI_BGN_SAVE;
	pFrame->MDIActivate(pWndActivate);
	GUI_END_SAVE;
	RETURN_NONE;
}
*/
/////////////////////// 
/*
// @mfcproto |CMDIFrameWnd* GetMDIFrame();
// @pymethod |PyCMDIChildWnd|GetMDIFrame|Returns the MDI parent frame
PyObject *
ui_mdi_child_window_get_mdi_frame(PyObject *self, PyObject *args)
	{
	CPythonFrame *pWnd = GetPythonFrame(self);
	if (!pWnd)return NULL;
	CHECK_NO_ARGS2(args,GetMDIFrame);

	GUI_BGN_SAVE;
	CMDIFrameWnd* pFrame=pWnd->GetMDIFrame();
	GUI_END_SAVE;
	
	return ui_assoc_object::make(UITypeFromCObject(pFrame), pFrame)->GetGoodRet();
	}
*/


// @pymethod <o PyCWnd>|win32ui|SubclassWindow|Creates a <o PyCWnd> from an integer containing a HWND
PyObject *
ui_window_subclass_window(PyObject *self, PyObject *args)
{
	HWND hwnd;
	if (!PyArg_ParseTuple(args, "i:SubclassWindow", &hwnd)) 
		return NULL;
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	GUI_BGN_SAVE;
	BOOL rc = pWnd->SubclassWindow(hwnd);
	GUI_END_SAVE;
	return Py_BuildValue( "i", rc);
}

// @pymethod <o PyCWnd>|win32ui|SubclassDlgItem|“dynamically subclass” a control created from a dialog template and attach it to this CWnd object
PyObject *
ui_window_subclass_dlg_item(PyObject *self, PyObject *args)
{
	UINT nID;
	PyObject *obParent;
	if (!PyArg_ParseTuple(args, "iO:SubclassDlgItem", &nID, &obParent)) 
		return NULL;

	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;

	CWnd *pParent = GetWndPtr(obParent);
	if (pParent==NULL)
		RETURN_TYPE_ERR("The parent window is not a valid PyWnd");
	
	GUI_BGN_SAVE;
	BOOL rc = pWnd->SubclassDlgItem(nID, pParent);
	GUI_END_SAVE;
	return Py_BuildValue( "i", rc);
}



// @pymethod <o PyCWnd>|win32ui|ScrollWindow|Scrolls the contents of the client area of the current CWnd object
PyObject *
ui_window_scroll_window(PyObject *self, PyObject *args)
{
	int xAmount, yAmount;
	if (!PyArg_ParseTuple(args, "ii:ScrollWindow", &xAmount, &yAmount)) 
		return NULL;
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	GUI_BGN_SAVE;
	pWnd->ScrollWindow(xAmount,yAmount,NULL,NULL);
	GUI_END_SAVE;
	RETURN_NONE;
}


// @pymethod <o PyCWnd>|win32ui|PrintClient|Draw any window in the specified device context 
PyObject *
ui_window_print_client(PyObject *self, PyObject *args)
{
	PyObject *obDC = NULL;
	DWORD dwFlags = PRF_CLIENT;
	if (!PyArg_ParseTuple(args, "|Oi:PrintClient", &obDC, &dwFlags)) 
		return NULL;
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd)
		return NULL;
	CDC *pDC=NULL;
	if (obDC && !(pDC=ui_dc_object::GetDC(obDC)))
		return NULL;
	GUI_BGN_SAVE;
	pWnd->PrintClient(pDC, dwFlags);
	GUI_END_SAVE;
	RETURN_NONE;
}

static PyObject *
ui_window_register_drop_target(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS(args);
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd) return NULL;

	// register drop target
	//pWnd->m_dropTarget.Register(pWnd);
	
	RETURN_NONE;
}
static PyObject *
ui_window_revoke_drop_target(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS(args);
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd) return NULL;

	// register drop target
	//pWnd->m_dropTarget.Revoke();
	
	RETURN_NONE;
}

static PyObject *
ui_window_do_drag_drop(PyObject *self, PyObject *args)
{
	int cf; // clipboard format 
	char *pszData;
	if (!PyArg_ParseTuple(args,"is:DoDragDrop",&cf,&pszData))
		return NULL;
	
	CWnd *pWnd = GetWndPtr(self);
	if (!pWnd) return NULL;

	CLIPFORMAT cfPrivate=(CLIPFORMAT)cf;
	DROPEFFECT dropEffect = DROPEFFECT_NONE;
	HGLOBAL hGlobal=GlobalAlloc(GMEM_MOVEABLE | GMEM_SHARE,lstrlen(pszData)+1);
	LPSTR lpGMem=(LPSTR)GlobalLock(hGlobal);
	lstrcpy(lpGMem,pszData);
	GlobalUnlock(hGlobal);

	COleDataSource oleDataSource;
	COleDataSource::FlushClipboard();
	oleDataSource.CacheGlobalData(cfPrivate,hGlobal);
	GUI_BGN_SAVE;
	dropEffect=oleDataSource.DoDragDrop();
	GUI_END_SAVE;
	GlobalFree(hGlobal);
	return Py_BuildValue("i", dropEffect);
}

// SubclassDlgItem

///////////////////////
// @pymeth GetWindowLong|Gets the style of a window.
// @pymeth SetWindowLong|Modifies the style of a window.
// @pymeth ScreenToClient|Converts from screen coordinates to client coordinates.
// @pymeth LockWindowUpdate|Disables drawing in the given window
// @pymeth UnLockWindowUpdate|Unlocks a window that was locked with LockWindowUpdate
// @pymeth MapWindowPoints|Converts (maps) a set of points from the coordinate space of the CWnd to the coordinate space of another window.
// @pymeth GetParentOwner|Returns the most immediate parent or owner window that is not a child window .
// @pymeth IsWindow|determines whether the specified window handle identifies an existing window.	
// @pymeth SetTimer|Installs a system timer
// @pymeth KillTimer|Destroys a system timer
// ...
// @pymethod (x, y)|PyCWnd|ChildWindowFromPoint|Returns the child window that contains the point and if not found the window asked for
// @pymethod <o PyCWnd>|win32ui|SubclassDlgItem|“dynamically subclass” a control created from a dialog template and attach it to this CWnd object

#define DEF_NEW_PY_METHODS_PyCWnd \
	{"IsKindOfMDIChildWnd",ui_window_is_kind_of_mdi_child_wnd,1},\
    {"GetWindowLong",ui_window_get_window_long,1},\
	{"SetWindowLong",ui_window_set_window_long,1},\
	{"ChildWindowFromPoint",ui_window_child_window_from_point,1},\
	{"SubclassWindow",ui_window_subclass_window,1},\
	{"ScrollWindow",ui_window_scroll_window,1},\
	{"PrintClient",ui_window_print_client,1},\
	{"ValidateRect",ui_window_validate_rect,1},\
	{"RegisterDropTarget",ui_window_register_drop_target,1},\
	{"RevokeDropTarget",ui_window_revoke_drop_target,1},\
	{"DoDragDrop",ui_window_do_drag_drop,1},\
	{"SubclassDlgItem",ui_window_subclass_dlg_item,1}, 


/*
#define DEF_NEW_PY_METHODS_PyCWnd \
	{"GetWindowLong",ui_window_get_window_long,1},\
	{"SetWindowLong",ui_window_set_window_long,1},\
	{"ScreenToClientRect",ui_window_screen_to_client_rect,1},\
	{"ClientToScreenRect",ui_window_client_to_screen_rect,1},\
	{"LockWindowUpdate",ui_lock_window_update,1},\
	{"UnlockWindowUpdate",ui_unlock_window_update,1},\
	{"MapWindowPoints",ui_window_map_window_points,1},\
	{"InvalidateRgn",ui_window_invalidate_rgn,1},\
	{"GetWindowDC",ui_window_get_window_dc,1},\
	{"GetDCEx",ui_window_get_dc_ex,1},\
	{"GetParentOwner",ui_window_get_parent_owner,1},\
	{"IsWindow",ui_window_is_window,1},\
	{"SetTimer",ui_window_set_timer,1},\
	{"KillTimer",ui_window_kill_timer,1},\
	{"RunModalLoop",ui_window_run_modal_loop,1},\
	{"EndModalLoop",ui_window_end_modal_loop,1},\
	{"RepositionBars",ui_window_reposition_bars,1},\
	{"IsKindOfMDIChildWnd",ui_window_is_kind_of_mdi_child_wnd,1},
*/


#define DEF_NEW_PY_METHODS_PyCFrameWnd\
	{"Create",PyCFrameWnd_create,1},\
	{"PreCreateWindow",PyCFrameWnd_pre_create_window,1},\
	{"LoadFrame2",PyCFrameWnd_load_frame2,1},



//#define DEF_NEW_PY_METHODS_PyCMDIFrameWnd\
//	{"GetMDIClient",ui_mdi_frame_get_mdi_client,1},\
//	{"MDIActivate",ui_mdi_frame_mdi_activate,1},

//#define DEF_NEW_PY_METHODS_PyCMDIChildWnd\
//	{"GetMDIFrame",ui_mdi_child_window_get_mdi_frame,1},


// @pymethod <o PyMiniFrameWnd>|win32ui|CreateMiniFrame|Creates a MiniFrame window.
PyObject *
ui_create_miniframe(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS2(args,CreateFrame);
	GUI_BGN_SAVE;
	CMiniFrameWnd* pFrame = new CMiniFrameWnd;
	GUI_END_SAVE;
	return ui_assoc_object::make(PyCFrameWnd::type, pFrame)->GetGoodRet();
	// @rdesc The window object (not the OS window) created.  An exception is raised if an error occurs.
}


// @pymethod tuple|PyCMiniFrameWnd|CreateWindow|Creates the actual window for the PyCWnd object.
PyObject *
ui_mini_frame_window_create_window(PyObject *self, PyObject *args)
{
	CPythonMiniFrameWnd *pWnd = 
		(CPythonMiniFrameWnd *)PyCWnd::GetPythonGenericWnd(self, &PyCFrameWnd::type);

	if (!pWnd)
		return NULL;
	PythonCreateContext cc;
	RECT rect = CMDIChildWnd::rectDefault;
	PyObject *obRect = Py_None;
	PyObject *obParent = Py_None;
	UINT id=0;
	char *szClass, *szTitle;
	DWORD style = WS_CHILD | WS_VISIBLE | WS_OVERLAPPEDWINDOW;
	if (!PyArg_ParseTuple(args, "zs|lOOO:CreateWindow",
		&szClass, // @pyparm string|wndClass||The window class name, or None
		&szTitle, // @pyparm string|title||The window title
		&style, // @pyparm int|style|WS_CHILD \| WS_VISIBLE \| WS_OVERLAPPEDWINDOW|The window style
		&obRect, // @pyparm int, int, int, int|rect|None|The default rectangle
		&obParent, // @pyparm parent|<o PyCWnd>|None|The parent window
		&id))// 
		return NULL;

	if (obRect != Py_None) {
		if (!PyArg_ParseTuple(obRect, "iiii", &rect.left,  &rect.top,  &rect.right,  &rect.bottom)) {
			PyErr_Clear();
			RETURN_TYPE_ERR("Rect must be None or a tuple of (iiii)");
		}
	}
	CMDIFrameWnd *pParent = NULL;
	if (obParent != Py_None) {
		pParent = GetMDIFrame( obParent );
		if (pParent==NULL)
			RETURN_TYPE_ERR("The parent window is not a valid PyMiniFrameWnd");
	}

	GUI_BGN_SAVE;
	BOOL ok = pWnd->Create(szClass, szTitle, style, rect, pParent, id);
	GUI_END_SAVE;
	if (!ok)
		RETURN_ERR("CMiniFrameWnd::Create");
	RETURN_NONE;
}


// @object PyCMiniFrameWnd|A windows mini frame window.  Encapsulates an MFC <c CMiniFrameWnd> class
static struct PyMethodDef PyCMiniFrameWnd_methods[] = {
	{"CreateWindow", ui_mini_frame_window_create_window, 1}, // @pymeth CreateWindow|Creates the actual window for the PyCWnd object.
	{NULL,			NULL}
};

ui_type_CObject PyCMiniFrameWnd::type("PyCMiniFrameWnd", 
									 &PyCFrameWnd::type, 
									 RUNTIME_CLASS(CMiniFrameWnd), 
									 sizeof(PyCMiniFrameWnd), 
									 PyCMiniFrameWnd_methods, 
									 GET_PY_CTOR(PyCMiniFrameWnd));

