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


static PyObject *timerexError;
static char cmifClass[100]="";
static char dbgmess[100]="";

static PyObject *testOb = Py_None;
static PyCWnd *testWnd=NULL;
static CWnd *newWnd, *mainWnd;
static UINT timerID = 100;

static PyObject* py_timerex_CreateWindow(PyObject *self, PyObject *args)
{
	if(testOb!=Py_None)
		return Py_BuildValue("O", testOb);
	
	newWnd = new CWnd;

	if(!PyArg_ParseTuple(args, ""))
		return Py_BuildValue("i", 0);

	mainWnd = AfxGetMainWnd();
	
	if(cmifClass[0]==0)
		strcpy(cmifClass, AfxRegisterWndClass( CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS, LoadCursor (NULL, IDC_ARROW), (HBRUSH) GetStockObject (WHITE_BRUSH), NULL));
		
	if(newWnd->CreateEx(WS_EX_CLIENTEDGE,
						cmifClass, "Timer",
						WS_OVERLAPPEDWINDOW,
						0, 0, 0, 0,
						mainWnd->m_hWnd,
						NULL))
		TRACE("timerex CreateWindow OK!\n");
	else
	{
		TRACE("timerex CreateWindow FALSE!\n");
		return Py_BuildValue("O", testOb);
	}
	
	testWnd = testWnd->make(testWnd->type, (CWnd*)(newWnd));
	testOb = testWnd->GetGoodRet();

	return Py_BuildValue("O", testOb);
}


static PyObject* py_timerex_SetTimer(PyObject *self, PyObject *args)
{
	UINT elapse, id;
	
	if(!PyArg_ParseTuple(args, "i", &elapse))
		return Py_BuildValue("i", -1);

	if(newWnd==NULL)
		return Py_BuildValue("i", -1);

	id = newWnd->SetTimer(timerID, elapse, NULL);
	if(++timerID>20000)
		timerID = 100;

	return Py_BuildValue("i", id);
}

static PyObject* py_timerex_KillTimer(PyObject *self, PyObject *args)
{
	BOOL res;
	UINT id;

	if(!PyArg_ParseTuple(args, "i", &id))
		return Py_BuildValue("i", -1);

	if(newWnd==NULL)
		return Py_BuildValue("i", -1);

	res = newWnd->KillTimer(id);

	return Py_BuildValue("i", (int)res);
}


BEGIN_PYMETHODDEF(Timerex)
	{"CreateTimerWindow", py_timerex_CreateWindow, 1},
	{"SetTimer", py_timerex_SetTimer, 1},
	{"KillTimer", py_timerex_KillTimer, 1},
END_PYMETHODDEF();

DEFINE_PYMODULETYPE("PyMTimerex",Timerex);