// -*- Mode: C++; tab-width: 4 -*-
// $Id$
//
#include "stdafx.h"

#include "win32ui.h"
#include "win32assoc.h"
#include "win32win.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(Timerex);
IMPLEMENT_PYMODULECLASS(Timerex,GetTimerex,"Timerex Module Wrapper Object");

///////////////////////////////////

static CWnd *mainWnd;  
static UINT timerID = 100;
static char cmifClass[100]="";

static PyObject* py_create_timer_window(PyObject *self, PyObject *args)
{

	CHECK_NO_ARGS(args);

	GUI_BGN_SAVE;
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), NULL));
	CWnd *pWnd = new CWnd;
	if(pWnd->CreateEx(WS_EX_CLIENTEDGE,
						cmifClass, "Timer",
						WS_OVERLAPPEDWINDOW,
						0, 0, 0, 0,
						AfxGetMainWnd()->m_hWnd,
						NULL))
		TRACE("timerex CreateWindow OK!\n");
	GUI_END_SAVE;
	
	PyCWnd *pPyWnd = PyCWnd::make(PyCWnd::type,pWnd);
	PyObject *pPyObj = pPyWnd->GetGoodRet();
	return Py_BuildValue("O",pPyObj);
}

static PyObject* py_set_timer(PyObject *self, PyObject *args)
{
	UINT elapse;
	PyObject *pPyObj;	
	if(!PyArg_ParseTuple(args, "Oi", &pPyObj ,&elapse))
		return NULL;
	
	CWnd *pWnd = GetWndPtr(pPyObj);

	if(pWnd==NULL)
		return NULL;

	timerID=timerID>100000?100:timerID;

	GUI_BGN_SAVE;
	UINT id = pWnd->SetTimer(timerID++, elapse, NULL);
	GUI_END_SAVE;
	
	return Py_BuildValue("i", id);
}

static PyObject* py_kill_timer(PyObject *self, PyObject *args)
	{
	UINT id;
	PyObject *pPyObj;
	if(!PyArg_ParseTuple(args, "Oi", &pPyObj, &id))
		return NULL;

    CWnd *pWnd = GetWndPtr(pPyObj);

	if(pWnd==NULL)
		return NULL;

	GUI_BGN_SAVE;
	BOOL res = pWnd->KillTimer(id);
	GUI_END_SAVE;

	return Py_BuildValue("i", (int)res);
	}

/////////////////////////////
BEGIN_PYMETHODDEF(Timerex)
	{ "CreateTimerWindow", py_create_timer_window, 1},
	{ "SetTimer", py_set_timer, 1},
	{ "KillTimer", py_kill_timer, 1},
END_PYMETHODDEF();

DEFINE_PYMODULETYPE("PyMTimerex",Timerex);

