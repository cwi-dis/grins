// CMIF_ADD
//
// kk@epsilon.com.gr
//
//
// Note that this source file contains embedded documentation.
// This documentation consists of marked up text inside the
// C comments, and is prefixed with an '@' symbol.  The source
// files are processed by a tool called "autoduck" which
// generates Windows .hlp files.
// @doc

// Purpose: This module exports to Python the global MFC functions.
// These functions according to an MFC convention start
// with the prefix Afx. For example AfxGetMainWnd is a global
// MFC function returning the application's main window.
// You access this module with the call:
// Afx=win32ui.GetAfx()
// the returned object is this module. To call the afformentioned
// function AfxGetMainWnd from this module you call:
// wnd=Afx.GetMainWnd()

#include "stdafx.h"
#include "win32ui.h"
#include "win32win.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(Afx);
IMPLEMENT_PYMODULECLASS(Afx,GetAfx,"Afx Module Wrapper Object");


// @pymethod <o PyAfx>|GetMainWnd|Returns the application's main window (for not OLE server applications)
// Return Values: PyCWnd or an object defived from PyCWnd
PyObject *
afx_get_mainwnd(PyObject *self, PyObject *args)
{
	CHECK_NO_ARGS2(args, GetAfx);
	GUI_BGN_SAVE;
	CWnd *pWnd = AfxGetMainWnd();
	GUI_END_SAVE;
	if (pWnd==NULL)
		RETURN_ERR("No main window.");
	return PyCWnd::make( UITypeFromCObject(pWnd), pWnd)->GetGoodRet();
}

// @pymethod <o PyAfx>|GetApp|Retrieves the application object.
// Return Values: the application objext as a PyCWinApp object
PyObject *
afx_get_app(PyObject *self, PyObject *args)
{
	// @comm There will only ever be one application object per application.
	CHECK_NO_ARGS2(args,GetApp);
	CWinApp *pApp = GetApp();
	if (pApp==NULL) return NULL;
	return ui_assoc_object::make(PyCWinApp::type, pApp)->GetGoodRet();
}

// @pymethod string|win32ui|RegisterWndClass|Registers a window class
// Return Values: A null-terminated string containing the registered class name.
static PyObject *
afx_register_wnd_class(PyObject *self, PyObject *args)
{
	long style;
	long hCursor = 0, hBrush = 0, hIcon = 0;
	if (!PyArg_ParseTuple(args,"l|lll:RegisterWndClass",
		&style, // @pyparm int|style||Specifies the Windows class style or combination of styles
		&hCursor, // @pyparm int|hCursor|0|
		&hBrush, // @pyparm int|hBrush|0|
		&hIcon)) // @pyparm int|hIcon|0|
		return NULL;

	GUI_BGN_SAVE;
	LPCTSTR ret = AfxRegisterWndClass( style, (HCURSOR)hCursor, (HBRUSH)hBrush, (HICON)hIcon); 
	GUI_END_SAVE;
	return PyString_FromString(ret);
	// @comm The Microsoft Foundation Class Library automatically registers several standard window classes for you. Call this function if you want to register your own window classes.
}

// Initializes the OLE DLLs.
// Return Values:: None
static PyObject *
afx_ole_init(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,OleInit);
	GUI_BGN_SAVE;
	AfxOleInit();
	GUI_END_SAVE;
	RETURN_NONE;
	}

// A call to this function enables support for containment of OLE controls
// Return Values: None
static PyObject *
afx_enable_control_container(PyObject *self, PyObject *args)
	{
	CHECK_NO_ARGS2(args,EnableControlContainer);
	GUI_BGN_SAVE;
	AfxEnableControlContainer();
	GUI_END_SAVE;
	RETURN_NONE;
	}

// This function posts a WM_QUIT message to the thread's message queue and returns immediately
// like the PostQuitMessage but it also unloads com/ole lib
// Return Values: None
static PyObject *
afx_post_quit_message(PyObject *self, PyObject *args)
	{
	int nExitCode;
	if (!PyArg_ParseTuple(args, "i:PostQuitMessage",&nExitCode))
		return NULL;
	AfxPostQuitMessage(nExitCode);
	RETURN_NONE;
	}



// @object PyAfx|A module wrapper object.  It is a general utility object, and is not associated with an MFC object.
BEGIN_PYMETHODDEF(Afx)
	{"GetMainWnd",              afx_get_mainwnd, 1 },    // @pymeth GetMainWnd|Retrieves the application main window.
	{"GetApp",                  afx_get_app, 1 },    // @pymeth GetApp|Retrieves the application object.
	{"RegisterWndClass",        afx_register_wnd_class, 1},    // @pymeth RegisterWndClass|Registers a window class.
	{"OleInit",afx_ole_init, 1},    
	{"EnableControlContainer",afx_enable_control_container,1},
	{"PostQuitMessage",afx_post_quit_message,1},
END_PYMETHODDEF()

DEFINE_PYMODULETYPE("PyAfx",Afx);

