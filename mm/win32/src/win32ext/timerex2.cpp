// -*- Mode: C++; tab-width: 4 -*-
// $Id$
//
#include "stdafx.h"

#include "win32ui.h"
#include "win32assoc.h"
#include "win32win.h"

#include "moddef.h"
DECLARE_PYMODULECLASS(Timerex2);
IMPLEMENT_PYMODULECLASS(Timerex2,GetTimerex2,"Timerex2 Module Wrapper Object");

///////////////////////////////////

static CWnd *mainWnd;  
static UINT timerID = 100;

static PyObject* py_timerex2_SetTimer(PyObject *self, PyObject *args)
{
	UINT elapse, id;
	CWnd *newWnd;	
	PyObject *ob = Py_None;
	
	if(!PyArg_ParseTuple(args, "Oi", &ob , &elapse))
		return Py_BuildValue("Oi",Py_None, -1);
	
	newWnd = GetWndPtr(ob);

	if(newWnd==NULL)
		return Py_BuildValue("i", -1);

	id = newWnd->SetTimer(timerID, elapse, NULL);
	if(++timerID>20000)
		timerID = 100;
	
	return Py_BuildValue("i", id);
}

static PyObject* py_timerex2_KillTimer(PyObject *self, PyObject *args)
{
	BOOL res;
	UINT id;
	CWnd *newWnd;
	PyObject *ob = Py_None;

	if(!PyArg_ParseTuple(args, "Oi", &ob, &id))
		return Py_BuildValue("Oi" ,Py_None, -1);

    newWnd = GetWndPtr(ob);

	if(newWnd==NULL)
		return Py_BuildValue("i", -1);

	res = newWnd->KillTimer(id);

	return Py_BuildValue("i", (int)res);
}



/////////////////////////////
BEGIN_PYMETHODDEF(Timerex2)
	{ "SetTimer", py_timerex2_SetTimer, 1},
	{ "KillTimer", py_timerex2_KillTimer, 1},
END_PYMETHODDEF();

DEFINE_PYMODULETYPE("PyMTimerex2",Timerex2);

